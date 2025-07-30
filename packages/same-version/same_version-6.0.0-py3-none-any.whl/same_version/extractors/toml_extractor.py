
import tomli

from same_version.extractors.file_extractor import FileExtractor


class TomlExtractor(FileExtractor):

    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:
            with open(self.target_file_path, 'rb') as f:
                data = tomli.load(f)
        return data