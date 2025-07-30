import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.py_version_assignment_extractor import (
    PyVersionAssignmentExtractor,
)

logger = logging.getLogger(__name__)


class PyVersionAssignmentChecker(FileChecker):

    def __init__(self, extractor: PyVersionAssignmentExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  