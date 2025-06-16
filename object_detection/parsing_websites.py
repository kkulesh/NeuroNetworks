import os
import re
import requests
import shutil
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def create_unique_folder(base_name="parsed_images"):
    counter = 1
    while os.path.exists(f"{base_name}{counter}"):
        counter += 1
    folder_name = f"{base_name}{counter}"
    os.makedirs(folder_name)
    return folder_name, counter

def log_message(message, log_file_path):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{timestamp} {message}"
    print(log_entry)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def get_images_with_selenium(url, folder, log_file_path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )
    except:
        log_message("Зображення не завантажились за таймаут.", log_file_path)
        driver.quit()
        return

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    img_tags = soup.find_all("img")
    image_urls = []

    for img in img_tags:
        src = img.get("src") or img.get("data-src")
        if not src:
            continue

        # Фільтрація за ключовими словами
        alt = img.get("alt", "").lower()
        class_attr = " ".join(img.get("class", [])).lower()
        full_src = src.lower()

        if any(word in full_src or word in alt or word in class_attr for word in ["tag", "banner"]):
            reason = f"Пропущено (tag/banner): src='{src}', alt='{alt}', class='{class_attr}'"
            log_message(reason, log_file_path)
            continue

        if src.endswith((".jpg", ".jpeg", ".png", ".webp")):
            full_url = urljoin(url, src)
            image_urls.append(full_url)

    log_message(f"Знайдено {len(image_urls)} зображень.", log_file_path)

    for idx, img_url in enumerate(image_urls, start=1):
        try:
            r = requests.get(img_url, stream=True, timeout=10)
            if r.status_code == 200:
                filename = sanitize_filename(os.path.basename(urlsplit(img_url).path))
                if not filename:
                    filename = f"image_{idx}.webp"
                path = os.path.join(folder, filename)
                with open(path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                log_message(f"{idx}. Завантажено: {img_url}", log_file_path)
            else:
                log_message(f"{idx}. Код {r.status_code}: {img_url}", log_file_path)
        except Exception as e:
            log_message(f"{idx}. Помилка: {img_url} -> {e}", log_file_path)

if __name__ == "__main__":
    url = "https://rozetka.com.ua/"
    folder, folder_number = create_unique_folder("parsed_images")
    log_file = f"parsing_log{folder_number}.txt"
    get_images_with_selenium(url, folder, log_file)
