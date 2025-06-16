from ultralytics import YOLO

# Тренування моделі
model = YOLO("yolov8s.pt")
model.train(data="Neural Network.v7i.yolov8/data.yaml",
            epochs=50,
            imgsz=416,
            batch=8,
            workers=0)



