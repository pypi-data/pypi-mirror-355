import xml.etree.ElementTree as ET

from same_version.extractors.file_extractor import FileExtractor


class XmlExtractor(FileExtractor):
    
    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:
            try:
                with open(self.target_file_path, 'rb'):
                    data['tree'] = ET.parse(self.target_file_path)
            except Exception:
                pass
        return data