import json
import asyncio
import requests
import tempfile
import os
import shutil
import time
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from PyPDF2 import PdfReader
import prompt
import logging
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR)


async def process_pdf(district_data, temp_dir):
    district_name = district_data['district_name']
    date = district_data['date'].replace('/', '-')
    pdf_link = district_data['link']['english']

    print("Processing data for", district_name)
    pdf_path = download_pdf(pdf_link, temp_dir)
    if pdf_path is None:
        logging.error(f"Error downloading PDF for {district_name}")
        return district_name, "Error"

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() if page.extract_text() else ""

        final_text = prompt.prompt + text

        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": final_text,
                }
            ],
            model="gpt-3.5-turbo-0125",
            response_format={"type": "json_object"},
        )

        response = chat_completion.choices[0].message.content
        response = json.loads(response)
        response['date'] = date

    except Exception as e:
        logging.error(f"Error processing PDF for {district_name}: {e}")
        return district_name, "Error"

    return district_name, response


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
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        data = []
        districts = soup.find_all('div', class_='hide1')
        for district in districts:
            district_name = district.get('id')[:-1]
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


async def main():
    temp_dir = tempfile.mkdtemp()

    try:
        districts_data = scraper()
    except Exception as e:
        logging.error(f"Error getting districts data: {e}")
        print("Error scraping website")

    tasks = [process_pdf(district_data, temp_dir) for district_data in districts_data]
    results = await asyncio.gather(*tasks)

    composite_json = {key: value for key, value in results}

    total_districts = len(districts_data)
    error_count = sum(1 for value in composite_json.values() if isinstance(value, str) and value == "error")
    metadata = f"District_done: {total_districts - error_count}, Total_district: {total_districts}"
    with open("meta_data.txt", "w") as meta_file:
        json.dump(metadata, meta_file, indent=4)

    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logging.error(f"Error removing temporary directory: {e}")

    return composite_json


if __name__ == "__main__":
    retries = 3
    retry_delay = 5

    for attempt in range(1, retries + 1):
        try:
            composite_results = asyncio.run(main())
            with open("latest_data.json", "w") as f:
                json.dump(composite_results, f, ensure_ascii=False, indent=4)
            print('latest data saved successfully')
            break  # If successful, break out of the retry loop
        except Exception as e:
            logging.error(f"Attempt {attempt}: An error occurred: {e}")
            if attempt < retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All retry attempts failed. Exiting.")
                raise e
