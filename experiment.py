from PyPDF2 import PdfReader
import asyncio
from openai import AsyncOpenAI
import os
import json
from dotenv import load_dotenv
import prompt

load_dotenv()
client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def process_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() if page.extract_text() else ""

    final_text = prompt.prompt + text

    try:
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
    except Exception as e:
        print(e)
        return pdf_path, "Error"
    return pdf_path, chat_completion.choices[0].message.content


async def main():
    pdf_folder = "/Users/__chaks__/repos/ouat.ac.in-api/pdfs"
    pdf_files = [
        os.path.join(pdf_folder, f)
        for f in os.listdir(pdf_folder)
        if f.endswith(".pdf")
    ]

    tasks = [process_pdf(pdf_file) for pdf_file in pdf_files]
    results = await asyncio.gather(*tasks)

    composite_json = {os.path.basename(key): value for key, value in results}
    return composite_json


# Run the main function
composite_results = asyncio.run(main())

for key in composite_results:
    composite_results[key] = json.loads(composite_results[key])

# Save the results in a file
with open("results.json", "w") as f:
    json.dump(composite_results, f, ensure_ascii=False, indent=4)
