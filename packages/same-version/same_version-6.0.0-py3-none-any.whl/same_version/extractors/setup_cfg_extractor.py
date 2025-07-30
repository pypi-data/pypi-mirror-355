import configparser
from argparse import Namespace

from same_version.extractors.ini_extractor import IniExtractor


class SetupCfgExtractor(IniExtractor):

    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--setup-cfg-path'
        default_target_name: str = "setup.cfg"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        config: configparser.ConfigParser | None = data.get('config', None)
        if config is None:
            return None
        
        if not config.has_section('metadata'):
            return None

        if not config.has_option('metadata', 'version'):
            return None

        version = config.get('metadata', 'version')

        if isinstance(version, str):
            version = version.strip() 
            
        return version