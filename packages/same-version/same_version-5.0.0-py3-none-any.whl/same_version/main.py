#!/usr/bin/env python3

import argparse
import logging
import sys

from same_version.checkers.cargo_toml_checker import CargoTomlChecker
from same_version.checkers.checker import Checker
from same_version.checkers.citation_cff_checker import CitationCffChecker
from same_version.checkers.codemeta_json_checker import CodeMetaJsonChecker
from same_version.checkers.composer_json_checker import ComposerJsonChecker
from same_version.checkers.github_event_checker import GitHubEventChecker
from same_version.checkers.nuspec_checker import NuspecChecker
from same_version.checkers.package_json_checker import PackageJsonChecker
from same_version.checkers.pom_xml_checker import PomXmlChecker
from same_version.checkers.py_version_assignment_checker import (
    PyVersionAssignmentChecker,
)
from same_version.checkers.pyproject_toml_checker import PyprojectTomlChecker
from same_version.checkers.r_description_checker import RDescriptionChecker
from same_version.checkers.ro_crate_metadata_json_checker import (
    RoCrateMetadataJsonChecker,
)
from same_version.checkers.setup_py_checker import SetupPyChecker
from same_version.checkers.zenodo_json_checker import ZenodoJsonChecker
from same_version.extractors.cargo_toml_extractor import CargoTomlExtractor
from same_version.extractors.citation_cff_extractor import CitationCffExtractor
from same_version.extractors.cli_extractor import CliExtractor
from same_version.extractors.codemeta_json_extractor import CodeMetaJsonExtractor
from same_version.extractors.composer_json_extractor import ComposerJsonExtractor
from same_version.extractors.github_event_extractor import GitHubEventExtractor
from same_version.extractors.nuspec_extractor import NuspecExtractor
from same_version.extractors.package_json_extractor import PackageJsonExtractor
from same_version.extractors.pom_xml_extractor import PomXmlExtractor
from same_version.extractors.py_version_assignment_extractor import (
    PyVersionAssignmentExtractor,
)
from same_version.extractors.pyproject_toml_extractor import (
    PyprojectTomlExtractor,
)
from same_version.extractors.r_description_extractor import RDescriptionExtractor
from same_version.extractors.ro_crate_metadata_json_extractor import (
    RoCrateMetadataJsonExtractor,
)
from same_version.extractors.setup_py_extractor import SetupPyExtractor
from same_version.extractors.zenodo_json_extractor import ZenodoJsonExtractor
from same_version.log_collector import get_log_collector

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check metadata files for consistent software versions using canonical PEP 440 and SemVer")
    parser.add_argument('--base-version', required=False, help='A base version from which to check')
    parser.add_argument('--fail-for-missing-file', default=False, required=False, help='Fail for any checked file that is missing')
    parser.add_argument('--check-citation-cff', default=True, required=False, help='Check CITATION.cff? (true/false)')
    parser.add_argument('--citation-cff-path', default='CITATION.cff', required=False, help='Path to CITATION.cff file')
    parser.add_argument('--check-pyproject-toml', default=True, required=False, help='Check pyproject.toml? (true/false)')
    parser.add_argument('--pyproject-toml-path', default='pyproject.toml', required=False, help='Path to pyproject.toml file')
    parser.add_argument('--check-codemeta-json', default=True, required=False, help='Check codemeta.json? (true/false)')
    parser.add_argument('--codemeta-json-path', default='codemeta.json', required=False, help='Path to codemeta.json')
    parser.add_argument('--check-zenodo-json', default=True, required=False, help='Check .zenodo.json? (true/false)')
    parser.add_argument('--zenodo-json-path', default='.zenodo.json', required=False, help='Path to .zenodo.json')
    parser.add_argument('--check-package-json', default=True, required=False, help='Check package.json? (true/false)')
    parser.add_argument('--package-json-path', default='package.json', required=False, help='Path to package.json')
    parser.add_argument('--check-setup-py', default=True, required=False, help='Check setup.py? (true/false)')
    parser.add_argument('--setup-py-path', default='setup.py', required=False, help='Path to setup.py')
    
    parser.add_argument('--check-r-description', default=True, required=False, help='Check R DESCRIPTION file? (true/false)')
    parser.add_argument('--r-description-path', default='DESCRIPTION', required=False, help='Path to R DESCRIPTION file')
    
    parser.add_argument('--check-composer-json', default=True, required=False, help='Check setup.py? (true/false)')
    parser.add_argument('--composer-json-path', default='composer.json', required=False, help='Path to composer.json')
    
    parser.add_argument('--check-pom-xml', default=True, required=False, help='Check pom.xml? (true/false)')
    parser.add_argument('--pom-xml-path', default='pom.xml', required=False, help='Path to pom.xml')
    
    parser.add_argument('--check-nuspec', default=True, required=False, help='Check .nuspec? (true/false)')
    parser.add_argument('--nuspec-path', default='.nuspec', required=False, help='Path to .nuspec')
    
    parser.add_argument('--check-cargo-toml', default=True, required=False, help='Check Cargo.toml? (true/false)')
    parser.add_argument('--cargo-toml-path', default='Cargo.toml', required=False, help='Path to Cargo.toml')

    parser.add_argument('--check-py-version-assignment', default=False, required=False, help='Check Python file with __version__ assignment? (true/false)')
    parser.add_argument('--py-version-assignment-path', required=False, help='Path to Python file with __version__ assignment')
    
    parser.add_argument('--check-ro-crate-metadata-json', default=False, required=False, help='Check ro-crate-metadata.json? (true/false)')
    parser.add_argument('--ro-crate-metadata-json-path', default='ro-crate-metadata.json', required=False, help='Path to ro-crate-metadata.json')
    parser.add_argument('--ro-crate-metadata-json-id', required=False, help='@id field for the resource in ro-crate-metadata.json')

    parser.add_argument('--check-github-event', default=False, required=False, help='Check GitHub events? (true/false)')
    parser.add_argument('--github-event-name', required=False, help='GitHub event name (push/release)')
    parser.add_argument('--github-event-ref', required=False, help='GitHub ref (for push event)')
    parser.add_argument('--github-event-release-tag', required=False, help='GitHub release tag name (for release event)')

    return parser.parse_args()

# --- Main ---


def main():
    cli_args: argparse.Namespace = parse_args()

    base_version_str: str | None = CliExtractor(cli_args=cli_args).extract_version()

    checkers: list[Checker] = []

    logger.info('📦 Extracting software version metadata...')

    # GitHub Event
    if str(getattr(cli_args, 'check_github_event', '') or '').lower() == 'true':
        github_event_extractor: GitHubEventExtractor = GitHubEventExtractor(cli_args=cli_args)
        github_event_checker: GitHubEventChecker = GitHubEventChecker(extractor=github_event_extractor, cli_args=cli_args)
        checkers.append(github_event_checker)

    # CITATION.cff
    if str(getattr(cli_args, 'check_citation_cff', '') or '').lower() == 'true':
        citation_cff_extractor: CitationCffExtractor = CitationCffExtractor(cli_args=cli_args)
        citation_cff_checker: CitationCffChecker = CitationCffChecker(extractor=citation_cff_extractor, cli_args=cli_args)
        checkers.append(citation_cff_checker)

    # pyproject.toml
    if str(getattr(cli_args, 'check_pyproject_toml', '') or '').lower() == 'true':
        pyproject_toml_extractor: PyprojectTomlExtractor = PyprojectTomlExtractor(cli_args=cli_args)
        pyproject_toml_checker: PyprojectTomlChecker = PyprojectTomlChecker(extractor=pyproject_toml_extractor, cli_args=cli_args)
        checkers.append(pyproject_toml_checker)


    # setup.py
    if str(getattr(cli_args, 'check_setup_py', '') or '').lower() == 'true':
        setup_py_extractor: SetupPyExtractor = SetupPyExtractor(cli_args=cli_args)
        setup_py_checker: SetupPyChecker = SetupPyChecker(extractor=setup_py_extractor, cli_args=cli_args)
        checkers.append(setup_py_checker)

    # package.json
    if str(getattr(cli_args, 'check_package_json', '') or '').lower() == 'true':
        package_json_extractor: PackageJsonExtractor = PackageJsonExtractor(cli_args=cli_args)
        package_json_checker: PackageJsonChecker = PackageJsonChecker(extractor=package_json_extractor, cli_args=cli_args)
        checkers.append(package_json_checker)

    # codemeta.json
    if str(getattr(cli_args, 'check_codemeta_json', '') or '').lower() == 'true':
        codemeta_json_extractor: CodeMetaJsonExtractor = CodeMetaJsonExtractor(cli_args=cli_args)
        codemeta_json_checker: CodeMetaJsonChecker = CodeMetaJsonChecker(extractor=codemeta_json_extractor, cli_args=cli_args)
        checkers.append(codemeta_json_checker)

    # composer.json
    if str(getattr(cli_args, 'check_composer_json', '') or '').lower() == 'true':
        composer_json_extractor: ComposerJsonExtractor = ComposerJsonExtractor(cli_args=cli_args)
        composer_json_checker: ComposerJsonChecker = ComposerJsonChecker(extractor=composer_json_extractor, cli_args=cli_args)
        checkers.append(composer_json_checker)

    # Cargo.toml
    if str(getattr(cli_args, 'check_cargo_toml', '') or '').lower() == 'true':
        cargo_toml_extractor: CargoTomlExtractor = CargoTomlExtractor(cli_args=cli_args)
        cargo_toml_checker: CargoTomlChecker = CargoTomlChecker(extractor=cargo_toml_extractor, cli_args=cli_args)
        checkers.append(cargo_toml_checker)

    # pom.xml
    if str(getattr(cli_args, 'check_pom_xml', '') or '').lower() == 'true':
        pom_xml_extractor: PomXmlExtractor = PomXmlExtractor(cli_args=cli_args)
        pom_xml_checker: PomXmlChecker = PomXmlChecker(extractor=pom_xml_extractor, cli_args=cli_args)
        checkers.append(pom_xml_checker)

    # .nuspec
    if str(getattr(cli_args, 'check_nuspec', '') or '').lower() == 'true':
        nuspec_extractor: NuspecExtractor = NuspecExtractor(cli_args=cli_args)
        nuspec_checker: NuspecChecker = NuspecChecker(extractor=nuspec_extractor, cli_args=cli_args)
        checkers.append(nuspec_checker)

    # R DESCRIPTION file
    if str(getattr(cli_args, 'check_r_description', '') or '').lower() == 'true':
        r_description_extractor: RDescriptionExtractor = RDescriptionExtractor(cli_args=cli_args)
        r_description_checker: RDescriptionChecker = RDescriptionChecker(extractor=r_description_extractor, cli_args=cli_args)
        checkers.append(r_description_checker)

    # Python file with `__version__` assignment
    if str(getattr(cli_args, 'check_py_version_assignment', '') or '').lower() == 'true':
        py_version_assignment_extractor: PyVersionAssignmentExtractor = PyVersionAssignmentExtractor(cli_args=cli_args)
        py_version_assignment_checker: PyVersionAssignmentChecker = PyVersionAssignmentChecker(extractor=py_version_assignment_extractor, cli_args=cli_args)
        checkers.append(py_version_assignment_checker)

    # ro-crate-metadata.json
    if str(getattr(cli_args, 'check_ro_crate_metadata_json', '') or '').lower() == 'true':
        ro_crate_metadata_json_extractor: RoCrateMetadataJsonExtractor = RoCrateMetadataJsonExtractor(cli_args=cli_args)
        ro_crate_metadata_json_checker: RoCrateMetadataJsonChecker = RoCrateMetadataJsonChecker(extractor=ro_crate_metadata_json_extractor, cli_args=cli_args)
        checkers.append(ro_crate_metadata_json_checker)

    # .zenodo.json
    if str(getattr(cli_args, 'check_zenodo_json', '') or '').lower() == 'true':
        zenodo_json_extractor: ZenodoJsonExtractor = ZenodoJsonExtractor(cli_args=cli_args)
        zenodo_json_checker: ZenodoJsonChecker = ZenodoJsonChecker(extractor=zenodo_json_extractor, cli_args=cli_args)
        checkers.append(zenodo_json_checker)

    # Loop through checkers
    logger.info('📦 Checking software version metadata...')

    for checker in checkers:
        # find the base version if it does not exist
        if base_version_str is None and checker.target_version_str is not None:
            base_version_str = checker.target_version_str
            logger.info(f'📦 Using {checker.target_name} for base version: {base_version_str}')
        else:
            checker.check(base_version_str=base_version_str)

    # Final result
    
    if get_log_collector().get_error_logs():
        logger.error("❌ Some versions do not match!")
        sys.exit(1)
    else:
        if base_version_str is None:
            logger.warning("⚠️ No base version found. No versions to match.")
        else:
            logger.info("✅ All versions match!")

if __name__ == '__main__':
    main()
