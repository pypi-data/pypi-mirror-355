import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.package_json_extractor import PackageJsonExtractor

logger = logging.getLogger(__name__)

class PackageJsonChecker(FileChecker):
    
    def __init__(self, extractor: PackageJsonExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  
