from argparse import Namespace

from same_version.extractors.json_extractor import JsonExtractor


class RoCrateMetadataJsonExtractor(JsonExtractor):
    
    def __init__(self, cli_args: Namespace):
        target_cli_parameter_name: str = '--ro-crate-metadata-json-path'
        default_target_name: str = "ro-crate-metadata.json"
        self.cli_args = cli_args
        super().__init__(
            target_file_path=self._create_target_file_path_from_cli_arg(cli_args=cli_args, cli_arg_parameter=target_cli_parameter_name), 
            default_target_name=default_target_name, 
            target_cli_parameter_name=target_cli_parameter_name
        )

    def _get_version_from_data(self, data: dict) -> str | None:
        version = None
        graph: list | None = data.get('@graph', None)
        if isinstance(graph, list) and graph is not None:
            id = self.cli_args.get('ro_crate_metadata_json_id', None)
            if id is not None:
                for resource in graph:
                    resource_id = resource.get('@id', None) 
                    if resource_id == id:
                        version = resource.get('version', None)
                        break
        return version