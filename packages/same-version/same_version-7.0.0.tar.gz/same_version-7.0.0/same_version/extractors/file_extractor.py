from argparse import Namespace
from pathlib import Path

from same_version.extractors.extractor import Extractor


class FileExtractor(Extractor):
    def __init__(self, target_file_path: Path | None, default_target_name: str, target_cli_parameter_name: str):
        self._target_file_path = target_file_path
        self._default_target_name = default_target_name
        self._target_cli_parameter_name = target_cli_parameter_name

    @property
    def target_file_path(self) -> Path | None:
        return self._target_file_path

    @property
    def target_exists(self) -> bool:
        return self._target_file_path is not None and self._target_file_path.exists()
    
    @property
    def target_name(self) -> str | None:
        if self.target_exists:
            return str(self._target_file_path)
        else:
            return self._default_target_name
    
    @property    
    def target_cli_parameter_name(self) -> str | None:
        return self._target_cli_parameter_name
    
    def _create_target_file_path_from_cli_arg(self, cli_args: Namespace, cli_arg_parameter: str) -> Path | None:
        cli_arg_parameter = cli_arg_parameter.lstrip('-').replace('-', '_') # change parameters like '--some-parameter' to 'some_parameter'
        path_str: str | None = getattr(cli_args, cli_arg_parameter, None)
        if path_str is None or str(path_str).strip() == '':
            return None
        else:
            return Path(path_str)