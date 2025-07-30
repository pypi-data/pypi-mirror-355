"""
This module contains related class for monitoring the PAL MLTrack.

The following class is available:

    * :class:`ExperimentMonitor`
"""
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=simplifiable-if-expression
# pylint: disable=simplifiable-if-statement
# pylint: disable=unused-argument
# pylint: disable=too-many-instance-attributes
# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
# pylint: disable=too-many-positional-arguments
import os
import threading
import time
from urllib.parse import quote
from typing import List
from enum import Enum
from queue import Queue
import pandas as pd
from prettytable import PrettyTable
from hdbcli import dbapi
from hana_ml.dataframe import ConnectionContext
from hana_ml.visualizers.shared import EmbeddedUI


TRUE_FLAG = '__js_true'
FALSE_FLAG = '__js_false'
BINDED_PROPERTY = 'TRACKING_IFRAME_P_S'
EXPERIMENT_SPLITTER = "_<EXPERIMENT_SPLITTER>_"


class TaskSchedulerConfig(object):
    def __init__(self):
        self.connection_context = None
        self.task_execution_interval = None
        self.runtime_platform = EmbeddedUI.get_runtime_platform()[1]
        self.debug = False if self.runtime_platform != 'databricks' else True

        self.task_scheduler: TaskScheduler = None

    def enable_debug(self):
        self.debug = True

    def set_task_execution_interval(self, task_execution_interval):
        self.task_execution_interval = task_execution_interval

    def set_connection_context(self, connection_context: ConnectionContext):
        if connection_context:
            self.connection_context = connection_context

    def start_task_scheduler(self):
        self.task_scheduler = TaskScheduler(self)
        self.task_scheduler.start()


class TaskStatus(Enum):
    Cancelled = -1    # raise exception or fronted send cancel cmd
    Running = 0
    Completed = 1     # execute complete, not included: fetch data and read data


class TaskScheduler(threading.Thread):
    def __init__(self, config: TaskSchedulerConfig):
        threading.Thread.__init__(self)
        self.config = config
        self.status = TaskStatus.Running

        self.fetch_log_task = FetchLogTask(self)
        self.output_log_task = None
        if self.config.debug:
            self.output_log_task = OutputLogToLocalFileTask(self)
        else:
            if self.config.runtime_platform == 'console':
                self.output_log_task = OutputLogToConsoleTask(self)
            else:
                self.output_log_task = OutputLogToUITask(self)

        self.interrupt_file_path = EmbeddedUI.get_resource_temp_file_path(self.output_log_task.task_id)

    def run(self):
        self.fetch_log_task.start()
        self.output_log_task.start()

        while True:
            if os.path.exists(self.interrupt_file_path):
                self.status = TaskStatus.Cancelled
                os.remove(self.interrupt_file_path)

            if self.status == TaskStatus.Cancelled:
                # if self.config.runtime_platform in ['vscode', 'bas']:
                #     print('tracking.cancel: {}'.format(self.output_log_task.task_id))
                break
        print("The experiment monitor has been cancelled!")


class ExecutionLog(object):
    def __init__(self, execution_id):
        self.execution_id = execution_id
        self.state = 'UNKNOWN'  # ACTIVE, FINISHED, FAILED

        self.seq_2_key = {}
        self.seq_2_msgs = {}
        self.seq_2_status = {}

        self.can_read_max_seq = -1
        self.already_read_seq = -1

        self.fetch_offset = 0
        self.fetch_completed = False

    def add_msg(self, seq, key, msg, timestamp, state):
        self.can_read_max_seq = seq - 1  # when current is 2, max current of can read is 1.
        if self.seq_2_msgs.get(seq) is None:
            self.seq_2_key[seq] = key
            self.seq_2_status[seq] = {'id': self.execution_id, 't': str(timestamp), 'k': key}
            self.seq_2_msgs[seq] = []
        if msg is not None and msg.strip() != '':
            self.seq_2_msgs[seq].append(msg)
        if self.state == 'UNKNOWN' or key == 'END_OF_TRACK':
            self.seq_2_status[seq]['state'] = state
            self.state = state
        if key == 'END_OF_TRACK':
            self.can_read_max_seq = self.can_read_max_seq + 1
            self.fetch_completed = True

    def read_next_status(self):
        next_msg_dict = None
        next_seq = self.already_read_seq + 1

        if self.can_read_max_seq >= 0 and next_seq <= self.can_read_max_seq:
            next_msg_list = self.seq_2_msgs.get(next_seq)
            if next_msg_list is not None:
                next_msg_str = ''.join(next_msg_list).strip()
                next_msg_str = next_msg_str if next_msg_str != '' else 'None'
                next_msg_dict = self.seq_2_status.get(next_seq)
                next_msg_dict['v'] = next_msg_str
                self.already_read_seq = next_seq
        return next_msg_dict


class FetchLogTask(threading.Thread):
    def __init__(self, task_scheduler: TaskScheduler):
        threading.Thread.__init__(self)
        self.task_scheduler = task_scheduler

        connection_context: ConnectionContext = task_scheduler.config.connection_context
        self.connection_cursor: dbapi.Cursor = connection_context.connection.cursor()
        self.connection_cursor.setfetchsize(32000)

        self.TRACK_SCHEMA = "PAL_ML_TRACK"
        self.TRACK_TABLE = "TRACK_LOG"
        self.TRACK_METADATA_TABLE = "TRACK_METADATA"

        self.id_2_log = {}  # execution_id -> execution_log
        self.last_ids = []  # execution_id, ...

        self.msg_queue = Queue()

    def fetch_data(self):
        current_execution_ids = []
        current_execution_id_2_status = {}

        # 1. fetch execution_ids from track_metadata_table
        fetched_columns = ["TRACK_ID", "STATUS"]
        fetched_sql = "SELECT {} from {}.{}".format(', '.join(fetched_columns), self.TRACK_SCHEMA, self.TRACK_METADATA_TABLE)
        self.connection_cursor.execute(fetched_sql)
        fetched_data = self.connection_cursor.fetchall()
        fetched_count = len(fetched_data)
        if fetched_count > 0:
            fetched_pd_df = pd.DataFrame(fetched_data, columns=fetched_columns)
            execution_id_list = list(fetched_pd_df[fetched_columns[0]])
            status_list = list(fetched_pd_df[fetched_columns[1]])
            for i in range(0, fetched_pd_df.shape[0]):
                execution_id = execution_id_list[i]
                if execution_id.find(EXPERIMENT_SPLITTER) > 0:
                    current_execution_ids.append(execution_id)
                    current_execution_id_2_status[execution_id] = status_list[i]

        # 2. delete execution_ids
        deleted_execution_ids = list(set(self.last_ids) - set(current_execution_ids))
        self.last_ids = current_execution_ids
        for deleted_execution_id in deleted_execution_ids:
            del self.id_2_log[deleted_execution_id]
            self.msg_queue.put({'id': deleted_execution_id, 'state': 'deleted'})

        # 3. fetch logs from_track_table
        fetched_columns = ["SEQ", "EVENT_KEY", "EVENT_TIMESTAMP", "EVENT_MESSAGE"]
        for execution_id in current_execution_ids:
            execution_log: ExecutionLog = self.id_2_log.get(execution_id)
            current_state = current_execution_id_2_status[execution_id]
            if execution_log is None:
                execution_log = ExecutionLog(execution_id)
                self.id_2_log[execution_id] = execution_log
            if execution_log.fetch_completed:
                if current_state != execution_log.state:
                    execution_log.state = current_state
                    self.msg_queue.put({'id': execution_id, 'state': current_state})
            else:
                fetch_sql = "SELECT {} from {}.{} WHERE EXECUTION_ID='{}' limit 1000 offset {}".format(', '.join(fetched_columns),
                                                                                                       self.TRACK_SCHEMA,
                                                                                                       self.TRACK_TABLE,
                                                                                                       execution_id,
                                                                                                       execution_log.fetch_offset)
                self.connection_cursor.execute(fetch_sql)
                fetched_data = self.connection_cursor.fetchall()
                fetched_count = len(fetched_data)
                if fetched_count > 0:
                    execution_log.fetch_offset = execution_log.fetch_offset + fetched_count
                    fetched_pd_df = pd.DataFrame(fetched_data, columns=fetched_columns)
                    seq_list = list(fetched_pd_df[fetched_columns[0]])
                    key_list = list(fetched_pd_df[fetched_columns[1]])
                    time_list = list(fetched_pd_df[fetched_columns[2]])
                    msg_list = list(fetched_pd_df[fetched_columns[3]])
                    for i in range(0, fetched_pd_df.shape[0]):
                        execution_log.add_msg(seq_list[i], key_list[i], msg_list[i], time_list[i], current_state)
                    while True:
                        next_msg = execution_log.read_next_status()  # next_msg: None | 'xxx'
                        if next_msg is not None:
                            self.msg_queue.put(next_msg)
                        else:
                            break

    def run(self):
        while True:
            if self.task_scheduler.status == TaskStatus.Cancelled:
                break
            self.fetch_data()
            time.sleep(self.task_scheduler.config.task_execution_interval)
        self.task_scheduler.config.connection_context.close()


class AbstractOutputLogTask(threading.Thread):
    def __init__(self, task_scheduler: TaskScheduler):
        threading.Thread.__init__(self)
        self.task_scheduler = task_scheduler
        self.task_id = EmbeddedUI.get_uuid()

    def output_msgs(self, msgs):
        pass

    def init(self):
        pass

    def on_task_did_complete(self):
        pass

    def run(self):
        self.init()
        time.sleep(2)

        msg_queue = self.task_scheduler.fetch_log_task.msg_queue
        while True:
            if self.task_scheduler.status == TaskStatus.Cancelled:
                self.output_msgs([{'cancelled': TRUE_FLAG}])
                break

            size = 0
            msgs = []
            queue_size = self.task_scheduler.fetch_log_task.msg_queue.qsize()
            while size < min(queue_size, 1000):  # 1000: Maximum number of UI status updates per time
                msgs.append(msg_queue.get())
                size = size + 1
            if len(msgs) > 0:
                self.output_msgs(msgs)
            time.sleep(self.task_scheduler.config.task_execution_interval)
        self.on_task_did_complete()

    @staticmethod
    def convert_msgs_to_str(msgs: List[dict]):
        return str(msgs).replace("'{}'".format(TRUE_FLAG), 'true').replace("'{}'".format(FALSE_FLAG), 'false')

    def get_html_str(self, initial_msgs_str='[]', comm_server_url=''):
        html_str = EmbeddedUI.get_resource_template('experiment_monitor.html').render(iframe_id=self.task_id,
                                                                                      msgs_str=initial_msgs_str,
                                                                                      runtime_platform=self.task_scheduler.config.runtime_platform,
                                                                                      will_be_binded_property=BINDED_PROPERTY,
                                                                                      experiment_splitter=EXPERIMENT_SPLITTER,
                                                                                      comm_server=quote(comm_server_url, safe=':/?=&'))
        return html_str


class OutputLogToUITask(AbstractOutputLogTask):
    def __init__(self, task_scheduler: TaskScheduler):
        AbstractOutputLogTask.__init__(self, task_scheduler)

    # @override
    def init(self):
        EmbeddedUI.render_html_str(EmbeddedUI.get_iframe_str(self.get_html_str(), self.task_id, 600))

        if self.task_scheduler.config.runtime_platform == 'bas':
            EmbeddedUI.execute_js_str("")
        else:
            EmbeddedUI.execute_js_str("", self_display_id=self.task_id)

        # if self.task_scheduler.config.runtime_platform in ['vscode', 'bas']:
        #     print('tracking.start: {}: {}'.format(EmbeddedUI.get_resource_temp_dir_path() + os.sep, self.task_id))
        #     print('In order to cancel execution on the BAS or VSCode platform, you must import the VSCode extension package manually.')
        #     print('VSCode extension package path: \n{}'.format(EmbeddedUI.get_resource_temp_file_path('hanamlapi-monitor-1.2.0.vsix')))

    # @override
    def output_msgs(self, msgs):
        msgs_str = self.convert_msgs_to_str(msgs)
        js_str = "targetWindow['{}']={}".format(BINDED_PROPERTY, msgs_str)
        js_str = "for (let i = 0; i < window.length; i++) {const targetWindow = window[i];if(targetWindow['iframeId']){if(targetWindow['iframeId'] === '" + self.task_id + "'){" + js_str + "}}}"

        if self.task_scheduler.config.runtime_platform == 'bas':
            EmbeddedUI.execute_js_str("{};".format(js_str))
        elif self.task_scheduler.config.runtime_platform == 'jupyter':
            EmbeddedUI.execute_js_str_for_update("{};".format(js_str), updated_display_id=self.task_id)
        elif self.task_scheduler.config.runtime_platform == 'vscode':
            vscode_script = "const scripts = document.getElementsByTagName('script');for (let i = 0; i < scripts.length; i++) {const hanamlPipelinePNode = scripts[i].parentNode;if(hanamlPipelinePNode.tagName == 'DIV' && scripts[i].innerText.indexOf('hanamlPipelinePNode') >= 0){hanamlPipelinePNode.remove();}}"
            EmbeddedUI.execute_js_str_for_update("{};{};".format(js_str, vscode_script), updated_display_id=self.task_id)


class OutputLogToLocalFileTask(AbstractOutputLogTask):
    def __init__(self, task_scheduler: TaskScheduler):
        AbstractOutputLogTask.__init__(self, task_scheduler)
        self.progress_file = open(EmbeddedUI.get_resource_temp_file_path(self.task_id + "_experiment_monitor.txt"), 'a', encoding="utf-8")

    # @override
    def init(self):
        if self.task_scheduler.config.runtime_platform == 'databricks':
            from hana_ml.visualizers.server import CommServerManager
            comm_server_task_scheduler = CommServerManager()
            comm_server_task_scheduler.start()
            comm_server_url = comm_server_task_scheduler.get_comm_server_url()

            html_str = self.get_html_str(comm_server_url=comm_server_url)
            EmbeddedUI.generate_file(EmbeddedUI.get_resource_temp_file_path("{}.html".format(self.task_id)), html_str)
            print('Page URL: {}/page?id={}&type=ExperimentMonitorUI'.format(comm_server_url, self.task_id))

    # @override
    def output_msgs(self, msgs):
        msgs_str = self.convert_msgs_to_str(msgs)
        self.progress_file.write(msgs_str + '\n')

    # @override
    def on_task_did_complete(self):
        self.progress_file.close()


class OutputLogToConsoleTask(AbstractOutputLogTask):
    def __init__(self, task_scheduler: TaskScheduler):
        AbstractOutputLogTask.__init__(self, task_scheduler)
        self.log_table = PrettyTable()
        self.log_table.field_names = [
            "EXPERIMENTID",
            "RUNID",
            "Key",
            "Value"
        ]

    # @override
    def init(self):
        pass

    # @override
    def output_msgs(self, msgs):
        for msg in msgs:
            execution_id = msg.get('id')
            experiment_id = None
            run_id = None
            if execution_id:
                experiment_id, run_id = execution_id.split(EXPERIMENT_SPLITTER)
            timestamp = msg.get('t')
            key = msg.get('k')
            value = msg.get('v')
            state = msg.get('state')
            cancelled = msg.get('cancelled')

            self.log_table.clear_rows()
            if state == 'finished':
                self.log_table.add_row([experiment_id, run_id, "*", state])
            elif cancelled == TRUE_FLAG:
                self.log_table.add_row(["*", "*", "Experiment Monitor", "Cancelled"])
                self.task_scheduler.fetch_log_task.all_msgs.append({'cancelled': TRUE_FLAG})
                msgs_str = self.convert_msgs_to_str(self.task_scheduler.fetch_log_task.all_msgs)
                html_str = self.get_html_str(initial_msgs_str=msgs_str)
                html_path = EmbeddedUI.get_resource_temp_file_path(self.task_id) + '.html'
                EmbeddedUI.generate_file(html_path, html_str)
                print("Generated file for experimnet monitor: ", html_path)
            else:
                self.log_table.add_row([experiment_id, run_id, key, value])
            print(self.log_table)


class ExperimentMonitor(object):
    """
    The instance of this class can monitor the PAL MLTrack.

    Parameters
    ----------
    connection_context : :class:`~hana_ml.dataframe.ConnectionContext`
        The connection to the SAP HANA system.

    Examples
    --------
    Establish a ExperimentMonitor object and then invoke start():

    >>> experiment_monitor = ExperimentMonitor(connection_context=dataframe.ConnectionContext(url, port, user, pwd))
    >>> experiment_monitor.start()
    """
    def __init__(self, connection_context: ConnectionContext):
        self.config = TaskSchedulerConfig()
        self.config.set_connection_context(EmbeddedUI.create_connection_context(connection_context))
        self.config.set_task_execution_interval(1)

    def start(self):
        """
        Call the method to create an experiment monitor UI.
        """
        self.config.start_task_scheduler()

    def cancel(self):
        """
        Call the method to interrupt the execution of the experiment monitor.
        """
        EmbeddedUI.generate_file(self.config.task_scheduler.interrupt_file_path, "")
