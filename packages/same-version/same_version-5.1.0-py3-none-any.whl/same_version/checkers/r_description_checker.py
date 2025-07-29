import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.r_description_extractor import RDescriptionExtractor

logger = logging.getLogger(__name__)


class RDescriptionChecker(FileChecker):

    def __init__(self, extractor: RDescriptionExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  