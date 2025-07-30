import ast
import logging
from argparse import Namespace

from same_version.extractors.py_ast_extractor import PyAstExtractor

logger = logging.getLogger(__name__)

class PyVersionAssignmentExtractor(PyAstExtractor):
    
    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--py-version-assignment-path'
        default_target_name: str = "Python file with __version__ assignment to a literal string"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        version = None
        tree = data.get('tree', None)
        if tree is not None:
            try:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if (isinstance(target, ast.Name) and
                                target.id == "__version__" and
                                isinstance(node.value, ast.Constant) and
                                isinstance(node.value.value, str)):
                                return node.value.value
            except Exception:
                version = None
        return version