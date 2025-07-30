"""Kills processes based on ther listening port"""

import subprocess
import os
import signal

def get_pids_for_ports(ports):
    """Retrieve PIDs for processes listening on specified ports."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=True
        )
        # Find lines that mention the specified ports
        pids = set()
        for line in result.stdout.splitlines():
            if any(f":{port}" in line for port in ports):
                # Extract the PID, which is usually the last column
                parts = line.split()
                pid = parts[-1]
                pids.add(pid)

        return pids
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving netstat information: {e.stderr}")
        return set()

def kill_process(pid):
    """Attempt to kill a process by PID."""
    try:
        os.kill(int(pid), signal.SIGTERM)
        print(f"✅ Process {pid} terminated.")
    except OSError as e:
        print(f"❌ Failed to terminate process {pid}: {e}")

def clean_ports(ports):
    """Clean processes associated with specified ports."""
    pids = get_pids_for_ports(ports)
    if not pids:
        print("No processes found for the specified ports.")
        return

    for pid in pids:
        kill_process(pid)
