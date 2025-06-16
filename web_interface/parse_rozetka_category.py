import os
import re
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from datetime import datetime

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def log_message(message, log_file_path, log_counter):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{log_counter}. {timestamp} {message}"
    print(log_entry)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def parse_rozetka_category(category_url, download_folder, max_images=300, log_file_path="rozetka_parsing_log.txt"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    # Запам'ятовуємо розмір лог-файлу на початку
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as f:
            initial_log_lines = f.readlines()
    else:
        initial_log_lines = []

    log_counter = 1
    try:
        response = requests.get(category_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log_message(f"[Помилка] Не вдалося завантажити сторінку Rozetka: {e}", log_file_path, log_counter)
        return []
    log_counter += 1

    soup = BeautifulSoup(response.text, 'html.parser')
    image_tags = soup.find_all('img')
    image_urls = []
    saved_files = []

    os.makedirs(download_folder, exist_ok=True)

    for tag in image_tags:
        if len(image_urls) >= max_images:
            break

        src = tag.get('src') or tag.get('data-src')
        combined_attributes = ' '.join(str(tag.get(attr, '')).lower() for attr in ['alt', 'class', 'title', 'aria-label'])
        if 'banner' in combined_attributes or (src and 'banner' in src.lower()):
            log_message(f"[Пропущено] Зображення з ознакою 'banner': {src}", log_file_path, log_counter)
            log_counter += 1
            continue

        if src and (src.endswith('.svg') or src.endswith('.png')):
            log_message(f"[Пропущено] Формат файлу не підтримується (svg/png): {src}", log_file_path, log_counter)
            log_counter += 1
            continue

        if src and src.startswith('http'):
            image_urls.append(src)

    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, stream=True, headers=headers, timeout=10)
            if response.status_code == 200:
                filename = sanitize_filename(os.path.basename(urlsplit(url).path)) or f"parsed_image_{i + 1}.jpg"
                filepath = os.path.join(download_folder, filename)
                with open(filepath, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                saved_files.append(filepath)
                log_message(f"[Збережено] {filepath}", log_file_path, log_counter)
            else:
                log_message(f"[Помилка] Код статусу {response.status_code} для {url}", log_file_path, log_counter)
            log_counter += 1
        except Exception as e:
            log_message(f"[Помилка] Неможливо завантажити {url}: {e}", log_file_path, log_counter)
            log_counter += 1

    # Після завершення: читаємо нові рядки з лог-файлу
    with open(log_file_path, "r", encoding="utf-8") as f:
        final_log_lines = f.readlines()

    new_entries = final_log_lines[len(initial_log_lines):]
    new_saved_count = sum(1 for line in new_entries if "[Збережено]" in line)

    log_message(f"Загальна кількість успішно збережених зображень за цей запуск: {new_saved_count}", log_file_path, log_counter)

    return saved_files


