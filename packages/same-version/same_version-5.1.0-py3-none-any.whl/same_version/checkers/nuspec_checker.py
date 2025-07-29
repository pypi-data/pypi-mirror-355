import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.nuspec_extractor import NuspecExtractor

logger = logging.getLogger(__name__)


class NuspecChecker(FileChecker):

    def __init__(self, extractor: NuspecExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  