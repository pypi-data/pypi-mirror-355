import xml.etree.ElementTree as ET
from argparse import Namespace

from same_version.extractors.xml_extractor import XmlExtractor


class NuspecExtractor(XmlExtractor):
    
    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--nuspec-path'
        default_target_name: str = ".nuspec"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        version: str | None = None
        tree: ET.ElementTree[ET.Element[str]] | None = data.get('tree', None)
        if tree is not None:

            try:
                root = tree.getroot()

                # XML structure: <package><metadata><version>...</version>
                # The {*} is used for optional namespaces that some tools prepend
                metadata = root.find('metadata') or root.find('{*}metadata')

                if metadata is not None:
                    version_elem = metadata.find('version') or metadata.find('{*}version')
                    if version_elem is not None and version_elem.text:
                        version = version_elem.text.strip()

            except Exception:
                version = None

        return version
