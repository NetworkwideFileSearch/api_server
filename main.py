from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import os
import nmap
import socket
from sqlalchemy.orm import Session

from models import File, Base
from database import SessionLocal, engine

from pysearch.new_sql import embeddings_table
from pysearch.work_with_model import transformer_ops
from pysearch.playground import search_ops, jaccard_sim, cosine_sim
from pysearch.common_methods import *

import uvicorn
from dataclasses import dataclass
from typing import List

Base.metadata.create_all(bind=engine)

# Find ip address of the current machine
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Initialize nmap with path to binary
s_path = [r'.\Nmap\nmap.exe']
nm = nmap.PortScanner(nmap_search_path=s_path)

# cache all hosts list
nw_hosts = []

# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utitlity functions


def get_all_ips():
    ip = ip_address.split('.')
    ip[-1] = '0'
    ipAddr = '.'.join(ip)
    nm.scan(hosts=f"{ipAddr}/24", arguments='-sn')
    res = {}
    return nm.all_hosts()


@dataclass
class ObjClass:
    """
    A class to store essential objects used for search operations.

    Attributes:
    -----------
    model_obj: object
        An object of the transformer_ops class.
    db_obj: object
        An object of the dbclient class.
    search_obj: object
        An object of the search_ops class.
    """
    model_obj: object = None
    db_obj: object = None
    search_obj: object = None


essentials = ObjClass()


app = FastAPI()

# /search - search query for the file name
# /rediscover - again check for devices in the network


def vectorize_whole_table():
    essentials.db_obj.create_embeddings_table()
    rows = essentials.db_obj.get_file_metadata_for_vectorization()
    # print(rows[0])
    data = [i for i in essentials.db_obj.get_id_vector_pairs_to_add_in_table(
        rows=rows, encoding_func=essentials.model_obj.encode_from_official_doc_by_HF)]
    # print(data[0])
    essentials.db_obj.add_multiple_vectors(data=data, table_name="embeddings")
    return {"message": "entire table is vectorized and stored in table"}


@app.on_event("startup")
async def startup_event():
    """
    Load essential objects when the application starts.

    Returns:
    --------
    str
        A message indicating whether the objects were loaded successfully or not.
    """
    try:
        essentials.model_obj = transformer_ops(
            "sentence-transformers@multi-qa-MiniLM-L6-cos-v1")
        essentials.model_obj.load_model_pickle()
        essentials.db_obj = embeddings_table("sample.db")
        essentials.search_obj = search_ops(k=5)
        vectorize_whole_table()
        return "Objects loaded successfully."
    except:
        return "Failed to load objects."


@app.get("/search/{query}")
async def search_func(query: str):
    """
    Perform a search operation based on the given query.

    Parameters:
    -----------
    query: str
        The query string to search for.

    Returns:
    --------
    list
        A list of file ids in decreasing order of relevance
    """
    res = essentials.search_obj.get_top_k_docs(query,
                                               fetch_func=essentials.db_obj.fetch_id_and_vector,
                                               k=10,
                                               similarity_func=cosine_sim,
                                               encoding_func=essentials.model_obj.encode_from_official_doc_by_HF)
    lis = list(next(res))
    # res = essentials.db_obj.keyword_search(
    #     query, table_name="files", column_name="filename")
    return lis


@app.get("/delete/{file_id}")
def delete_row(file_id: int):
    op = essentials.db_obj.delete_vector(
        file_id=int(file_id), table_name="files")
    if not op:
        return {'message': f"file data with file_id : {file_id} deleted successfully"}
    else:
        return {"message": f"file data with file_id: {file_id} deletion unsuccessful"}


@app.get("/add_vector/{id_list}")
async def add_vector(id_list: int):
    rows = essentials.db_obj.fetch_metadata_of_specific_ids(
        file_ids=[id_list], table_name="files")

    data = essentials.db_obj.get_id_vector_pairs_to_add_in_table(
        rows=rows, encoding_func=essentials.model_obj.encode_from_official_doc_by_HF)

    essentials.db_obj.add_multiple_vectors(data=data, table_name="embeddings")


@app.get("/rediscover")
async def rediscover():
    hosts = get_all_ips()
    nw_hosts = hosts
    return {"hosts": hosts}


@app.get("/file")
async def read_file(location: str):
    filename = os.path.basename(location)
    file_path = os.path.abspath(location)
    file_like = open(file_path, mode="rb")
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return StreamingResponse(file_like, headers=headers, media_type="application/octet-stream")


# Testing below

@app.get("/")
async def root():
    return {"message": "Hello Sourabh"}


@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
