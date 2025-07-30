import configparser

from same_version.extractors.file_extractor import FileExtractor


class IniExtractor(FileExtractor):

    def _get_data(self) -> dict:
        data = {}
        if self.target_file_path and self.target_exists:            

            config = configparser.ConfigParser()

            # configparser lowercases keys by default — we'll preserve case sensitivity for safety
            setattr(config, 'optionxform', str)
            config.read(self.target_file_path)
            data['config'] = config

        return data
    

