""" Generates a [name, kubeconfig] map from Lens kubeconfigs. """

from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

def get_kubeconfigs():
    """Generates a map from namespace or cluster name to kubeconfig file path."""
    lens_kubeconfigs_dir = Path.home() / "AppData" / "Roaming" / "Lens" / "kubeconfigs"

    if not lens_kubeconfigs_dir.exists():
        print("Lens kubeconfigs directory not found. Ensure Lens is installed and configured.")
        return None

    kubeconfig_files = list(lens_kubeconfigs_dir.glob('*'))
    if not kubeconfig_files:
        print("No kubeconfig files found in the Lens directory.")
        return None

    namespace_to_kubeconfig = {}

    for kubeconfig_file in kubeconfig_files:
        try:
            with open(kubeconfig_file, 'r', encoding="utf-8") as f:
                kubeconfig_data = yaml.load(f)

            for context in kubeconfig_data.get('contexts', []):
                namespace = context.get('context', {}).get('namespace')
                cluster = context.get('context', {}).get('cluster')
                if namespace:
                    namespace_to_kubeconfig[namespace] = str(kubeconfig_file)
                elif cluster:
                    namespace_to_kubeconfig[cluster] = str(kubeconfig_file)
        except OSError as e:
            print(f"Error reading {kubeconfig_file}: {e}")

    return namespace_to_kubeconfig
