from dotenv import load_dotenv
import os

# Automatically load the .env file when the package is imported
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)


from .all_files_ import *
from .mini_utils import *
from .seed_file import *
from .data_path_settings import * 

