import logging
from argparse import Namespace

from same_version.extractors.json_extractor import JsonExtractor

logger = logging.getLogger(__name__)

class ZenodoJsonExtractor(JsonExtractor):

    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--zenodo-json-path'
        default_target_name: str = ".zenodo.json"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        version = data.get('version', None)
        return version