"""Looks up services in a Kubernetes cluster, and returns a map with the forwarded local ports"""

import subprocess
import json
import socket
from pathlib import Path
from ruamel.yaml import YAML
from .kubectl_service import KubectlService

yaml = YAML()
yaml.preserve_quotes = True

def get_free_port():
    """Find an available port on the local machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to a free port provided by the host
        return s.getsockname()[1]

def load_service_mappings(mapping_file):
    """Load service mappings from a JSON file."""
    try:
        with open(mapping_file, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Mapping file {mapping_file} not found.")
        return {}
    except json.JSONDecodeError:
        print("Error decoding JSON mapping file.")
        return {}

def get_kubeconfig_for_namespace(namespace, kubeconfigs):
    """Find the kubeconfig file for a given namespace."""

    # Try to find an exact match for the namespace
    if namespace in kubeconfigs:
        print(kubeconfigs[namespace])
        return kubeconfigs[namespace]

    # Try to find a match by splitting on delimiters
    for key in kubeconfigs:
        if namespace in key.split('.') or namespace in key.split('-'):
            return kubeconfigs[key]

    print(f"Error: No matching kubeconfig found for namespace '{namespace}'.")
    print(f"Warning: Using '{kubeconfigs[0]}' as a fallback.")
    return kubeconfigs[0]

def get_context_from_kubeconfig(kubecfg):
    """Extract the context name from a kubeconfig file."""
    try:
        with open(kubecfg, 'r', encoding='utf-8') as f:
            config = yaml.load(f)
            current_context = config.get('current-context')
            if current_context:
                return current_context
            print("No current context found in the kubeconfig.")
            return None
    except OSError as e:
        print(f"Error reading kubeconfig {kubecfg}: {e}")
        return None

def port_forward_services(service_filter, service_mappings, services, namespace, kubectl):
    """Port forward services, return a [service_name, local_port] map and a list of local ports"""

    replacements = {}
    forwarded_ports = []

    for local_name in service_filter:
        k8s_service_name = service_mappings.get(local_name)
        service = next((s for s in services.get("items", [])
            if s["metadata"]["name"] == k8s_service_name), None)

        if service and k8s_service_name:
            ports = service.get("spec", {}).get("ports", [])
            if ports:
                local_port = get_free_port()
                replacements[local_name] = f"localhost:{local_port}"
                target_port = ports[0]["port"]

                kubectl.port_forward(namespace, k8s_service_name, local_port, target_port)
                forwarded_ports.append(local_port)
        else:
            print(f"No mapping found or service '{local_name}' not found in the namespace.")

    print()
    return replacements, forwarded_ports


def discover_services_and_port_forward(namespace, service_filter,
    service_mappings, kubeconfigs=None):

    """Looks up services in a Kubernetes cluster, returns a map with the forwarded local ports."""
    try:
        kubecfg = (
            get_kubeconfig_for_namespace(namespace, kubeconfigs)
            if kubeconfigs else
            Path.home() / ".kube" / "config"
        )

        context_name = get_context_from_kubeconfig(kubecfg)
        if not context_name:
            print("Failed to determine context.")
            return {}

        kubectl = KubectlService(kubecfg)

        kubectl.use_context(context_name)

        services = kubectl.get_services(namespace)

        return port_forward_services(service_filter, service_mappings, services, namespace, kubectl)

    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl: {e.stderr}")
        return {}
