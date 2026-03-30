from fastapi import UploadFile
import os
import pandas as pd
import re

def analizeData(file: UploadFile) -> tuple[str, dict]:
    directory = "./temp/"
    file_path = f"{directory}/temp.csv"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open (file_path, "wb") as buffer:
        buffer.write(file.file.read())
    

    report = pd.read_csv(file_path)

    row = report.iloc[0].to_dict()

    row.pop('Service', None)

    total_key = ""

    for k in row.keys():
        if re.match(r'[Pp]otal', k):
            total_key = k
            break
    
    total_cost = float(row.pop(total_key)) if total_key and row.get(total_key) is not None else None

    service_cost = {}
    for k, v in row.items():
        if v is None:
            continue
        service_name = str(k).strip()
        service_name = service_name.replace("($)","")
        
        try:
            cost_val = float(v)
        except Exception:
            continue
        service_cost[service_name] = cost_val
        
        if total_cost is None:
            total_cost = sum(service_cost.values())
        
    
    
