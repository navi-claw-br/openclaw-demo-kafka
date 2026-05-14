#!/usr/bin/env python3
"""Troublemaker CLI - Create/cleanup problems in OpenShift"""
import requests, sys, json

BASE_URL = "https://agent-system-kafka.apps.bbdw.sandbox3066.opentlc.com"

ACTIONS = {
    "crash": "Create CrashLoopBackOff pod",
    "oom": "Create OOM-risk pod",
    "broken-svc": "Create misconfigured service",
    "security": "Create privileged security pod",
    "cleanup": "Remove all created problems",
    "problems": "List active problems",
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print("Usage: python3 troublemaker.py <action>")
        print(f"Actions: {', '.join(ACTIONS.keys())}")
        for k, v in ACTIONS.items():
            print(f"  {k}: {v}")
        sys.exit(1)
    
    action = sys.argv[1]
    ns = sys.argv[2] if len(sys.argv) > 2 else "default"
    
    resp = requests.post(f"{BASE_URL}/{action}", data=f"namespace={ns}", timeout=15, verify=False)
    print(resp.text)

if __name__ == "__main__":
    main()
