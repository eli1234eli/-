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
                'token': '0773201948:14725836'  # החלף לטוקן שלך
            }
            response = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=data, files=files)
            if response.status_code == 200 and '"success":true' in response.text:
                print(f"[OK] קובץ {new_filename} נשלח ל-5/{subfolder} בהצלחה.")
                return True
            else:
                print(f"[ERROR] שליחה נכשלה לקובץ {new_filename} (סטטוס: {response.status_code})")
                print("תגובה מהשרת:", response.text)
                return False
    except Exception as e:
        print(f"[EXCEPTION] שגיאה בשליחת קובץ {new_filename}: {e}")
        return False


def clean_text_by_line_length(title, text, min_words=13):
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if len(line.strip().split()) >= min_words:
            cleaned_lines.append(line.strip())
    return title + "\n\n" + "\n\n".join(cleaned_lines)


print(f"\nהתחלת הרצה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

today = datetime.now().strftime('%Y-%m-%d')
folder_name = f"כתבות_{today}"
os.makedirs(folder_name, exist_ok=True)

counter = 0

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
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        original_filename = f"{safe_title[:100]}.tts"
        filepath = os.path.join(folder_name, original_filename)

        if os.path.exists(filepath):
            print(f"[SKIP] הקובץ כבר קיים: {original_filename}")
            continue

        content_divs = art_soup.find_all('div', class_='elementor-widget-container')
        article_text = ''
        for div in content_divs:
            paragraphs = div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    article_text += text + "\n\n"

        cleaned_text = clean_text_by_line_length(title, article_text)

        if cleaned_text.strip():
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)

            new_filename = f"{str(counter).zfill(3)}.tts"
            subfolder = str(counter)
            print(f"[INFO] מעלה קובץ: {new_filename} לתת-שלוחה 5/{subfolder}")
            upload_success = send_to_yemot(filepath, new_filename, subfolder)

            if upload_success:
                counter += 1
            else:
                print(f"[FAIL] נכשל שליחת הקובץ: {new_filename}")
        else:
            print(f"[EMPTY] תוכן ריק לאחר סינון לכתבה: {link}")

    except Exception as e:
        print(f"[ERROR] שגיאה בעיבוד הכתבה {link}: {e}")

print(f"\nסיום ההרצה: {datetime.now().strftime('%H:%M:%S')}")
