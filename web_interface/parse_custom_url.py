import os
import re
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, urlparse
from datetime import datetime

# Очистка імені файлу від заборонених символів
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Логування подій у файл з нумерацією та таймстампом
def log_message(message, log_file_path, log_counter):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{log_counter}. {timestamp} {message}"
    print(log_entry)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

# Перевірка на валідність та безпечність URL-адреси
def is_valid_url(url):
    try:
        parsed = urlparse(url)
        # Перевірка схеми (http/https) та наявності домену
        if parsed.scheme not in ['http', 'https'] or not parsed.netloc:
            return False

        # Заборонені розширення, небезпечні для обробки
        disallowed_exts = ('.exe', '.bat', '.js', '.zip', '.rar', '.mp4', '.avi', '.mkv')
        # Дозволені розширення веб-сторінок
        allowed_exts = ('.html', '.php', '')  # '' означає шлях без розширення

        path = parsed.path.lower()
        if '.' in os.path.basename(path):  # Якщо є розширення файлу в URL
            if not path.endswith(allowed_exts) or path.endswith(disallowed_exts):
                return False

        return True
    except Exception:
        return False

# Основна функція парсингу зображень зі сторінки
def parse_custom_url(category_url, download_folder, max_images=300, log_file_path="custom_parsing_log.txt"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    # Зчитування наявного лог-файлу для подальшого підрахунку нових записів
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as f:
            initial_log_lines = f.readlines()
    else:
        initial_log_lines = []

    log_counter = 1

    # Перевірка валідності URL перед парсингом
    if not is_valid_url(category_url):
        log_message(f"[Відхилено] Некоректне або потенційно небезпечне посилання: {category_url}", log_file_path, log_counter)
        return []
    log_counter += 1

    # Завантаження HTML-коду сторінки
    try:
        response = requests.get(category_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        log_message(f"[Помилка] Не вдалося завантажити сторінку: {e}", log_file_path, log_counter)
        return []
    log_counter += 1

    # Парсинг HTML для пошуку зображень
    soup = BeautifulSoup(response.text, 'html.parser')
    image_tags = soup.find_all('img')
    image_urls = []
    saved_files = []

    # Створення директорії для збереження, якщо вона ще не існує
    os.makedirs(download_folder, exist_ok=True)

    # Фільтрація зображень за ключовими словами та збирання URL-ів
    for tag in image_tags:
        if len(image_urls) >= max_images:
            break

        src = tag.get('src') or tag.get('data-src')
        combined_attributes = ' '.join(
            str(tag.get(attr, '')).lower() for attr in ['alt', 'class', 'title', 'aria-label'])

        # Пропускаємо зображення з ознаками реклами, банерів, логотипів тощо
        if any(skip_word in combined_attributes for skip_word in ['banner', 'tag', 'logo']) or (
                src and any(skip_word in src.lower() for skip_word in ['banner', 'tag', 'logo'])):
            log_message(f"[Пропущено] Зображення з ознакою 'banner', 'tag' або 'logo': {src}", log_file_path, log_counter)
            log_counter += 1
            continue

        # Додаємо тільки прямі посилання на зображення
        if src and src.startswith('http'):
            image_urls.append(src)

    # Завантаження зображень за зібраними URL
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

    # Визначення кількості нових успішних збережень після поточного запуску
    with open(log_file_path, "r", encoding="utf-8") as f:
        final_log_lines = f.readlines()

    new_entries = final_log_lines[len(initial_log_lines):]
    new_saved_count = sum(1 for line in new_entries if "[Збережено]" in line)

    log_message(f"Загальна кількість успішно збережених зображень за цей запуск: {new_saved_count}", log_file_path, log_counter)

    return saved_files
