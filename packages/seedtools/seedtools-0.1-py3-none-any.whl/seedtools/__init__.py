from dotenv import load_dotenv
import os

# Automatically load the .env file when the package is imported
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)


from .all_files_ import show_all_datasets,count_files,get_all_exts
from .mini_utils import (
    display_recursive,display_Seed_file,
    read_json,write_json,
    read_seed,write_seed,read_seed_extended,
    get_ext,get_name,connect)

from .seed_file import check_data,check_data_mini,register_csv,load_seed

