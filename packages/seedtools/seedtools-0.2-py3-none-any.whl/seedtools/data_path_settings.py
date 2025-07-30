import os 
from dotenv import load_dotenv



load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


def return_data_path():
    return os.getenv("DATA_PATH")