import os
import csv
from parser import analizeData
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/file-upload/")
async def upload_file(file: UploadFile):
    if not file:
        raise HTTPException(
            status_code=400,
            detail="No files found in the request"
            )
    if file.content_type not in ["text/csv", "application/vnd.ms-excel", "application/octet-stream"]:
         raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
            )
    
    file_path, service_Cost = analizeData(file)
    
    return {
        "message": f"File received successfully {file.filename}",
        "file_path": file_path,
        "file_size": os.path.getsize(file_path),
        "content_type": file.content_type,
        "service_Cost": service_Cost
    }