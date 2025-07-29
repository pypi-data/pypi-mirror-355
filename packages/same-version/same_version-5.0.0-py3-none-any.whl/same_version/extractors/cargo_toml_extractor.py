import logging
from argparse import Namespace

from same_version.extractors.toml_extractor import TomlExtractor

logger = logging.getLogger(__name__)

class CargoTomlExtractor(TomlExtractor):

    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--cargo-toml-path'
        default_target_name: str = "Cargo.toml"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )
    
    def _get_version_from_data(self, data: dict) -> str | None:
        project = data.get('package', {})
        version = project.get('version')
        return version
    
    def _log_missing_version_error(self, data: dict):
        logger.error(f"❌ {self.target_name} missing [project] version!")
