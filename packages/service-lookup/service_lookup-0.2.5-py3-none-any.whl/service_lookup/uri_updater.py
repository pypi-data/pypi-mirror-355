"""Updates URI properties found in YAML files under the given root"""

import re
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

def replace_host_port(url, new_host_port):
    """Replace only the host:port part in a URL, keeping the rest."""
    return re.sub(r"(http://)([^/]+)", rf"\1{new_host_port}", url)

def update_yaml_urls_by_key(file_path, replacements):
    """Update URI properties by service name"""
    with open(file_path, 'r', encoding="utf-8") as f:
        data = yaml.load(f)

    if not isinstance(data, dict):
        return

    updated = False

    def recurse_dict(d):
        nonlocal updated

        if not isinstance(d, dict):
            return

        for key, value in d.items():
            if isinstance(value, dict):
                for service, new_host_port in replacements.items():
                    if key == service and "url" in value and isinstance(value["url"], str):
                        old_url = value["url"]
                        new_url = replace_host_port(old_url, new_host_port)
                        if old_url != new_url:
                            value["url"] = new_url
                            updated = True
            recurse_dict(value)

    recurse_dict(data)

    if updated:
        with open(file_path, 'w', encoding="utf-8") as f:
            yaml.dump(data, f)
        print(f"✅ Updated: {file_path}")

def update_directory(root_path: Path, replacements: dict[str, str], exclude_paths: list[str]):
    """Updates URI properties in YAML files under the root path"""

    exclude_paths = [Path(exclude).resolve() for exclude in exclude_paths]

    for file in root_path.rglob("*.yml"):
        if any(file.resolve().is_relative_to(exclude) for exclude in exclude_paths):
            print(f"❌ Skipped: {file} (excluded)")
            continue

        if update_yaml_urls_by_key(file, replacements):
            print(f"✅ Updated: {file}")
    print()
