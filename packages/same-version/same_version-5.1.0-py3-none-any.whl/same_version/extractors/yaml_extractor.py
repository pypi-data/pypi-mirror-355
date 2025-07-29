import yaml

from same_version.extractors.file_extractor import FileExtractor


class YamlExtractor(FileExtractor):

    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:
            with open(self.target_file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        return data