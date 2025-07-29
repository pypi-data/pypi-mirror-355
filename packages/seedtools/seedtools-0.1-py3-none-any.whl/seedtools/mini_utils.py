import os ,json
from dotenv import load_dotenv
from rich import print as rich_print


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
DATA_PATH= os.getenv("DATA_PATH")




def read_json(file_path):
    """Read a JSON file and return its content."""
    with open(file_path, 'r') as file:
        return json.load(file)
    

def write_json(data, file_path):
    """Write data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def display_recursive(obj):
    
    for i in obj :
 
        if "-:" in i:
            heading  =  f"[underline]{i.split('-:')[0]}[/underline]"
            cont =  i.split("-")[1]
            rich_print(f"{heading} {cont}")
            
        else:
            print(i)

        

def connect(filename):
    return os.path.join(DATA_PATH,filename)


def get_name(filename):
    name, ext =  os.path.splitext(filename)
    return name 

# def detect_encoding(file_path):
#     encoding = chardet.detect(open(file_path,"rb").read(100000))["encoding"]
#     return encoding


def get_ext(filename):
    name, ext =  os.path.splitext(filename)
    return ext 

def write_seed(filename,data_):
    seed_file_name  =  f"{get_name(filename)}_seed.json"
    write_json(data_,connect(seed_file_name))
    return seed_file_name

def read_seed(filename):
    seed_file_name  =  f"{get_name(filename)}_seed.json"
    data  =  read_json(connect(seed_file_name))
    return data 


def read_seed_extended(filename):
    data = read_seed(filename)
    shape = data["shape"]
    cls =  data["columns"]
    desc =  data["desc"]
    return (shape,cls,desc)

def display_Seed_file(filename):
    data =   read_seed(filename)
    
    for key , value in data.items() :
        print(f"{key} :  {value}")
    