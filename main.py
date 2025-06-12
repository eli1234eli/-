import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

def send_to_yemot(file_path, new_filename, subfolder):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (new_filename, f)}
            data = {
                'path': f"ivr2:/5/{subfolder}/{new_filename}",
                'token': '0773201948:14725836'
            }
            response = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=data, files=files)
            if response.status_code == 200 and '"success":true' in response.text:
                print(f"[OK] קובץ {new_filename} נשלח ל-5/{subfolder} בהצלחה.")
                return True
            else:
                print(f"[ERROR] שליחה נכשלה לקובץ {new_filename} (סטטוס: {response.status_code})")
                return False
    except Exception as e:
        print(f"[EXCEPTION] שגיאה בשליחת קובץ {new_filename}: {e}")
        return False

def clean_text_by_line_length(text, min_words=13):
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if len(line.strip().split()) >= min_words:
            cleaned_lines.append(line.strip())
    return "\n\n".join(cleaned_lines)

def split_text_to_chunks(full_text, chunk_size_words=150):
    words = full_text.split()
    chunks = [' '.join(words[i:i+chunk_size_words]) for i in range(0, len(words), chunk_size_words)]
    return chunks

print(f"\nהתחלת הרצה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

today = datetime.now().strftime('%Y-%m-%d')
folder_name = f"כתבות_{today}"
os.makedirs(folder_name, exist_ok=True)

current_file_number = 1  # התחלה מ-001
article_counter = 1
index_entries = []

BASE_URL = "https://www.jdn.co.il"
NEWS_SECTION_URL = f"{BASE_URL}/news/"

try:
    response = requests.get(NEWS_SECTION_URL)
    response.raise_for_status()
except Exception as e:
    print(f"[ERROR] שגיאה בשליפת עמוד חדשות: {e}")
    exit(1)

soup = BeautifulSoup(response.content, 'html.parser')

article_links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith(f"{BASE_URL}/news/") and re.match(r".*/\d+/?$", href):
        article_links.append(href)

article_links = list(set(article_links))
print(f"נמצאו {len(article_links)} כתבות לשליחה.")

for link in article_links:
    try:
        art_res = requests.get(link)
        art_res.raise_for_status()
        art_soup = BeautifulSoup(art_res.content, 'html.parser')

        title_tag = art_soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "ללא כותרת"
        short_title = title.split(" - ")[0][:50]
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

        content_divs = art_soup.find_all('div', class_='elementor-widget-container')
        article_text = ''
        for div in content_divs:
            paragraphs = div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    article_text += text + "\n\n"

        cleaned_text = clean_text_by_line_length(article_text)
        if not cleaned_text.strip():
            print(f"[EMPTY] תוכן ריק לאחר סינון לכתבה: {link}")
            continue

        chunks = split_text_to_chunks(cleaned_text)
        subfolder = str(article_counter)

        for i in range(5):  # תמיד 5 קבצים
            if i < len(chunks):
                chunk_text = chunks[i]
                if i == 0:
                    full_text = f"{title}\n\n{chunk_text}"
                else:
                    full_text = chunk_text
            else:
                full_text = "ס"

            filename = f"{str(current_file_number).zfill(3)}.tts"
            filepath = os.path.join(folder_name, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_text)

            print(f"[INFO] מעלה קובץ: {filename} לתת-שלוחה 5/{subfolder}")
            send_to_yemot(filepath, filename, subfolder)

            current_file_number += 1

        index_entries.append(f"{short_title} הקש {subfolder}.\n")
        article_counter += 1

    except Exception as e:
        print(f"[ERROR] שגיאה בעיבוד הכתבה {link}: {e}")

# יצירת קובץ אינדקס
if index_entries:
    index_filename = "M0000.tts"
    index_path = os.path.join(folder_name, index_filename)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(index_entries))

    print(f"[INFO] מעלה את הקובץ {index_filename} לשלוחה הראשית 5")
    send_to_yemot(index_path, index_filename, "")

print(f"\nסיום ההרצה: {datetime.now().strftime('%H:%M:%S')}")
