#!/usr/bin/env python3
"""
Test script to check Flask routes
"""
from app import app

if __name__ == '__main__':
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    
    print(f"\nApp running on: {app.config.get('SERVER_NAME', 'default')}")
    print(f"Debug mode: {app.debug}")
