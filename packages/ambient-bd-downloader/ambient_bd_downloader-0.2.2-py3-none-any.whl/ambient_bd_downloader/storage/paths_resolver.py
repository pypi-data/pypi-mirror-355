import os
import logging


class PathsResolver:

    def __init__(self, path=os.path.join('..', 'downloaded_data')):
        self._logger = logging.getLogger('PathsResolver')
        self._main_dir = None
        self.set_main_dir(path)

    def set_main_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.isdir(path):
            raise ValueError(f'Main storage: {path} is not a directory')
        self._main_dir = path
        self._logger.info(f'Using storage dir: {os.path.abspath(self._main_dir)}')

    def get_main_dir(self):
        return self._main_dir

    def get_subject_dir(self, subject_id):
        subject_dir = os.path.join(self._main_dir, subject_id)
        if not os.path.exists(subject_dir):
            os.makedirs(subject_dir)
        return subject_dir

    def get_subject_sys_dir(self, subject_id):
        sys_dir = os.path.join(self.get_subject_dir(subject_id), 'sys')
        if not os.path.exists(sys_dir):
            os.makedirs(sys_dir)
        return sys_dir

    def get_subject_data_dir(self, subject_id):
        data_dir = os.path.join(self.get_subject_dir(subject_id), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir

    def get_subject_raw_dir(self, subject_id):
        raw_dir = os.path.join(self.get_subject_dir(subject_id), 'raw')
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir)
        return raw_dir

    def get_subject_last_session(self, subject_id):
        return os.path.join(self.get_subject_sys_dir(subject_id), 'last_session.json')

    def has_last_session(self, subject_id):
        last_path = os.path.join(self._main_dir, subject_id, 'sys', 'last_session.json')
        return os.path.exists(last_path)

    def get_subject_global_report(self, subject_id):
        return os.path.join(self.get_subject_data_dir(subject_id), 'all_sessions_report.csv')
