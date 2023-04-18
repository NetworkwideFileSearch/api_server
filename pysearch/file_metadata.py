

import os
import time
import re
from functools import lru_cache
import json
from .common_methods import load_field_from_json,global_info_path



class FileManager:
    """
    This class provides functionality to get metadata of all files and folders in a given directory.
    """
    def __init__(self, path):
        """
        Constructor to initialize the class with the path to the directory to fetch metadata from.

        Parameters:
        path (str): The path to the directory to fetch metadata from.
        """
        self.path = path
        self.ignore_regex_pattern = FileManager.compile_regex(global_info_path)
        self.metadata_list = []


    @staticmethod
    def compile_regex(path):
        ignore_file_types = load_field_from_json(path)
        pattern = '|'.join(ignore_file_types)
        regex = re.compile(pattern)
        return regex
    
     
    def is_ignore_file(self,file_name):
        match =  self.ignore_regex_pattern.search(file_name)
        return bool(match)

    def get_metadata(self, file_path):
        """
        Returns the metadata of the given file/folder.

        Parameters:
        file_path (str): The path to the file/folder to get metadata for.

        Returns:
        tuple: A tuple containing the metadata of the file/folder in the following order:
        (name, type, size, accessed_time, modified_time, created_time, path)
        """

        name = os.path.basename(file_path)
        if os.path.isdir(file_path):
            type = 'folder'
            size = sum(os.path.getsize(os.path.join(root, f)) for root, dirs, files in os.walk(file_path) for f in files)
        else:
            type = os.path.splitext(name)[1].replace('.', '')
            size = os.path.getsize(file_path)

        # accessed_time = time.ctime(os.path.getatime(file_path))
        # # modified_time = time.ctime(os.path.getmtime(file_path))
        created_time = time.ctime(os.path.getctime(file_path))

        return (name, type, size,  created_time, file_path)

    def get_metadata_recursive(self, path):
        """
        Recursively gets metadata for all files and folders in the given path and appends it to the metadata_list.

        Parameters:
        path (str): The path to the directory to fetch metadata from.
        """
        if os.access(path, os.R_OK):
            for entry in os.scandir(path):
                if self.is_ignore_file(entry.name):
                    print(entry.name)
                    pass
                else: 
                    metadata = self.get_metadata(entry.path)
                    # yield metadata
                    self.metadata_list.append(metadata)

                    if entry.is_dir():
                        self.get_metadata_recursive(entry.path)



def get_all_metadata(folder_path = r'D:\js calculator'):
    """
    Gets metadata for all files and folders in the specified directory.

    Returns:
    list: A list containing metadata of all files and folders in the specified directory.
    """
    
    file_manager = FileManager(folder_path)
    file_manager.get_metadata_recursive( folder_path)
    return file_manager.metadata_list


if __name__ == '__main__':
    path = r'D:\pendrive\filesearch2.0'
    obj = get_all_metadata(path)
    for i in obj:
        print(i,"\n")

     