#!/usr/bin/env python3
"""Cria problemas controlados no OpenShift."""
import sys
sys.path.insert(0, ".")
from scripts.troublemaker import main as tm
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: create.py <crash|oom|security|broken-svc> [namespace]")
        sys.exit(1)
    exec(open(__file__.replace('create.py', 'troublemaker.py')).read().replace('sys.argv[1]', f'"{sys.argv[1]}"').replace('print(resp.text)', 'json.dumps(resp.json(), indent=2)'))
