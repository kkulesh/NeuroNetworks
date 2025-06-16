from ultralytics import YOLO

# Завантаження моделі
model = YOLO('D:/PycharmProjects/NeuroNetworks/neural_model/runs/detect/train10/weights/best.pt')

# Задаємо шлях до папки з зображеннями
image_dir = 'D:/PycharmProjects/NeuroNetworks/object_detection/parsed_images'

# Запускаємо детекцію на всіх зображеннях у папці
results = model(
    source=image_dir,
    project='D:/PycharmProjects/NeuroNetworks/object_detection',
    name='detection_results',
    save=True,
    show=True,
    conf=0.9
)

# Обробка кожного зображення в результатах
for i, result in enumerate(results):
    boxes = result.boxes.xyxy.cpu().numpy()
    scores = result.boxes.conf.cpu().numpy()
    classes = result.boxes.cls.cpu().numpy()

    print(f"\n--- Image {i + 1} ---")
    print("Boxes:\n", boxes)
    print("Scores:\n", scores)
    print("Classes:\n", classes)
