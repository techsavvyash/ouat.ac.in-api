import requests
import tempfile
import os
from bs4 import BeautifulSoup
import json
import openai
from dotenv import load_dotenv

load_dotenv()
api_key=os.environ.get("OPENAI_API_KEY")
openai.api_key = api_key

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

def scraper():
    url='https://ouat.ac.in/quick-links/agro-advisory-services/'
    response=requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data=[]
    districts = soup.find_all('div', class_='hide1')
    for district in districts:
        district_name=district.get('id')[:-1]
        data_dict={'district_name': district_name, 'info':{}}
        table=district.find('table').find('tbody')
        rows = table.select('tr')
        for row in rows:
            columns = row.find_all('td')
            date = columns[1].text.strip()
            english_link = columns[2].find('a')['href']
            odia_link = columns[3].find('a')['href']
            link_dict = {'english': english_link, 'odia': odia_link}
            data_dict['info'][date] = link_dict
        data.append(data_dict)
    
    return data

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

def send_to_api(pdf_path, base_url):
    api_url = f"{base_url}/process_md/"
    files = {'file': open(pdf_path, 'rb')}
    data = {'language': 'english'}

    response = requests.post(api_url, files=files, data=data)

    if response.status_code == 200:
        pdf_id = response.json().get('pdf_id')
        print("PDF processed successfully. PDF ID:", pdf_id)
        return pdf_id
    else:
        print(f"Failed to send PDF to API. Status code: {response.status_code}")
        return None

def download_md(pdf_id, base_url, temp_dir):
    # api_url = f"{base_url}/download_md/"
    api_url="https://rachitavya.github.io/testing_ghapi/gpt_response.md"
    params = {'pdf_id': pdf_id}

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        md_content = response.text
        md_temp_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".md")
        with open(md_temp_file.name, 'w') as f:
            f.write(md_content)
        print("Markdown file downloaded successfully.")
        return md_temp_file.name
    else:
        print(f"Failed to download Markdown file. Status code: {response.status_code}")
        return None



def process_data(data, system_prompt, base_api_url, temp_dir):
    for district in data:
        district_name = district["district_name"]
        info = district["info"]

        latest_date = None
        latest_gpt_response = None

        for date, languages in info.items():
            # Focus only on English language links
            date_str = date.replace('/', '-')
            english_link = languages.get("english")

            if english_link:
                pdf_path = download_pdf(english_link, temp_dir)

                if pdf_path:
                    pdf_id = send_to_api(pdf_path, base_api_url)

                    if pdf_id:
                        md_path = download_md(pdf_id, base_api_url, temp_dir)

                        if md_path:
                            with open(md_path, 'r') as md_file:
                                user_prompt = md_file.read()

                            gpt_response = get_gpt_response(system_prompt, user_prompt)

                            history_output_dir = "history"
                            os.makedirs(history_output_dir, exist_ok=True)
                            history_output_file = os.path.join(history_output_dir, f"{date_str}_{district_name}.json")
                            with open(history_output_file, 'w') as json_file:
                                json.dump(gpt_response, json_file, indent=2)

                            print(f"GPT response for {district_name} on {date} saved to {history_output_file}")

                            # Update the latest date for the district
                            if latest_date is None or date > latest_date:
                                latest_date = date
                                latest_gpt_response = gpt_response

                            # Clean up the temporary files
                            os.unlink(pdf_path)
                            os.unlink(md_path)

        # Save the GPT response for the latest date to the "latest" folder
        if latest_date:
            latest_output_dir = "latest"
            os.makedirs(latest_output_dir, exist_ok=True)
            latest_output_file = os.path.join(latest_output_dir, f"{district_name}.json")
            with open(latest_output_file, 'w') as json_file:
                json.dump(latest_gpt_response, json_file, indent=2)

            print(f"Latest GPT response for {district_name} saved to {latest_output_file}")


if __name__ == "__main__":
    system_prompt='''You are an agent which analyze data in the form of md file content and return only json for the information required.
I will give an md having agro-advisory data. You need to extract these things:
- Key: 'weather'; Value:Extracting table about weather details tagged as 'weather table' 
Note: keep weather table in dict format with keys having individual tupples.
- Key:'general_advice'; value: Extracting general advice about the weather and cropping from the pdf tagged as 'general advice' 
- Key:'name_of_crops'; Value: Name of crops for which further info is present 
- Key:'crops_data'; Value: dictionary having info of extracting the crops/animal husbandry/poultry/fishing details from it and extracting information for each crop/animal from it, each tagged separately for each crop/subgroup (There should be a distinct finite list of these subgroups) (Keys: each crop name, Value: Should be a dict with compulsory key 'advisory')

Return only json, nothing else.'''
    base_api_url = "http://52.191.57.171:8000"

    temp_dir = tempfile.mkdtemp()

    # Call the scraper function to get data
    data = scraper()

    process_data(data, system_prompt, base_api_url, temp_dir)

    # Clean up the temporary directory
    os.rmdir(temp_dir)