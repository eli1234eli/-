import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

# תיקייה לשמירת הכתבות
today = datetime.now().strftime('%Y-%m-%d')
folder_name = f"כתבות_{today}"
os.makedirs(folder_name, exist_ok=True)

# כתובת עמוד החדשות הראשי
BASE_URL = "https://www.jdn.co.il"
NEWS_SECTION_URL = f"{BASE_URL}/news/"

# משיג את קוד ה־HTML של עמוד החדשות
response = requests.get(NEWS_SECTION_URL)
soup = BeautifulSoup(response.content, 'html.parser')

# מציאת כל הקישורים לכתבות
article_links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith(f"{BASE_URL}/news/") and re.match(r".*/\d+/?$", href):
        article_links.append(href)

# הסרת כפילויות
article_links = list(set(article_links))

print(f"נמצאו {len(article_links)} כתבות. מתחיל בשליפה...")

for link in article_links:
    try:
        art_res = requests.get(link)
        art_soup = BeautifulSoup(art_res.content, 'html.parser')

        # כותרת
        title_tag = art_soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "ללא כותרת"

        # ניקוי הכותרת לשם קובץ
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

        # תוכן הכתבה
        content_divs = art_soup.find_all('div', class_='elementor-widget-container')
        article_text = ''
        for div in content_divs:
            paragraphs = div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    article_text += text + "\n\n"

        if article_text.strip():
            # שמירת קובץ
            filepath = os.path.join(folder_name, f"{safe_title[:100]}.TTS")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(title + "\n\n" + article_text)
            print(f"שמור: {filepath}")
        else:
            print(f"תוכן ריק בכתבה: {link}")

    except Exception as e:
        print(f"שגיאה בקישור {link}: {e}")

print("סיום השליפה.")
