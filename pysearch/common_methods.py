import os
import pickle
import json
from functools import lru_cache

## global variables
pyfolder = os.path.dirname( os.path.abspath(__file__))
parent_dir =  os.path.dirname(pyfolder)
global_info_path = os.path.join(parent_dir,"global_info.json")


def save_pickle_obj(obj,path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)

@lru_cache
def load_pickle_obj(path):
    with open( path, 'rb') as f:
        return  pickle.load(f)
    
@lru_cache
def load_json_file(path = global_info_path):
    with open(path, 'r') as f:
        return json.load(f)


def load_field_from_json(path = global_info_path ,field= "ignore_file_types"):
    content = load_json_file(path)
    return content[field]


def make_file_content(row):
    """ the row has following metadata about file : (as per order)
    row is a tuple and it will look like this
    (name, type, size,  created_time,accessed_time, modified_time, file_path)
    we will use this info to develop a paragraph describing about a file 
    we are doing this becoz we want to encode that content into vectorspace

    Generate file content for the given row of metadata.
    """
    file_path, is_directory, file_type, created_time,file_name,size = row
    
    # Generate a human-readable size string
    if size < 1024:
        size_str = str(size) + " bytes"
    elif size < 1048576:
        size_str = str(round(size / 1024, 2)) + " KB"
    else:
        size_str = str(round(size / 1048576, 2)) + " MB"
        
    is_folder = "folder" if is_directory else "file"
    
    # Generate the file content string
    content = f"{is_folder} named {file_name} type of {is_folder} {file_type}  with a size of {size_str}. " \
            f"created on {created_time} " \
            f"{is_folder} location {file_path}."       

    return content





       


if __name__ == "__main__":
    # row = ("mk.py","pdf",230,"Tue Mar  7 10:01:25 2023","Tue Mar  7 10:01:25 2023","Wed Oct 21 22:55:37 2020",r"C:\Users\shree\OneDrive\Documents\21142_DEL_Comparator_expt.no. 05.pdf")
    # print(make_file_content(row))
    print(parent_dir)

     