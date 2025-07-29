import ast

from same_version.extractors.file_extractor import FileExtractor


class PyAstExtractor(FileExtractor):
    
    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:
            with open(self.target_file_path, 'r', encoding='utf-8') as f:
                data['tree'] = ast.parse(f.read(), filename=self.target_file_path.resolve())
        return data