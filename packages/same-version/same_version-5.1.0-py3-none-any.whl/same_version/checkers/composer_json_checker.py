import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.composer_json_extractor import ComposerJsonExtractor

logger = logging.getLogger(__name__)

class ComposerJsonChecker(FileChecker):

    def __init__(self, extractor: ComposerJsonExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)   