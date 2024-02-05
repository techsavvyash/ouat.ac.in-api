# ouat.ac.in-api
Server for ouat.ac.in Agri Advisory Services

## Description
This is a service to provide the the agro advisory data provided by OUAT. One can use the environment and run the python script to gather all the data in provided folder. Steps to follow:
1. Run the script and required JSON data will be stored.
2. The data can be accessed statically through github pages deployment.

### Format of data
JSON files will be stored in following folder and naming conventions once scrapped.

Districtwise complete data: 
```
root/history/{date}_{district}.json
```
Latest data for each district: 
```
root/latest/{district}.json
```

## Setting up a virtual env
```
python3 -m venv venv
source venv/bin/activate
```

## Environment Setup
Setup an OpenAI API key in the environment variables or in a .env file.
```
OPENAI_API_KEY = 'sk-XXXXXXXXX'
```

## Installing dependencies
Run the following to install the required libraries.
```
pip install -r requirements.txt
```

## Running the script
Run the script contained in main.py
```
python3 main.py
```