import json

from same_version.extractors.file_extractor import FileExtractor


class JsonExtractor(FileExtractor):

    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:
            with open(self.target_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return data