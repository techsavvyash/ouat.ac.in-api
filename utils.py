import requests
from bs4 import BeautifulSoup
import json
import requests
import tempfile
import os
import shutil
import logging

def download_pdf(url, temp_dir):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".pdf")
            with open(temp_file.name, 'wb') as f:
                f.write(response.content)
            return temp_file.name
        else:
            logging.error(f"Failed to download PDF from {url}")
            return None
    except Exception as e:
        logging.error(f"Error downloading PDF: {e}")
        return None


def scraper():
    url = 'https://ouat.ac.in/quick-links/agro-advisory-services/'
    rename_districts = {
        'angul': 'anugul',
        'balasore': 'baleshwar',
        'boudh': 'baudh',
        'deogarh': 'debagarh',
        'keonjhar': 'kendujhar',
        'mayurbhanjha': 'mayurbhanj',
        'nabarangpur': 'nabarangapur',
        'sonepur': 'subarnapur'
    }    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        data = []
        districts = soup.find_all('div', class_='hide1')
        for district in districts:
            district_name = district.get('id')[:-1]
            if district_name in rename_districts.keys():
                district_name=rename_districts[district_name]
            data_dict = {'district_name': district_name}
            table = district.find('table').find('tbody')
            if len(table.select('tr')) > 0:
                rows = table.select('tr')[0]
            else:
                continue
            columns = rows.find_all('td')
            date = columns[1].text.strip()
            data_dict['date'] = date
            english_link = columns[2].find('a')['href']
            odia_link = columns[3].find('a')['href']
            link_dict = {'english': english_link, 'odia': odia_link}
            data_dict['link'] = link_dict
            data.append(data_dict)

        return data

    except Exception as e:
        logging.error(f"Error scraping website: {e}")
        return []
    

def move_json_to_history(source_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(source_dir, exist_ok=True)

    for filename in os.listdir(source_dir):
        if filename.endswith(".json"):
            source_path = os.path.join(source_dir, filename)
            with open(source_path, 'r') as json_file:
                data = json.load(json_file)
                date = data.get('date')
                district_name = filename.split('.')[0]
                history_filename = f"{date}_{district_name}.json"
                dest_path = os.path.join(dest_dir, history_filename)
                shutil.move(source_path, dest_path)
                print(f"Moved {filename} to {dest_path}")