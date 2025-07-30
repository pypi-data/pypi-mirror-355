import logging
from argparse import Namespace

from verple.verple import Verple

from same_version.extractors.extractor import Extractor

logger = logging.getLogger(__name__)

class Checker():

    def __init__(self, extractor: Extractor, cli_args: Namespace):
        self.extractor = extractor        
        self.cli_args = cli_args
        self._extracted_version: str | None = self.extractor.extract_version()
        self._verple_version: Verple | None = self.create_verple_version(self._extracted_version)
    
    def create_verple_version(self, version_str: str | None) -> Verple | None:
        if version_str is None:
            return None
        try:
            return Verple.parse(version_str)
        except ValueError:
            return None
    
    @property
    def target_version_str(self) -> str | None:
        return self._extracted_version
    
    @property
    def target_version(self) -> Verple | None:
        return self._verple_version
    
    @property
    def target_exists(self) -> bool:
        return self.extractor.target_exists

    @property    
    def target_name(self) -> str | None:
        return self.extractor.target_name
    
    @property
    def target_cli_parameter_name(self) -> str | None:
        return self.extractor.target_cli_parameter_name
    
    def check(self, base_version_str: str | None) -> bool:
        if base_version_str is None:
                return True
        base_version: Verple | None = self.create_verple_version(version_str=base_version_str)
        if self.target_exists:
            if base_version != self.target_version:
                self._log_version_mismatch(base_version_str=base_version_str)
                return False
            else:
                return True
        else:
            self._log_missing_target()
            return False

    def _log_version_mismatch(self, base_version_str: str | None):
        logger.error(f"❌ Version mismatch: {self.target_name} {self.target_version_str} != base version {base_version_str}")

    def _log_missing_target(self, msg: str | None = None):
        if msg is None:
            msg = f"Data source for parameter {self.target_cli_parameter_name} does not exist: {self.target_name}"

        if str(getattr(self.cli_args, 'fail_for_missing_file', '') or '').lower() == 'true':
            msg = "❌ " + msg
            logger.error(msg)
        else:
            msg = "⚠️ " + msg
            logger.warning(msg)
     


