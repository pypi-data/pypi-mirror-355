import os 
from dotenv import load_dotenv
from .mini_utils import display_recursive, connect,read_seed_extended,get_ext
from .seed_file import check_data_mini


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DATA_PATH= os.getenv("DATA_PATH")






# wise is only for csv , "shape","columns","cls","desc"
def show_all_datasets(type="csv",show=True,wise="shape"):
    #types  = "csv" ,"dir","all"
    
    dirs =  os.listdir(DATA_PATH)
    datasets = []
    
    for obj in dirs :
        
        if get_ext(obj)[1:] in ["csv","tsv"] and type == "csv":
            
            seed_status =  "✔" if check_data_mini(obj) else "❌"
            
            if check_data_mini(obj) == True :
                (shape,cls,desc) =  read_seed_extended(obj)
                item_data  =  {"shape":shape,"columns":cls,"cls":cls,"desc":desc}
                item_data["seed"] =  seed_status
                obj_item = f''' {obj} -: {item_data[wise]}'''
            else:
                item_data  =  {"shape":shape,"columns":cls,"cls":cls,"desc":desc}
                item_data[wise] = "SEED X"
                item_data["seed"] =  seed_status
                obj_item = f''' {obj} -: {item_data[wise]}'''
            
            
            datasets.append(obj_item)
        
        if os.path.isdir(connect(obj))  and type=="dir":
            datasets.append(obj)
        
        if type=="all":
            datasets.append(obj)
    
    if show == True :
        display_recursive(datasets)
    else:
        return datasets
    

def get_all_exts():
    all_files =  os.listdir(DATA_PATH)
    file_Exts = []
    
    for obj in all_files:
        _,ext =  os.path.splitext(obj)
        ext =  ".folder" if ext == '' else ext 
        file_Exts.append(ext)
    
    return list(set(file_Exts))

    
def count_files():
    get_exts = get_all_exts()
    ext_count = {}
    
    for i  in get_exts:
        ext_count[f"{i[1:]}"] = 0    # setting all ext count  = 0
    
    for obj in os.listdir(DATA_PATH):
        _,ext =  os.path.splitext(obj)
        ext =  ".folder"  if ext == '' else ext 
        if ext in get_exts :
            ext_count[ext[1:]] +=1  # checking and counting 
    
    for obj_key,obj_count in ext_count.items():
        print(f"{obj_key} -  {obj_count}")  # displaying 
        
