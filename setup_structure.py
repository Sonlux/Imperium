#!/usr/bin/env python3
"""Setup script to create project directory structure"""
import os
import pathlib

# Define directory structure
directories = [
    'src/intent_manager',
    'src/policy_engine',
    'src/enforcement',
    'src/feedback',
    'src/iot_simulator',
    'config',
    'monitoring/prometheus',
    'monitoring/grafana',
    'scripts',
    'tests'
]

# Create all directories
base_path = pathlib.Path(__file__).parent
for directory in directories:
    dir_path = base_path / directory
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {directory}")
    
    # Create __init__.py for Python packages
    if directory.startswith('src/'):
        init_file = dir_path / '__init__.py'
        init_file.write_text('"""Package initialization"""\n')

print("\n✓ Project structure created successfully!")
