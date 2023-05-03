from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
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
from pysearch.faiss_index import faiss_index
 



import uvicorn
from dataclasses import dataclass
from typing import List

import concurrent.futures
import requests

from scapy.all import ARP, Ether, srp


def scan_network(ip, mask):
    # Generate the network CIDR notation from the IP address and subnet mask
    cidr = ip + '/' + mask

    # Create an ARP request packet to send to the network
    arp_request = ARP(pdst=cidr)

    # Create an Ether packet to encapsulate the ARP request
    ether_request = Ether(dst='ff:ff:ff:ff:ff:ff')

    # Combine the ARP request and Ether packet into a single packet
    packet = ether_request/arp_request

    # Use the srp function in scapy to send and receive packets on the network
    result = srp(packet, timeout=3, verbose=False)[0]

    # Extract the IP and MAC addresses from the responses
    active_ips = set()
    for sent, received in result:
        active_ips.add(received.psrc)

    return active_ips


Base.metadata.create_all(bind=engine)

# Find ip address of the current machine
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Initialize nmap with path to binary
s_path = [r'.\Nmap\nmap.exe']
# nm = nmap.PortScanner(nmap_search_path=s_path)

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
    # ip = ip_address.split('.')
    # ip[-1] = '0'
    # ipAddr = '.'.join(ip)
    # nm.scan(hosts=f"{ipAddr}/24", arguments='-sn')
    # res = {}
    # hostNames = []
    # for host in nm.all_hosts():
    #     info = {'ip':host}
    #     if 'hostnames' in nm[host]:
    #         info['hostnames'] = nm[host]['hostnames'][0]['name']
    #     else:
    #         info['hostnames'] = 'Unknown'
    #     hostNames.append(info)
    # return hostNames
    # hosts = scan_network(ip_address, "24")
    # return hosts
    return []


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
    index_obj : object = None


essentials = ObjClass()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /search - search query for the file name
# /rediscover - again check for devices in the network

def vectorize_whole_index():
    
    encoding_func = essentials.model_obj.encode_from_official_doc_by_HF
    rows = essentials.db_obj.get_file_metadata_for_vectorization()
    # print(rows[0])
    for row in rows:
        content = make_file_content(row[1:])
        vector = encoding_func(content)
        essentials.index_obj.add_single_vector(vector=vector,id = row[0])
     
    return {"message": "entire table is vectorized and stored in table"}


def search(query ):
    query_vec = essentials.model_obj.encode_from_official_doc_by_HF(query)
    res = essentials.index_obj.search_top_k(query_vector=query_vec,k = 10,do_normalize=1)
    output = essentials.index_obj.convert_to_dict(distances= res[0],ids=res[1])
    print(output)
    return output

def add_to_index(id,encoding_func):
    try:
        rows = essentials.db_obj.fetch_metadata_of_specific_ids(
            file_ids=[id], table_name="files")
        for row in rows:
            content = make_file_content(row[1:])
            vector = encoding_func(content)
            essentials.index_obj.add_single_vector(vector=vector,id = row[0])
        return "success"
    except:
        return ""

def delete_in_index(id):
    op = essentials.index_obj.remove_data(id_list=[id])
    return op


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
        essentials.index_obj = faiss_index(dim = 384,index_name="test_index")
        vectorize_whole_index()
        return "Objects loaded successfully."
    except:
        return "Failed to load objects."


@app.get("/search/{query}")
async def search_func(query: str, db: Session = Depends(get_db)):
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
    top_k_dict =  search(query=query)
    # the top_k variable is already sorted and of format list of dictionaries

    lis = list(top_k_dict.keys())

    files = db.query(File).filter(File.id.in_(lis)).all()
    files.sort(key=lambda row: lis.index(row.id))
    print(files)

    api_output_dict = {}

    mod_files = []

    for file in files:
        file_dict = file.__dict__
        file_dict["score"] = top_k_dict[file.id]
        mod_files.append(file_dict)

    api_output_dict[ip_address] = mod_files
    print(api_output_dict)

    # Define a function to make the API call and store the output in the dictionary
    def make_api_call(ip):
        # Replace "api" with the actual API endpoint
        url = f"http://{ip}:6969/fwd_search/{query}"
        print("url", url)
        try:
            response = requests.get(url)
            api_output_dict[ip] = response.json()
        except:
            api_output_dict[ip] = []

    # Use a ThreadPoolExecutor to make API calls in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit each API call to the executor
        print(nw_hosts)
        futures = [executor.submit(make_api_call, ip) for ip in nw_hosts]

        # Wait for all API calls to complete
        concurrent.futures.wait(futures)

    # Return the API output dictionary
    return api_output_dict


@app.get("/fwd_search/{query}")
async def search_func(query: str, db: Session = Depends(get_db)):
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
    top_k_dict =  search(query=query)
    # the top_k variable is already sorted and of format list of dictionaries

    lis = list(top_k_dict.keys())

    files = db.query(File).filter(File.id.in_(lis)).all()
    files.sort(key=lambda row: lis.index(row.id))

    mod_files = []

    for file in files:
        file_dict = file.__dict__
        file_dict["score"] = top_k_dict[file.id]
        mod_files.append(file_dict)

    return mod_files


@app.get("/delete/{id}")
def delete_row(id:int):   
    op =  delete_in_index(id=id)
    if op:
        return {'message': f"file data with file_id : {id} deleted successfully"}
    else:
        return {"message": f"file data  deletion unsuccessful"}


@app.get("/add_vector/{id}")
async def add_vector(id: int):
    op = add_to_index(id = id,encoding_func = essentials.model_obj.encode_from_official_doc_by_HF)
    
    if op:
        return {'message': f"file data and vectors with file_ids : {id} added successfully"}
    else:
        return {"message": f"file data and vector addition unsuccessful"}


@app.get("/rediscover")
async def rediscover():
    hosts = get_all_ips()
    hostnames = []

    nw_hosts.clear()
    for host in hosts:
        if host['ip'] != ip_address:
            nw_hosts.append(host['ip'])
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
