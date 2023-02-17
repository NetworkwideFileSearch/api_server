from fastapi import FastAPI
import nmap
import socket

# Find ip address of the current machine
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Initialize nmap with path to binary
s_path = [r'.\Nmap\nmap.exe']
nm = nmap.PortScanner(nmap_search_path=s_path)

# cache all hosts list
nw_hosts = []

# Utitlity functions


def get_all_ips():
    ip = ip_address.split('.')
    ip[-1] = '0'
    ipAddr = '.'.join(ip)
    nm.scan(hosts=f"{ipAddr}/24", arguments='-sn')
    res = {}
    return nm.all_hosts()


app = FastAPI()

# /search - search query for the file name
# /rediscover - again check for devices in the network
# /download - download file from the device


@app.get("/search")
async def search(query: str):
    return {"query": query}


@app.get("/rediscover")
async def rediscover():
    hosts = get_all_ips()
    nw_hosts = hosts
    return {"hosts": hosts}


# Testing below

@app.get("/")
async def root():
    return {"message": "Hello Sourabh"}


@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
