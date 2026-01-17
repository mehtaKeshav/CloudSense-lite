import os
import csv
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
    
    directory = "./temp/"
    file_path = f"{directory}/{file.filename}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open (file_path, "wb") as buffer:
        buffer.write(file.file.read())

    df = pd.read_csv(file_path)

    service_Cost = df.iloc[0].to_dict()
    
    return {
        "message": f"File received successfully {file.filename}",
        "file_path": file_path,
        "file_size": os.path.getsize(file_path),
        "content_type": file.content_type,
        "service_Cost": service_Cost
    }