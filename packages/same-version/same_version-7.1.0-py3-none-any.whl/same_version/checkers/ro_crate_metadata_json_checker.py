import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.ro_crate_metadata_json_extractor import (
    RoCrateMetadataJsonExtractor,
)

logger = logging.getLogger(__name__)

class RoCrateMetadataJsonChecker(FileChecker):

    def __init__(self, extractor: RoCrateMetadataJsonExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)   