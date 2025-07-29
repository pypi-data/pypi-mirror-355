from argparse import Namespace

from same_version.checkers.checker import Checker
from same_version.extractors.github_event_extractor import GitHubEventExtractor


class GitHubEventChecker(Checker):
    def __init__(self, extractor: GitHubEventExtractor, cli_args: Namespace):
        super().__init__(extractor=extractor, cli_args=cli_args) 