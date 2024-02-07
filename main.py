import asyncio
import aiohttp
import requests
import tempfile
import os
from bs4 import BeautifulSoup
import json
import openai
from dotenv import load_dotenv
import shutil
import time
from aiohttp.client_exceptions import ClientConnectorError

counter=0

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
openai.api_key = api_key

async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.text()

def get_gpt_response(system_prompt, user_prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    gpt_response = response["choices"][0]["message"]["content"]
    return gpt_response

def move_json_to_history(source_dir, dest_dir):
    # Create the history directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(source_dir, exist_ok=True)
    
    # Iterate through all JSON files in the source directory
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

async def download_and_process(session, district, system_prompt, base_api_url, temp_dir):
    global counter
    district_name = district["district_name"]
    info = district.get("link", {})  # Extracting the "link" key instead of "info"
    date=district["date"]
    try:
        tasks = []
        pdf_paths = []
        md_paths = []
        gpt_responses = []

        for language, link in info.items():
            # Focus only on English language links
            if language == "english":
                english_link = link
                print(f"Downloading PDF for {district_name}")
                pdf_path = download_pdf(english_link, temp_dir)
                pdf_paths.append(pdf_path)

                if pdf_path:
                    print(f"Parsing to MD for {district_name}")
                    pdf_id_task = send_to_api(session, pdf_path, base_api_url)
                    tasks.append(pdf_id_task)
        
        # Run all the tasks concurrently
        pdf_ids = await asyncio.gather(*tasks)

        for pdf_id in pdf_ids:
            if pdf_id:
                md_path = await download_md(session, pdf_id, base_api_url, temp_dir)
                md_paths.append(md_path)
                if md_path:
                    with open(md_path, 'r') as md_file:
                        user_prompt = md_file.read()
                    gpt_response = get_gpt_response(system_prompt, user_prompt)
                    gpt_responses.append(gpt_response)

        for gpt_response, pdf_path, md_path in zip(gpt_responses, pdf_paths, md_paths):
            # Handle GPT responses and cleanup
            if gpt_response:
                latest_output_dir = "latest"
                os.makedirs(latest_output_dir, exist_ok=True)
                district_file_name = f"{district_name}.json"
                latest_output_file = os.path.join(latest_output_dir, district_file_name)
                try:
                    json_dict = json.loads(gpt_response)
                except:
                    print(f"error in {district_name}")
                json_dict['date']=date.replace('/','-')
                with open(latest_output_file, 'w') as json_file:
                    json.dump(json_dict, json_file, indent=2)
                print(f"GPT response for {district_name} saved to {latest_output_file}")
                counter+=1
                os.unlink(pdf_path)
                os.unlink(md_path)

    except Exception as e:
            print(f"failed for {district_name}. Error: {e}")
            
                # Clean up the temporary files
            

def check_status_type(pdf_id, base_url):
    url = f"{base_url}/status/?pdf_id={pdf_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        status = data.get("status", {})
        message = status.get("message", {})
        message_type = message.get("type")
        return message_type
    else:
        print(f"Error: Failed to fetch status. Status code: {response.status_code}")
        return None

async def send_to_api(session, pdf_path, base_url):
    api_url = f"{base_url}/process/"
    
    # Create a multipart request
    form = aiohttp.FormData()
    form.add_field('language', 'english')
    form.add_field('to', 'md')
    form.add_field('file', open(pdf_path, 'rb'), filename=os.path.basename(pdf_path))

    async with session.post(api_url, data=form) as response:
        if response.status == 200:
            pdf_id = (await response.json()).get('pdf_id')
            print("PDF processed successfully. PDF ID:", pdf_id)
            return pdf_id
        else:
            print(f"Failed to send PDF to API. Status code: {response.status}")
            return None

async def download_md(session, pdf_id, base_url, temp_dir):
    while check_status_type(base_url=base_url,pdf_id=pdf_id)!='SUCCESS':
        time.sleep(2)

    api_url = f"{base_url}/download/"
    params = {'pdf_id': pdf_id, 'format': 'md'}
    async with session.get(api_url, params=params) as response:
        if response.status == 200:
            md_url = (await response.json()).get('data')[0]['mdURL']
            async with session.get(md_url) as md_response:
                md_content = await md_response.text()
                md_temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".md")
                with open(md_temp_file.name, 'w') as f:
                    f.write(md_content)
                print("Markdown file downloaded successfully.")
                return md_temp_file.name
        else:
            print(f"Failed to download Markdown file. Status code: {response.status}")
            return None

def download_pdf(url, temp_dir):
    response = requests.get(url)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".pdf")
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        return temp_file.name
    else:
        print(f"Failed to download PDF from {url}")
        return None

def scraper():
    url = 'https://ouat.ac.in/quick-links/agro-advisory-services/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    districts = soup.find_all('div', class_='hide1')
    for district in districts:
        district_name = district.get('id')[:-1]
        data_dict = {'district_name': district_name}
        table = district.find('table').find('tbody')
        if len(table.select('tr'))>0:
            rows = table.select('tr')[0]
        else:
            continue
        columns = rows.find_all('td')
        date = columns[1].text.strip()
        data_dict['date']=date
        english_link = columns[2].find('a')['href']
        odia_link = columns[3].find('a')['href']
        link_dict = {'english': english_link, 'odia': odia_link}
        data_dict['link'] = link_dict
        data.append(data_dict)

    return data

async def main():
    system_prompt = '''You are an agent which analyze data in the form of md file content and return only json for the information required.
I will give an md having agro-advisory data. You need to extract these things:
- Key: 'weather'; Value:Extracting table about weather details tagged as 'weather table' 
Note: keep weather table in dict format with keys having individual tupples.
- Key:'general_advice'; value: Extracting general advice about the weather and cropping from the pdf tagged as 'general advice' 
- Key:'name_of_crops'; Value: Name of crops/animal husbandry/poultry/fishing for which further info is present 
- Key:'crops_data'; Value: dictionary having info of extracting the crops/animal husbandry/poultry/fishing details from it and extracting information for each crops/animal husbandry/poultry/fishing from it, each tagged separately for each crop/subgroup (There should be a distinct finite list of these subgroups) (Keys: each crop name, Value: Should be a dict with compulsory key 'advisory')

Note:1. Don't give any triple backticks or newline characters in response. It should be proper json.
2. Name of keys of each crop/animal and all in 'crops_data' should be identical to what is was in 'name_of_crops'.

Return only json, nothing else.'''
    base_api_url = "https://api.staging.pdf-parser.samagra.io"
    temp_dir = tempfile.mkdtemp()

    try:
        data = scraper()
    except:
        print("error scrapping website")
    try:
        move_json_to_history("latest", "history")
    except Exception as e:
        print("error",e)

    async with aiohttp.ClientSession() as session:
        tasks = [download_and_process(session, district, system_prompt, base_api_url, temp_dir) for district in data]
        await asyncio.gather(*tasks)

    total_districts = len(data)
    metadata = f"District_done: {counter}, Total_district: {total_districts}"
    with open("meta_data.txt", "w") as meta_file:
        json.dump(metadata, meta_file, indent=4)


    os.rmdir(temp_dir)

if __name__ == "__main__":
    retries = 3  
    retry_delay = 5

    for attempt in range(1, retries + 1):
        try:
            asyncio.run(main())
            break  # If successful, break out of the retry loop
        except Exception as e:
            print(f"Attempt {attempt}: An error occurred: {e}")
            if attempt < retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All retry attempts failed. Exiting.")
                raise e