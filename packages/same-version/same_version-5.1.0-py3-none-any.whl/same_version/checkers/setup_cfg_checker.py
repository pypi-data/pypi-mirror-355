from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.setup_cfg_extractor import SetupCfgExtractor


class SetupCfgChecker(FileChecker):
    
    def __init__(self, extractor: SetupCfgExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  