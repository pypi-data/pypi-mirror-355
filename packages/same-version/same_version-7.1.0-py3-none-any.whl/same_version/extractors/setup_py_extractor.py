import ast
import logging
from argparse import Namespace

from same_version.extractors.py_ast_extractor import PyAstExtractor

logger = logging.getLogger(__name__)

class SetupPyExtractor(PyAstExtractor):

    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--setup-py-path'
        default_target_name: str = "setup.py"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        tree = data.get('tree', None)
        if tree is None:
            return None

        visitor = SetupPyVisitor()
        visitor.visit(tree)
        
        version: str | None = visitor.version
        if not isinstance(version, str) and version is not None:
            version = None

        return version


class SetupPyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.version = None
        self.assignments = {}

    def visit_Assign(self, node):
        # Capture simple assignments: version = "1.2.3"
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            value = self._get_constant_value(node.value)
            if value is not None:
                self.assignments[var_name] = value

    def visit_Call(self, node):
        # Look for any call to 'setup' function
        if self._is_setup_call(node):
            for kw in node.keywords:
                if kw.arg == "version":
                    value = self._get_constant_value(kw.value)
                    if value is None and isinstance(kw.value, ast.Name):
                        # Handle: version=version_var
                        value = self.assignments.get(kw.value.id)
                    if value is not None:
                        self.version = value

    def _get_constant_value(self, node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, str):
                return node.value
        elif isinstance(node, ast.Str):  # Python <3.8
            return node.s
        return None

    def _is_setup_call(self, node):
        # Accept setup() or setuptools.setup()
        if isinstance(node.func, ast.Name):
            return node.func.id == "setup"
        if isinstance(node.func, ast.Attribute):
            return (
                node.func.attr == "setup" and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == "setuptools"
            )
        return False
