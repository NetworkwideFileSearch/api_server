from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import os
import nmap
import socket
from sqlalchemy.orm import Session

from models import File, Base
from database import SessionLocal, engine

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


app = FastAPI()

# /search - search query for the file name
# /rediscover - again check for devices in the network


@app.get("/search")
async def search(query: str, db: Session = Depends(get_db)):
    files = db.query(File).all()
    return files


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
