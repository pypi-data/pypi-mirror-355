import xml.etree.ElementTree as ET
from argparse import Namespace

from same_version.extractors.xml_extractor import XmlExtractor


class PomXmlExtractor(XmlExtractor):
    
    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--pom-xml-path'
        default_target_name: str = "pom.xml"
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        version = None
        tree: ET.ElementTree[ET.Element[str]] | None = data.get('tree', None)
        if tree is not None:

            try:
                root = tree.getroot()

                # Handle XML namespaces
                ns = {'m': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}

                # Attempt to find the <version> element directly under <project>
                version = root.find('m:version', ns)
                if version is not None:
                    version = version.text.strip()
                else:
                    # If <version> is not directly in <project>, check for a parent <parent><version>
                    parent_version = root.find('m:parent/m:version', ns)
                    if parent_version is not None:
                        version = parent_version.text.strip()

            except Exception:
                version = None

        return version


    
