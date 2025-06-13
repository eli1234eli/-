#  קוד לאתר אמס
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
                'path': f"ivr2:/4/{subfolder}/{new_filename}",
                'token': '0773201948:14725836'
            }
            response = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=data, files=files)
            if response.status_code == 200 and '"success":true' in response.text:
                print(f"[OK] קובץ {new_filename} נשלח ל-4/{subfolder} בהצלחה.")
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


def split_text_to_chunks(full_text, chunk_size_words=100):
    words = full_text.split()
    chunks = [' '.join(words[i:i+chunk_size_words]) for i in range(0, len(words), chunk_size_words)]
    return chunks

print(f"\nהתחלת הרצה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

today = datetime.now().strftime('%Y-%m-%d')
folder_name = f"כתבות_{today}"
os.makedirs(folder_name, exist_ok=True)

current_file_number = 1
article_counter = 1
index_entries = []

BASE_URL = "https://www.emess.co.il"
NEWS_SECTION_URL = f"{BASE_URL}/section/1312"

try:
    response = requests.get(NEWS_SECTION_URL)
    response.raise_for_status()
except Exception as e:
    print(f"[ERROR] שגיאה בשליפת עמוד כתבות: {e}")
    exit(1)

soup = BeautifulSoup(response.content, 'html.parser')

# שליפת הקישורים
article_links = []
for a in soup.find_all('a', href=True, class_=lambda c: c and 'news-item' in c):
    href = a['href']
    if href.startswith("/radio/") and href not in article_links:
        article_links.append(BASE_URL + href)
    if len(article_links) >= 10:
        break

print(f"נמצאו {len(article_links)} כתבות לשליחה.")

# עיבוד כל כתבה
for link in article_links:
    try:
        art_res = requests.get(link)
        art_res.raise_for_status()
        art_soup = BeautifulSoup(art_res.content, 'html.parser')

        # כותרת מה- <h1> בתוך div.article-info
        article_info = art_soup.find('div', class_='article-info')
        title = article_info.find('h1').get_text(strip=True) if article_info and article_info.find('h1') else "ללא כותרת"
        short_title = title[:50]
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

        # תוכן הכתבה
        paragraphs = art_soup.find_all('p')
        article_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        cleaned_text = clean_text_by_line_length(article_text)

        if not cleaned_text.strip():
            print(f"[EMPTY] תוכן ריק לאחר סינון לכתבה: {link}")
            continue

        chunks = split_text_to_chunks(cleaned_text)
        chunks = chunks[:5]  # מקסימום 5 קבצים
        subfolder = str(article_counter)

        for i in range(5):  # תמיד 5 קבצים
            if i < len(chunks):
                chunk_text = chunks[i]
                if i == 0:
                    full_text = f"{title}\n\n{chunk_text}"
                else:
                    full_text = chunk_text
            else:
                full_text = "סוף כתבה"

            filename = f"{str(current_file_number).zfill(3)}.tts"
            filepath = os.path.join(folder_name, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_text)

            print(f"[INFO] מעלה קובץ: {filename} לתת-שלוחה 4/{subfolder}")
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

    print(f"[INFO] מעלה את הקובץ {index_filename} לשלוחה הראשית 4")
    send_to_yemot(index_path, index_filename, "")

print(f"\nסיום ההרצה: {datetime.now().strftime('%H:%M:%S')}")
