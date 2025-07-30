# 🚀 same-version

Automatically ensures your software version metadata is consistent across key project files.

---

## 📦 What does it do?

`same-version` checks that software version metadata is consistent across your project files. It can stop GitHub pull requests and local git commits/pushes of projects with inconsistent software version metadata.

Helps ensure:

✅ Reproducibility  
✅ Correct citations  
✅ Consistent packaging metadata  
✅ Accurate DOIs (Zenodo)  
✅ Cross-language version consistency (Python / JS / metadata)

It can be used in **three ways**, each of which have different capabilities:

### 1️⃣ GitHub Action

- Runs in GitHub Actions
- Can block:
  - Inconsistent **pull requests** (which helps prevent inconsistent **tags** and **GitHub releases** )
- Can report (but only after the tag/release has been created):
  - Incorrect **tags**
  - Incorrect **GitHub releases**

  _Note: GitHub Actions cannot block tags or releases after they have been created.  
This workflow runs after the tag or release exists and can report problems, but cannot prevent them from appearing in GitHub UI._


### 2️⃣ Pre-commit hook

- Runs automatically **before each commit and push** (if enabled)
- Can block:
  - Inconsistent **commits**
  - Inconsistent **tags being pushed**

### 3️⃣ Python CLI

- You can run `same-version` manually from the command line
- Useful for:
  - Local checks before release
  - CI checks outside of GitHub Actions
  - Automated scripts

---

## 📋 Features

✅ Ultra-conservative version normalization and strict equality comparison using [Verple](https://pypi.org/project/verple/)

✅ Compare software version metadata from:
- GitHub tag/release
- `CITATION.cff`
- `pyproject.toml` (Python)
- `setup.py` (Python, via static analysis only — no execution)
- `setup.cfg` (Python)
- Python files with `__version__` assignment (static parsing only — must be assigned directly to a string literal)
- `codemeta.json` (General)
- `.zenodo.json` (General)
- `package.json` (JS/TypeScript)
- `composer.json` (PHP)
- `Cargo.toml` (Rust)
- `pom.xml` (Java)
- `.nuspec` (.NET/C#/NuGet)
- `DESCRIPTION` (R)
- `ro-crate-metadata.json` (RO-Crate)


✅ Cross-language support (e.g., Python, R, JS/TypeScript, Java, Rust, PHP, C#)

✅ Cross-standard support for FAIR and Open Science metadata (e.g., CFF, CodeMeta, RO-Crate, Zenodo)

✅ Lightweight, pure Python — no third-party services  

✅ Easy to configure via GitHub Action inputs  

✅ Suitable for reproducible research and software citation best practices

✅ Blocks inconsistent GitHub pull requests (via GitHub Action) 

✅ Reports inconsistent GitHub releases/tags (via GitHub Action) 

✅ Blocks inconsistent commits and tags (via Pre-commit hook)

✅ Modular and extendable for additional software version metadata (via Python CLI)

---

## 🔍 How are versions compared?

`same-version` automatically normalizes all detected versions using [Verple](https://pypi.org/project/verple/), which provides a strict, ultra-conservative version model that fully supports PEP 440, SemVer, Calendar Versioning, and hybrid schemes across ecosystems.

- Verple parses versions from many ecosystems (Python, JavaScript, Rust, Java, PHP, R, etc.).
- Unlike many versioning libraries that attempt to relax equivalence rules, Verple enforces **strict equality**: two versions are only considered equal if every component of the version string matches exactly — including release, pre-release, post-release, dev-release, and local identifiers.
- This ensures that version mismatches across files are caught even if the differences are subtle (e.g. `1.0.0` vs `1.0.0+build123` are considered different).
- For ordering (less-than, greater-than comparisons), Verple allows comparisons only when local identifiers are identical. If local identifiers differ, ordering comparisons are rejected to avoid any ambiguity.

---

## 🔬 Why is Verple ultra-conservative?

Many packaging standards (SemVer, PEP 440) have nuanced rules for equality and ordering:

- SemVer ignores build metadata when determining equality or ordering.
- PEP 440 may allow local identifiers to affect ordering but not equality.

However, for the purpose of cross-file version consistency checking (the core goal of `same-version`), such leniency can mask subtle inconsistencies that may later cause confusion or deployment issues.

By using Verple's conservative model:

✅ Any discrepancy between files will be surfaced explicitly.  
✅ No silent equivalence is assumed across ecosystems.  
✅ Comparison logic remains simple, transparent, and safe for reproducibility.

---

## 🔬 When is this behavior helpful?

Verple's strict comparison is **ideal for version consistency checks**, where exact agreement across files is required:

- ✅ Reproducible research outputs
- ✅ FAIR/Open Science metadata harmonization
- ✅ Software citation accuracy
- ✅ Multi-language package version alignment (Python, JS, R, Rust, etc.)
- ✅ CI/CD pipelines validating metadata consistency

---

## ⚠ When might this behavior be limiting?

Verple’s ultra-conservative model may not be ideal for:

- Dependency resolution (where lenient comparisons are often useful)
- Compatibility checks (where you care about version ranges, not exact equality)
- Package managers that intentionally ignore metadata differences

For those use cases, specialized dependency resolution libraries (e.g. `packaging`, `semver`, `dephell`) may be more appropriate.

---

## 🔍 What files does it check?

| File             | Original Version Format | Normalization |
|------------------|-------------------------|----------------|
| `CITATION.cff`   | PEP 440 / free text     | Verple |
| `pyproject.toml` | PEP 440                 | Verple |
| `setup.cfg`       | PEP 440                 | Verple |
| `setup.py`       | PEP 440                 | Verple |
| `package.json`   | SemVer                  | Verple |
| `codemeta.json`  | Free text               | Verple |
| `.zenodo.json`   | Free text               | Verple |
| `composer.json`  | PHP Composer (SemVer-like) | Verple |
| `Cargo.toml`     | Rust Cargo (SemVer-like) | Verple |
| `pom.xml`        | Maven (loosely SemVer)  | Verple |
| `.nuspec`        | NuGet (SemVer-like)     | Verple |
| `DESCRIPTION`    | Free text               | Verple |
| `__version__` file | PEP 440 (usually)     | Verple |
| `ro-crate-metadata.json` | Free text | Verple |

> ✅ All formats are normalized automatically to Verple before comparison.
 

---

## ⚙️ Inputs

| CLI Parameter                 | GitHub Action Input                     | Description            | Required                 | Default           |
|-------------------------------|-----------------------------------------|--------------------|---------------------|-------------------|
| `--base-version`         | `base_version`                     | Base version from which to compare all other versions  | No | *(empty)*      |
| `--check-github-event`         | `check_github_event`                     | Check GitHut events? (`true` or `false`)  | No | `false`      |
| `--github-event-name`         | `github_event_name`                     | GitHub event name (`push` or `release` or `pull_request`) | No  | *(empty)*      |
| `--github-event-ref`                | `github_event_ref`                            | GitHub ref (for `push` event)       | No           | *(empty)*      |
| `--github-event-release-tag`        | `github_event_release_tag`                    | GitHub release tag name (for `release` event)  | No | *(empty)*      |
| `--fail-for-missing-file`     | `fail_for_missing_file`                 | Fail for any checked file that is missing| No | `false`           |
| `--check-citation-cff`        | `check_citation_cff`                    | Check `CITATION.cff`? (`true/false`)   | No  | `true`            |
| `--citation-cff-path`         | `citation_cff_path`                     | Path to `CITATION.cff`             | No      | `CITATION.cff`    |
| `--check-pyproject-toml`      | `check_pyproject_toml`                  | Check `pyproject.toml`? (`true/false`)  | No  | `true`            |
| `--pyproject-toml-path`       | `pyproject_toml_path`                   | Path to `pyproject.toml`         | No        | `pyproject.toml`  |
| `--check-codemeta-json`       | `check_codemeta_json`                   | Check `codemeta.json`? (`true/false`)  | No  | `true`            |
| `--codemeta-json-path`        | `codemeta_json_path`                    | Path to `codemeta.json`             | No     | `codemeta.json`   |
| `--check-zenodo-json`         | `check_zenodo_json`                     | Check `.zenodo.json`? (`true/false`)  | No   | `true`            |
| `--zenodo-json-path`          | `zenodo_json_path`                      | Path to `.zenodo.json`              | No     | `.zenodo.json`    |
| `--check-package-json`        | `check_package_json`                    | Check `package.json`? (`true/false`)  | No   | `true`            |
| `--package-json-path`         | `package_json_path`                     | Path to `package.json`               | No    | `package.json`    |
| `--check-setup-py`            | `check_setup_py`                        | Check `setup.py`? (`true/false`)     | No    | `true`            |
| `--setup-py-path`             | `setup_py_path`                         | Path to `setup.py`                 | No      | `setup.py`        |
| `--check-setup-cfg`            | `check_setup_cfg`                        | Check `setup.cfg`? (`true/false`)     | No    | `true`            |
| `--setup-cfg-path`             | `setup_cfg_path`                         | Path to `setup.cfg`                 | No      | `setup.cfg`        |
| `--check-py-version-assignment`            | `check_py_version_assignment`                        | Check Python file with `__version__` assignment? (`true/false`)     | No    | `false`            |
| `--py-version-assignment-path`             | `py_version_assignment_path`                         | Path to Python file with `__version__` assignment                 | No      | *(empty)*        |
| `--check-composer-json`        | `check_composer_json`                    | Check `composer.json`? (`true/false`)  | No   | `true`            |
| `--composer-json-path`         | `composer_json_path`                     | Path to `composer.json`               | No    | `composer.json`    |
| `--check-ro-crate-metadata-json`        | `check_ro_crate_metadata_json`                    | Check `ro-crate-metadata.json`? (`true/false`)  | No   | `false`            |
| `--ro-crate-metadata-json-path`         | `ro_crate_metadata_json_path`                     | Path to `ro-crate-metadata.json`               | No    | `ro-crate-metadata.json`    |
| `--ro-crate-metadata-json-id`         | `ro_crate_metadata_json_id`                     | @id of resource in `ro-crate-metadata.json`               | No    | *(empty)*    |
| `--check-cargo-toml`      | `check_cargo_toml`                  | Check `Cargo.toml`? (`true/false`)  | No  | `true`            |
| `--cargo-toml-path`       | `cargo_toml_path`                   | Path to `Cargo.toml`         | No        | `Cargo.toml`  |
| `--check-r-description`      | `check_r_description`                  | Check R `DESCRIPTION` file? (`true/false`)  | No  | `true`            |
| `--r-description-path`       | `r_description_path`                   | Path to R `DESCRIPTION` file         | No        | `DESCRIPTION`  |
| `--check-pom-xml`      | `check_pom_xml`                  | Check `pom.xml`? (`true/false`)  | No  | `true`            |
| `--pom-xml-path`       | `pom_xml_path`                   | Path to `pom.xml`         | No        | `pom.xml`  |
| `--check-nuspec`      | `check_nu_spec`                  | Check `.nuspec`? (`true/false`)  | No  | `true`            |
| `--nuspec-path`       | `nuspec_path`                   | Path to `.nuspec`         | No        | `.nuspec`  |


---


## 🎯 When does it run?

### GitHub Action:

- On **pull requests** (blocks inconsistent PRs)
- On **push of version tags** (reports incorrect tags after tag creation)
- On **published GitHub releases** (reports incorrect releases after release creation)
- Manually (via `workflow_dispatch`)


### Pre-commit hook:

- **Before each commit** (`pre-commit` hook)
- **Before pushing commits or tags** (`pre-push` hook)

### CLI:

- **Anytime**, on demand

---

## 🛠 How to use

---

### 1️⃣ Using in GitHub Actions

#### To block inconsistent pull requests:

```yaml
name: Check version consistency on pull requests for Python project using pyproject.toml

on:
  pull_request:

jobs:
  check-version:
    runs-on: ubuntu-latest

    steps:

      - uses: actions/checkout@v4

      - name: Install Python
        uses: actions/setup-python@v5
        with:
          python-version: ">=3.10"

      - name: Run same-version
        uses: willynilly/same-version@v7.0.0
        with:
          fail_for_missing_file: false
          check_github_event: true
          github_event_name: ${{ github.event_name }}
          github_event_ref: ${{ github.ref }}
          github_event_release_tag: ${{ github.event.release.tag_name }}
          check_pyproject_toml: true
          check_citation_cff: true
          check_codemeta_json: true
          check_zenodo_json: true
          check_setup_cfg: false
          check_setup_py: false
          check_r_description: false
          check_cargo_toml: false
          check_py_version_assignment: false
          check_pom_xml: false
          check_nuspec: false
          check_composer_json: false
          check_ro_crate_metadata_json: false
```

---

#### To report (BUT NOT BLOCK) incorrect tags/releases:

```yaml
name: Check version consistency on tags/releases for Python project using pyproject.toml

on:
  push:
    tags:
      - 'v*.*.*'
  release:
    types: [published]

jobs:
  check-version:
    runs-on: ubuntu-latest

    steps:

      - uses: actions/checkout@v4

      - name: Install Python
        uses: actions/setup-python@v5
        with:
          python-version: ">=3.10"

      - name: Run same-version
        uses: willynilly/same-version@v7.0.0
        with:
          fail_for_missing_file: false
          check_github_event: true
          github_event_name: ${{ github.event_name }}
          github_event_ref: ${{ github.ref }}
          github_event_release_tag: ${{ github.event.release.tag_name }}
          check_pyproject_toml: true
          check_citation_cff: true
          check_codemeta_json: true
          check_zenodo_json: true
          check_setup_cfg: false
          check_setup_py: false
          check_r_description: false
          check_cargo_toml: false
          check_py_version_assignment: false
          check_pom_xml: false
          check_nuspec: false
          check_composer_json: false
          check_ro_crate_metadata_json: false
```

---

### 2️⃣ Using with pre-commit hooks

You can configure a pre-commit hook to block:

✅ Commits with inconsistent version metadata (`pre-commit`)  
✅ Tags with inconsistent version metadata (`pre-push`)

#### Adding the hook:

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/willynilly/same-version
    rev: v7.0.0  # Use latest tag
    hooks:
      - id: same-version
        stages: [pre-commit, pre-push]

```

#### Installing the hooks:

```bash
# Install the pre-commit tool if you have not already installed it
pip install pre-commit
```

```bash
# Install for both pre-commit and pre-push
pre-commit install -t pre-commit -t pre-push
```

#### Manually run the hook (optional):

```bash
pre-commit run same-version --all-files
```

---

### 3️⃣ Using the CLI manually

After installing the package:

```bash
pip install same-version  # or pip install .
```

Run the CLI:

```bash
same-version
```

By default, it will scan all files, but not GitHub events. You can specify additiona parameters (see the `action.yml` of this GitHub Action for a robust example).

By default, the tool will not fail if some of the files are missing. This inclusively checks as many file types as possible without additional configuration.
However, you may want to be strict and fail if any files used during checking is missing.
Here's an example of failing if any files are missing for a Python project that uses a CITATION.CFF file and pyproject.toml file, any of the other supported files that contain software version metatadata (e.g., codemeta.json, setup.py, package.json, etc.)  

```bash
same-version --fail-for-missing-file "true" --check-package-json "false" --check-codemeta-json "false" --check-setup-py "false" --check-zenodo-json "false"
```

You can integrate this into:

✅ Local release scripts  
✅ CI pipelines (non-GitHub)  
✅ Manual checks

---

## 🤝 Contributing

Pull requests and contributions are welcome!

To set up your development environment:

```bash
git clone https://github.com/willynilly/same-version.git
cd same-version
pip install -e .[testing,dev]
pre-commit install -t pre-commit -t pre-push
pre-commit run --all-files
```

---

## 🔍 Comparisons with similar tools

| Tool / Action | Scope / Limitations |
|---------------|--------------------|
| [`check-version`](https://github.com/marketplace/actions/check-version) | Compares one or two files (e.g. `package.json` or `pyproject.toml`) against Git tag; no cross-file or multi-ecosystem checks |
| [`validate-version-tag-action`](https://github.com/marketplace/actions/validate-version-tag-action) | Focused on NPM (`package.json` only); no support for Python, metadata standards, or multi-file consistency |
| [`python-semantic-release`](https://python-semantic-release.readthedocs.io/) | Automated release tool (version bumping, changelogs); not designed for cross-file or cross-language version consistency |
| `check-tag-version` (various community actions) | Typically limited to checking one file type; lacks support for multiple ecosystems and scientific metadata standards |

✅ **`same-version` is currently the only GitHub Action that provides:**

- Ultra-conservative version normalization using **Verple** (strict, cross-standard comparison)
- Cross-ecosystem version consistency checks, including:
    - Python (`pyproject.toml`, `setup.py`, `__version__`)
    - JavaScript (`package.json`)
    - Scientific metadata (`CITATION.cff`, `codemeta.json`, `.zenodo.json`, `ro-crate-metadata.json`)
    - Other languages (`composer.json`, `Cargo.toml`, `pom.xml`, `.nuspec`, `DESCRIPTION`)
- Strict equality across files using full version fields: release, pre-release, post-release, dev-release, and local identifiers
- Lightweight, pure Python implementation — fully offline, no third-party services
- Flexible use in GitHub Actions, pre-commit hooks, or standalone CLI

---

## 📜 License

Apache License 2.0 — free to use, fork, extend 🚀

---

## 🙏 Acknowledgements

Inspired by best practices for reproducible research and software citation!

---
