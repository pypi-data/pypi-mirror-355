
from argparse import Namespace

from same_version.extractors.file_extractor import FileExtractor


class RDescriptionExtractor(FileExtractor):
    
    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--r-description-path'
        default_target_name: str = "DESCRIPTION"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )
    
    
    def _get_version_from_data(self, data: dict) -> str | None:
        version = data.get('version', None)
        return version

    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:
            with open(self.target_file_path, 'r') as file:
                for line in file:
                    if line.startswith("Version:"):
                        data['version'] = line.split(":", 1)[1].strip()
                        break
        return data
    


    
