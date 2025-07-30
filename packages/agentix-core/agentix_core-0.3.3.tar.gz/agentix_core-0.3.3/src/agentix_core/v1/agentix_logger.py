import logging

class AgentixLogger:
    def __init__(self, name: str, task_key: str = None, log_level: int = logging.INFO):
        self.task_key = task_key
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
            print(f"No Logger Handler found, Initializing logger for {name} with log level {log_level}")
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)

    def set_task_key(self, task_key: str):
        self.task_key = task_key

    def _prefix(self, msg: str):
        return f"[{self.task_key}] | {msg}" if self.task_key else msg

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(self._prefix(msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(self._prefix(msg), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(self._prefix(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(self._prefix(msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(self._prefix(msg), *args, **kwargs)

    def set_task_key(self, task_key: str):
        self.task_key = task_key