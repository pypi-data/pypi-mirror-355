"""
YOLO8 Stream Processor - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from typing import Dict, List, Callable, Optional, Union, Tuple
from pathlib import Path
import mss
import PIL.Image


class YOLOStreamProcessor:
    """
    Процессор для обработки видео потока с использованием YOLO8
    """

    def __init__(self, model_path: str, device: str = 'auto'):
        """
        Инициализация процессора

        Args:
            model_path (str): Путь к файлу модели .pt
            device (str): Устройство для вычислений ('cpu', 'cuda', 'auto')
        """
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Модель не найдена: {model_path}")

        self.model_path = model_path
        self.model = YOLO(model_path)

        # Настройка устройства
        if device == 'auto':
            import torch
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        self.model.to(self.device)

        # Состояние процессора
        self.current_detections = {}
        self.is_running = False
        self.callback = None
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()

    def set_callback(self, callback: Callable[[Dict], None]):
        """
        Установка callback функции для получения детекций

        Args:
            callback: Функция, которая будет вызвана при каждой детекции
        """
        self.callback = callback

    def get_model_info(self) -> Dict:
        """
        Получение информации о модели

        Returns:
            Dict: Информация о модели (классы, количество параметров и т.д.)
        """
        return {
            'classes': self.model.names,
            'num_classes': len(self.model.names),
            'device': self.device,
            'model_path': str(self.model_path)
        }

    def process_stream(self,
                      source: Union[int, str] = 0,
                      confidence: float = 0.5,
                      iou_threshold: float = 0.45,
                      max_detections: int = 100,
                      imgsz: int = 640,
                      screen_region: Optional[Dict] = None) -> None:
        """
        Запуск обработки видео потока

        Args:
            source: Источник видео (0 для камеры, путь к файлу, 'screen' для экрана)
            confidence: Порог уверенности (0.0-1.0)
            iou_threshold: Порог IoU для NMS
            max_detections: Максимальное количество детекций
            imgsz: Размер изображения для обработки
            screen_region: Область экрана {"top": y, "left": x, "width": w, "height": h}
        """
        self.is_running = True

        # Обработка захвата экрана
        if source == 'screen':
            self._process_screen_stream(confidence, iou_threshold, max_detections, imgsz, screen_region)
            return

        # Обычный видео поток
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise RuntimeError(f"Не удалось открыть источник видео: {source}")

        # Настройка видео захвата
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        print(f"Запуск обработки потока на устройстве: {self.device}")
        print(f"Классы модели: {list(self.model.names.values())}")

        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    print("Завершение потока")
                    break

                # Обработка кадра
                self._process_frame(frame, confidence, iou_threshold, max_detections, imgsz)

                # Обновление FPS
                self._update_fps()

        except Exception as e:
            print(f"Ошибка при обработке потока: {e}")
        finally:
            cap.release()
            self.is_running = False

    def _process_screen_stream(self, confidence, iou_threshold, max_detections, imgsz, screen_region):
        """
        Обработка потока захвата экрана
        """
        print(f"Запуск захвата экрана на устройстве: {self.device}")
        print(f"Классы модели: {list(self.model.names.values())}")

        with mss.mss() as sct:
            # Определение области захвата
            if screen_region is None:
                # Захват всего экрана (первый монитор)
                monitor = sct.monitors[1]
            else:
                monitor = screen_region

            print(f"Область захвата: {monitor}")

            try:
                while self.is_running:
                    # Захват скриншота
                    screenshot = sct.grab(monitor)

                    # Конвертация в numpy array
                    frame = np.array(screenshot)

                    # Конвертация BGRA -> BGR (удаляем альфа канал)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    # Обработка кадра
                    self._process_frame(frame, confidence, iou_threshold, max_detections, imgsz)

                    # Обновление FPS
                    self._update_fps()

                    # Небольшая задержка для снижения нагрузки
                    time.sleep(0.01)

            except Exception as e:
                print(f"Ошибка при захвате экрана: {e}")
            finally:
                self.is_running = False

    def _process_frame(self, frame, confidence, iou_threshold, max_detections, imgsz):
        """Внутренняя обработка кадра"""
        # Запуск детекции
        results = self.model(
            frame,
            conf=confidence,
            iou=iou_threshold,
            max_det=max_detections,
            imgsz=imgsz,
            device=self.device,
            verbose=False
        )

        # Обновление детекций
        self._update_detections(results[0])

        # Вызов callback
        if self.callback:
            try:
                self.callback(self.current_detections.copy())
            except Exception as e:
                print(f"Ошибка в callback: {e}")

    def _update_detections(self, result):
        """
        Обновление текущих детекций
        """
        detections = {}

        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.cpu().numpy()

            for i, box in enumerate(boxes):
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                confidence = float(box.conf[0])

                # Координаты bbox
                x1, y1, x2, y2 = box.xyxy[0].astype(int)

                # Создание записи детекции
                detection_info = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                    'area': int((x2 - x1) * (y2 - y1))
                }

                # Группировка по классам
                if class_name not in detections:
                    detections[class_name] = []

                detections[class_name].append(detection_info)

        self.current_detections = detections

    def _update_fps(self):
        """Обновление счетчика FPS"""
        self.frame_count += 1
        current_time = time.time()

        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time

    def get_detections(self) -> Dict:
        """Получение текущих детекций"""
        return self.current_detections.copy()

    def get_classes(self) -> Dict[int, str]:
        """Получение всех классов модели"""
        return self.model.names.copy()

    def get_fps(self) -> float:
        """Получение текущего FPS"""
        return self.fps

    def get_screen_info(self) -> List[Dict]:
        """Получение информации о доступных мониторах"""
        try:
            with mss.mss() as sct:
                monitors = []
                for i, monitor in enumerate(sct.monitors):
                    if i == 0:  # Пропускаем виртуальный монитор
                        continue
                    monitors.append({
                        'id': i,
                        'top': monitor['top'],
                        'left': monitor['left'],
                        'width': monitor['width'],
                        'height': monitor['height']
                    })
                return monitors
        except Exception as e:
            print(f"Ошибка получения информации о мониторах: {e}")
            return []

    def stop(self):
        """Остановка обработки потока"""
        self.is_running = False
        print("Остановка обработки потока...")

    def is_active(self) -> bool:
        """Проверка активности процессора"""
        return self.is_running