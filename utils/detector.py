import time
from pathlib import Path

import cv2
from ultralytics import YOLO


class DishDetector:
    """Поиск посуды и столовых приборов на изображении."""

    DISH_CLASSES = {
        "wine glass": "бокал",
        "cup": "чашка",
        "fork": "вилка",
        "knife": "нож",
        "spoon": "ложка",
        "bowl": "миска",
    }

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.class_ids = []

        for class_id, class_name in self.model.names.items():
            if class_name in self.DISH_CLASSES:
                self.class_ids.append(class_id)

        if not self.class_ids:
            raise ValueError("В модели не найдены классы посуды.")

    def detect_dishes(
        self,
        input_path: str,
        output_path: str,
        confidence: float = 0.35,
        image_size: int = 640,
    ):
        """Обрабатывает одно изображение и возвращает статистику."""
        start_time = time.perf_counter()

        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError("Файл не является корректным изображением.")

        results = self.model.predict(
            source=image,
            conf=confidence,
            imgsz=image_size,
            classes=self.class_ids,
            verbose=False,
        )

        result = results[0]
        boxes = result.boxes
        class_counts = {}
        confidences = []

        for box in boxes:
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            russian_name = self.DISH_CLASSES.get(class_name, class_name)
            class_counts[russian_name] = class_counts.get(russian_name, 0) + 1
            confidences.append(float(box.conf[0]))

        annotated_image = result.plot()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if not cv2.imwrite(str(output_path), annotated_image):
            raise OSError("Не удалось сохранить обработанное изображение.")

        average_confidence = 0
        if confidences:
            average_confidence = sum(confidences) / len(confidences)

        return {
            "count": len(boxes),
            "class_counts": class_counts,
            "average_confidence": round(average_confidence * 100, 2),
            "processing_time": round(time.perf_counter() - start_time, 3),
            "image_size": image_size,
            "confidence": round(confidence * 100, 1),
        }
