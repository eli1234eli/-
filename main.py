import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

# התחלה
print(f"\nהתחל הרצה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# תיקייה לשמירת הכתבות
today = datetime.now().strftime('%Y-%m-%d')
folder_name = f"כתבות_{today}"
os.makedirs(folder_name, exist_ok=True)

# כתובת עמוד החדשות
BASE_URL = "https://www.jdn.co.il"
NEWS_SECTION_URL = f"{BASE_URL}/news/"

# שליפת עמוד ראשי
try:
    response = requests.get(NEWS_SECTION_URL)
    response.raise_for_status()
except Exception as e:
    print(f"שגיאה בשליפת עמוד חדשות: {e}")
    exit(1)

soup = BeautifulSoup(response.content, 'html.parser')

# קישורים לכתבות
article_links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith(f"{BASE_URL}/news/") and re.match(r".*/\d+/?$", href):
        article_links.append(href)

article_links = list(set(article_links))
print(f"נמצאו {len(article_links)} כתבות. מתחיל בשליפה...\n")

# שליפת כל כתבה
for link in article_links:
    try:
        art_res = requests.get(link)
        art_res.raise_for_status()
        art_soup = BeautifulSoup(art_res.content, 'html.parser')

        title_tag = art_soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "ללא כותרת"
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        filename = f"{safe_title[:100]}.TTS"
        filepath = os.path.join(folder_name, filename)

        # דילוג אם כבר נשמר
        if os.path.exists(filepath):
            print(f"כבר נשמר: {filename}")
            continue

        content_divs = art_soup.find_all('div', class_='elementor-widget-container')
        article_text = ''
        for div in content_divs:
            paragraphs = div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    article_text += text + "\n\n"

        if article_text.strip():
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(title + "\n\n" + article_text)
            print(f"שמור: {filename}")
        else:
            print(f"תוכן ריק בכתבה: {link}")

    except Exception as e:
        print(f"שגיאה בכתבה {link}: {e}")

print(f"\nסיום השליפה: {datetime.now().strftime('%H:%M:%S')}")
