import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.setup_py_extractor import SetupPyExtractor

logger = logging.getLogger(__name__)

class SetupPyChecker(FileChecker):

    def __init__(self, extractor: SetupPyExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  