import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.pyproject_toml_extractor import (
    PyprojectTomlExtractor,
)

logger = logging.getLogger(__name__)


class PyprojectTomlChecker(FileChecker):

    def __init__(self, extractor: PyprojectTomlExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  