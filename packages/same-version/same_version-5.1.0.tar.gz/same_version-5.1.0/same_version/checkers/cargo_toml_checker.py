import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.cargo_toml_extractor import CargoTomlExtractor

logger = logging.getLogger(__name__)


class CargoTomlChecker(FileChecker):

    def __init__(self, extractor: CargoTomlExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  