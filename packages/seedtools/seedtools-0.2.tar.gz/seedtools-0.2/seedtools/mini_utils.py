import os ,json
from .data_path_settings import return_data_path
from rich import print as rich_print

DATA_PATH= return_data_path()



def print_u(text):
    rich_print(f"[underline]{text}[/underline]")


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



def dropper(df,cols,status="speak"):
    if status !=  "quiet":
        print("Dropping Columns:", cols)
    df = df.drop(columns=cols, errors='ignore')
    return df

def mapper(df,cols_map,status="speak"):
    if status != "quiet":
        print("Mapped Columns:", list(cols_map.keys()))
        
    for (key,maps) in cols_map.items():
        if key in df.columns:
            if maps == "auto":
                maps = {v: k for k, v in enumerate(df[key].unique())}
            df[key] = df[key].map(maps)   
    return df  
        

def connect(filename):
    return os.path.join(DATA_PATH,filename)


def get_name(filename):
    name, ext =  os.path.splitext(filename)
    return name 

def get_Seed_name(filename):
    return f"{get_name(filename)}_seed.json"


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


def read_version_names(filename):
    return read_seed(filename)["version_names"]

def update_seed(filename,new_data):
    data = read_seed(filename)
    data.update(new_data)
    write_json(data, connect(f"{get_name(filename)}_seed.json"))
    print("Seed Updated Successfully")
    return True





def read_seed_extended(filename):
    data = read_seed(filename)
    shape = data["shape"]
    cls =  data["columns"]
    desc =  data["desc"]
    return (shape,cls,desc)

def display_Seed_file(filename):
    (shape,cls,desc) =   read_seed_extended(filename)
    
    print(f"Shape: {shape}")
    print(f"Columns: {cls}")
    print(f"Description: {desc}")
    
    