import os 
from dotenv import load_dotenv
from .mini_utils import connect,get_name,write_seed,display_Seed_file
import pandas as pd




load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
DATA_PATH= os.getenv("DATA_PATH")

# to check data file and seed file
def check_data(filename):
    seed_file =  False 
    data_file = False 
    file_path =  connect(filename)
    
    if filename in os.listdir(DATA_PATH):
        print("- data File ✔")
        data_file =  True
        
    else:
        print("-  data File ❌")
    
    seed_file_name =  f"{get_name(filename)}_seed.json" 
    if seed_file_name in os.listdir(DATA_PATH):
        print("- Seed file ✔")
        seed_file= True 
    else:
        print("- Seed File ❌")
    return seed_file


#check seed file status 

def check_data_mini(filename):
    
    seed_status = False
    
    
    seed_file_name =  f"{get_name(filename)}_seed.json" 
    if seed_file_name in os.listdir(DATA_PATH):
        seed_status = True 
    return seed_status
    
        

# here data is loaded one , cause data might be tsv or encoded utf-8 
# to register csv file 
def register_csv(data,filename,desc=None):
    
    data_seed = {}
    
    desc= desc if desc is not None  else "DATA IS NOT YET PROVIDED"
    
    data_seed["shape"] =  data.shape 
    data_seed["columns"] =  list(data.columns)
    data_seed["desc"] =  desc
    
    seed_name  = write_seed(filename,data_seed)
    print(f"Seed `{seed_name}`  Registered Succesfully")
    


def load_seed(filename):
    seed_status = check_data(filename)
    
    if seed_status == True :
        display_Seed_file(filename)
        
    return connect(filename)

    
    
    

    
    
