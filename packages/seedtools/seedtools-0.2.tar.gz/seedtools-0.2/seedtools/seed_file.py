import os
from .mini_utils import *
import pandas as pd
from rich import print as rich_print
from .data_path_settings import return_data_path




DATA_PATH= return_data_path()

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
    
    seed_file_name = get_Seed_name(filename)
    if seed_file_name in os.listdir(DATA_PATH):
        print("- Seed file ✔")
        seed_file= True 
    else:
        print("- Seed File ❌")
    return seed_file


#check seed file status 

def check_data_mini(filename):

    seed_file_name =  get_Seed_name(filename)
    if seed_file_name in os.listdir(DATA_PATH):
        return True 
    else:
        return False 

    
        

# here data is loaded one , cause data might be tsv or encoded utf-8 
# to register csv file 
def register_csv(data,filename,desc=None):
    
    if check_data_mini(filename):
        os.remove(connect(get_Seed_name(filename)))  # removing the old seed file  and creating a fresh one 
        print("found already existing seed file , removed it ")
    
    
    data_seed = {}
    
    desc= desc if desc is not None  else "DATA IS NOT YET PROVIDED"
    
    data_seed["shape"] =  data.shape 
    data_seed["columns"] =  list(data.columns)
    data_seed["desc"] =  desc
    data_seed["version_names"] = []  # new names version will be added here
    
    seed_name  = write_seed(filename,data_seed)
    print(f"Seed `{seed_name}`  Registered Succesfully")
    


class RegisterVersion:
    
    def __init__(self,filename,version_name):
        self.filename = filename
        self.version_name = None
        self.enable_execute =  False
        if self.check_version(filename,version_name):
                self.version_name = version_name
                self.enable_execute =  True
                self.new_data = {}
                self.new_data["version_names"] = read_version_names(self.filename) + [self.version_name]
                self.new_data.setdefault(self.version_name, {})["drop_cols"] = []
                self.new_data.setdefault(self.version_name, {})["map_cols"] = {}
                
        else:
            print(f"Version `{version_name}` already exists or seed file is not registered.")
       
    
    def drop_cols(self,cols_list=[]):
        try :
            if self.version_name is not None:
                self.new_data[self.version_name]["drop_cols"] = cols_list
        except KeyError:
            print("Version name is already registered, please choose a different name.")
            
        
    def map_cols(self,cols_map={}):
        
        try:
            if self.version_name is not None:
                self.new_data[self.version_name]["map_cols"] = cols_map 
        except KeyError:
            print("Version name is already registered, please choose a different name.")
    
    
    def execute(self):
        if self.enable_execute:
            update_status = update_seed(self.filename, self.new_data)
            if update_status:
                print(f"Version `{self.version_name}` registered successfully")
                return True
            else:
                print("Failed to register version.")
                return False
        else:
            print_u("Version registration is not enabled. Please check the version name or seed file status.")
            return False
        
            
    
    def check_version(self,filename,version_name):        
        
        try :
            check_data_mini(filename)
            if version_name not in read_version_names(filename):
                return True
            else:
                print(f"Version `{version_name}` already registered. Please choose a different name.")
                return False
        except FileNotFoundError:
            print("Seed file not found, please register the seed file first.")
            return False
        
        
        
class load_seed:
    def __init__(self,filename,version=None):
        seed_status = check_data(filename)
        self.filename =  filename 
        
        if version in read_version_names(filename) and seed_status:
            self.data =  self.read_data_file(self.filename,version)
            display_Seed_file(filename)
        elif seed_status:
            self.data =  pd.read_csv(connect(self.filename))
            print_u(f"Version Name : {version}  Not Found")
            display_Seed_file(filename)
        else:
            self.data  = pd.read_csv(connect(filename))
            print_u("SEED FILE IS NOT CONFIGURED YET , CONFIGURE IT USING `register` and `register_version`")
        
        
        
        
    def read_data_file(self,filename,version):
        seed_data = read_seed(filename)[version]
        data = pd.read_csv(connect(filename))
        data  = dropper(data,seed_data["drop_cols"])
        data =  mapper(data,seed_data["map_cols"])
        return data
    
    

    def versions_list(self):
        versions = read_version_names(self.filename)
        return f"AvAILABLE VERSIONS : {versions}"
    
    def seed_file(self):
        return read_seed(self.filename)
    
    def terminate_version(self,vname):
        
        if vname in read_version_names(self.filename):
            seed_data = read_seed(self.filename)
            del seed_data[vname]
            seed_data["version_names"] =  [i for i in seed_data["version_names"] if i !=  vname]
            write_seed(self.filename,seed_data)
            return f"{vname} terminated "
    
    def register(self,desc=None):
        register_csv(self.data,self.filename,desc)
    
    
    def register_version(self,version,drop_cols=[],cols_maps={}):
        v =  RegisterVersion(self.filename,version)
        if drop_cols != []:
            v.drop_cols(drop_cols)
        if cols_maps != {}:
            v.map_cols(cols_maps)
            
        print_u("`v.execute()` it after checking new data")
        
        return v



             
        
            
            
    
    
    

    
    
