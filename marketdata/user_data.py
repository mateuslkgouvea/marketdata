import os
import json

PATH = os.environ['MD_DATA_PATH']
FILE_NAME = 'records.json'
RECORDS_PATH = f'{PATH}/{FILE_NAME}'

template = {
    "nameofuser": {
        "username": "nameofuser",
        "hashed_password": None,
        "disabled": True,
    } 
}

if not os.path.exists(RECORDS_PATH):
    with open(RECORDS_PATH, "w") as file:
        json.dump(template, file)

with open(RECORDS_PATH, 'r') as file:
    records = json.load(file)


