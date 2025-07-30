import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.zenodo_json_extractor import (
    ZenodoJsonExtractor,
)

logger = logging.getLogger(__name__)

class ZenodoJsonChecker(FileChecker):

    def __init__(self, extractor: ZenodoJsonExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  