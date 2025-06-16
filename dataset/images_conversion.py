import os
import sys
import shutil
import logging
from PIL import Image
import pillow_avif

input_root = "parsed_images"
output_root = "converted_parsed_images"

# Список класів (папок)
classes = ["cannabis", "cigarette", "gun"]

# Підтримувані формати
allowed_extensions = ('.png', '.jpeg', '.jpg', '.webp', '.avif')

# Налаштування логування
log_filename = "conversion_log.txt"
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

for cls in classes:
    logging.info("")  # порожній рядок перед виводом кожного класу

    input_folder = os.path.join(input_root, f"{cls}_raw")
    output_folder = os.path.join(output_root, f"{cls}_jpg")

    if not os.path.isdir(input_folder):
        logging.warning(f"Input folder '{input_folder}' не існує, пропускаємо.")
        continue
    if not os.path.isdir(output_folder):
        logging.warning(f"Output folder '{output_folder}' не існує, пропускаємо.")
        continue

    counter = 1
    for filename in os.listdir(input_folder):
        ext = os.path.splitext(filename)[1].lower()

        if ext not in allowed_extensions:
            logging.error(f"Файл '{filename}' має непідтримуваний формат '{ext}', пропускаємо.")
            continue

        input_path = os.path.join(input_folder, filename)

        # Перевірка на формат jpg
        if ext == '.jpg':
            # Пропускаємо конвертацію тих зображень, що уже у форматі jpg
            new_filename = f"{counter}.jpg"
            output_path = os.path.join(output_folder, new_filename)
            try:
                shutil.copy2(input_path, output_path)  # копіюємо файл у нову папку з новим іменем
                logging.info(f"Пропущено конвертацію (вже jpg) та збережено: {output_path}")
                counter += 1
            except Exception as e:
                logging.error(f"Не вдалося скопіювати {input_path}: {e}")
            continue

        # Конвертуємо всі інші підтримувані формати
        try:
            with Image.open(input_path) as img:
                rgb_img = img.convert("RGB")
                new_filename = f"{counter}.jpg"
                output_path = os.path.join(output_folder, new_filename)
                rgb_img.save(output_path, "JPEG")
                logging.info(f"Конвертовано та збережено: {output_path}")
                counter += 1
        except Exception as e:
            logging.error(f"Не вдалося обробити {input_path}: {e}")
