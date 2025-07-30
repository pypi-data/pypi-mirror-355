from same_version.checkers.checker import Checker


class FileChecker(Checker):
    
    def _log_missing_target(self, msg: str | None = None):
        msg = f"File for parameter(s) {self.target_cli_parameter_name} does not exist: {self.target_name}"
        super()._log_missing_target(msg=msg)