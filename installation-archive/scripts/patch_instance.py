"""Patch Autolume's visualizer.py for multi-instance operation.

Replaces the hardcoded NDI name and OSC ports so multiple instances
can run simultaneously with unique identities.

Usage:
    python patch_instance.py <visualizer_path> <ndi_name> <osc_in_port> <osc_out_port>

Example:
    python patch_instance.py autolume-fish/modules/visualizer.py Autolume-Fish 1338 1337
"""

import re
import sys
from pathlib import Path


def patch(visualizer_path: str, ndi_name: str, osc_in_port: int, osc_out_port: int):
    p = Path(visualizer_path)
    text = p.read_text()

    # Patch NDI name
    text = re.sub(
        r"self\.ndi_name\s*=\s*['\"].*?['\"]",
        f"self.ndi_name = '{ndi_name}'",
        text,
    )

    # Patch OSC ports
    text = re.sub(
        r"self\.in_port\s*=\s*\d+",
        f"self.in_port = {osc_in_port}",
        text,
    )
    text = re.sub(
        r"self\.out_port\s*=\s*\d+",
        f"self.out_port = {osc_out_port}",
        text,
    )

    p.write_text(text)
    print(f"Patched {p}: NDI={ndi_name}, OSC in={osc_in_port}, out={osc_out_port}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    patch(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
