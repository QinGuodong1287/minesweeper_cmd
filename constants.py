import os

__version__ = "v1.0.2, Build 2023/5/17"
program_path = os.path.dirname(__file__)
error_file = os.path.join(program_path, r"error.log")
records_file = os.path.join(program_path, r"records.json")
map_file = os.path.join(program_path, r"map.json")
settings_file = os.path.join(program_path, r"settings.json")
