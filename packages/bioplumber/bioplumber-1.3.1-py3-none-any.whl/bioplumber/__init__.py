import sys
import os
import json
import pathlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

__version__ = '0.1.0'

def get_config():
    """Get the current configuration."""
    with open(os.path.join(os.path.dirname(__file__), 'configs.json'), 'r') as f:
        config = json.load(f)
    return config

config=get_config()
if not pathlib.Path(config.get('base_directory')):
    config['base_directory'] = ""

    
def set_base_directory(path):
    """Set the base directory for the application."""
    with open(os.path.join(os.path.dirname(__file__), 'configs.json'), 'r') as f:
        config = json.load(f)
    config['base_directory'] = path
    with open(os.path.join(os.path.dirname(__file__), 'configs.json'), 'w') as f:
        json.dump(config, f, indent=4)

