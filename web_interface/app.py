from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import os
import shutil
import requests
from parse_rozetka_category import parse_rozetka_category
from parse_custom_url import parse_custom_url

# Flask config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'D:/PycharmProjects/NeuroNetworks/web_interface/uploads'
app.config['OUTPUT_FOLDER'] = 'D:/PycharmProjects/NeuroNetworks/web_interface/outputs'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Load YOLOv8 model
model = YOLO('D:/PycharmProjects/NeuroNetworks/neural_model/runs/detect/train10/weights/best.pt')

# Категорії Rozetka
ROZETKA_CATEGORIES = {
    "Смартфони": "https://rozetka.com.ua/ua/smartfony/c80003/",
    "Ноутбуки": "https://rozetka.com.ua/ua/noutbuki/c80004/",
    "Навушники": "https://rozetka.com.ua/ua/naushniki/c168958/",
    "Цигарки": "https://rozetka.com.ua/ua/tovary-dlya-kurinnya/c4629318/",
    "Планшети": "https://rozetka.com.ua/ua/planshety/c1303091/",
    "Смарт-годинники": "https://rozetka.com.ua/ua/smart-watches/c105755/",
    "Телевізори": "https://rozetka.com.ua/ua/televizory/c80037/",
    "Холодильники": "https://rozetka.com.ua/ua/holodilniki/c80125/",
    "Пральні машини": "https://rozetka.com.ua/ua/stiralnye-mashiny/c80124/",
    "Пилососи": "https://rozetka.com.ua/ua/pylesosy/c80143/",
    "Фени та плойки": "https://rozetka.com.ua/ua/hair_dryers/c80188/",
    "Мікрохвильовки": "https://rozetka.com.ua/ua/microwaves/c80123/",
    "Електрочайники": "https://rozetka.com.ua/ua/electric-kettles/c80115/",
    "Кавомашини": "https://rozetka.com.ua/ua/coffee_machines/c80119/",
    "Фотоапарати": "https://rozetka.com.ua/ua/photo/c80001/",
    "Ігрові приставки": "https://rozetka.com.ua/ua/game-consoles/c80167/",
    "Відеокарти": "https://rozetka.com.ua/ua/videocards/c80087/",
    "Материнські плати": "https://rozetka.com.ua/ua/motherboards/c80082/",
    "Дрилі та перфоратори": "https://rozetka.com.ua/ua/drills/c80052/",
    "Шини": "https://rozetka.com.ua/ua/shiny/c80199/",
    "Чай та кава": "https://rozetka.com.ua/ua/tea-coffee/c4626955/",
    "Солодощі": "https://rozetka.com.ua/ua/konfety/c4625025/",
    "Ковбаси та м'ясні делікатеси": "https://rozetka.com.ua/ua/sausage_meat/c4627095/",
    "Молочні продукти": "https://rozetka.com.ua/ua/milk_products/c4627059/",
    "Крупи та макарони": "https://rozetka.com.ua/ua/cereals_pasta/c4627086/",
    "Овочі та фрукти": "https://rozetka.com.ua/ua/fruits-vegetables/c4626983/",
    "Заморожені продукти": "https://rozetka.com.ua/ua/frozen-foods/c4627085/",
    "Жіночий одяг": "https://rozetka.com.ua/ua/womens_clothing/c133888/",
    "Чоловічий одяг": "https://rozetka.com.ua/ua/mens_clothing/c133883/",
    "Дитячий одяг": "https://rozetka.com.ua/ua/children_clothes/c133891/"
}

# Дозволені типи файлів
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Головна сторінка
@app.route('/')
def index():
    image_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', categories=ROZETKA_CATEGORIES, image_files=image_files)

# Обробка завантажених зображень
@app.route('/process', methods=['POST'])
def process():
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    shutil.rmtree(app.config['OUTPUT_FOLDER'], ignore_errors=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    uploaded_files = request.files.getlist("images")
    detected_labels = {}

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            results = model(filepath, conf=0.9)
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            results[0].save(filename=output_path)

            labels = [model.names[int(cls)] for cls in results[0].boxes.cls]
            detected_labels[filename] = labels

    return render_template('results.html', results=detected_labels, image_files=os.listdir(app.config['OUTPUT_FOLDER']))

# Скачування оброблених зображень
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

# Відображення зображень із папки outputs
@app.route('/outputs/<filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

# Парсинг зображень із Rozetka
@app.route('/parse_rozetka', methods=['POST'])
def parse_rozetka_images():
    category_key = request.form.get('category')
    if category_key not in ROZETKA_CATEGORIES:
        return "Категорія не знайдена", 400

    category_url = ROZETKA_CATEGORIES[category_key]

    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    image_urls = parse_rozetka_category(category_url, app.config['UPLOAD_FOLDER'])

    for url in image_urls:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                filename = secure_filename(url.split("/")[-1])
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
        except Exception as e:
            print(f"[Помилка] Не вдалося завантажити зображення {url}: {e}")

    return redirect(url_for('index'))

@app.route('/parse_custom', methods=['POST'])
def parse_custom_images():
    custom_url = request.form.get('custom_url')
    if not custom_url or not custom_url.startswith("http"):
        return "Некоректна URL-адреса", 400

    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    image_urls = parse_custom_url(custom_url, app.config['UPLOAD_FOLDER'])

    for url in image_urls:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                filename = secure_filename(url.split("/")[-1].split("?")[0])
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
        except Exception as e:
            print(f"[Помилка] Не вдалося завантажити зображення {url}: {e}")

    return redirect(url_for('index'))

# Запуск Flask-сервера
if __name__ == '__main__':
    app.run(debug=True)
