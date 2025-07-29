import logging
from argparse import Namespace

from same_version.checkers.file_checker import FileChecker
from same_version.extractors.pom_xml_extractor import PomXmlExtractor

logger = logging.getLogger(__name__)


class PomXmlChecker(FileChecker):

    def __init__(self, extractor: PomXmlExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args)  