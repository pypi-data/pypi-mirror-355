from __future__ import annotations
import io
import json
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import numpy as np
import torch
import onnxruntime as ort
from ultralytics import YOLO
from .exceptions import InferenceError, ModelExportError

class Detector:
    def __init__(
        self,
        model_stream: io.BytesIO,
        format: Literal["torch", "onnx"] = "torch",
        class_labels: Optional[List[str]] = None,
        confidence_threshold: float = 0.5,
        device: Literal["cpu", "cuda"] = "cuda",
    ):
        self.conf_th = confidence_threshold
        self.device = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
        self._model = None
        self._ort_session = None
        self._classes = class_labels or []
        self._arch = "yolov8"
        self._model_size = "n"
        self._image_size = 640
        self._cls_thresholds = {}
        self._load_model_from_stream(model_stream, format)
        self.stats = {"frames": 0, "time": 0.0}

    def _load_model_from_stream(self, stream: io.BytesIO, fmt: str):
        stream.seek(0)
        data = stream.read()

        if not data:
            raise ModelExportError("Empty model data stream")

        try:
            if fmt == "torch":
                payload = torch.load(io.BytesIO(data), map_location=self.device)
                if "model_data" not in payload or "meta" not in payload:
                    raise ModelExportError("Invalid torch model format")

                model_data, meta = payload["model_data"], payload["meta"]
                self._arch = meta.get("architecture", "yolov8")
                self._model_size = meta.get("model_size", "n")
                self._image_size = meta.get("image_size", 640)

                if not self._classes:
                    self._classes = meta.get("classes", [])
                if not self._classes:
                    raise ModelExportError("No classes found in model metadata")

                temp_model = Path(tempfile.mktemp(suffix=".pt"))
                temp_model.write_bytes(model_data)
                self._model = YOLO(str(temp_model))
                self._model.to(self.device)
                temp_model.unlink()

            elif fmt == "onnx":
                json_start = data.rfind(b"{")
                if json_start == -1:
                    raise ModelExportError("No metadata found in ONNX file")

                onnx_bytes = data[:json_start]
                meta_bytes = data[json_start:]
                meta = json.loads(meta_bytes.decode('utf-8'))

                self._arch = meta.get("architecture", "yolov8")
                self._model_size = meta.get("model_size", "n")
                self._image_size = meta.get("image_size", 640)

                if not self._classes:
                    self._classes = meta.get("classes", [])
                if not self._classes:
                    raise ModelExportError("No classes found in ONNX model metadata")

                sess_opt = ort.SessionOptions()
                sess_opt.intra_op_num_threads = 1
                sess_opt.inter_op_num_threads = 1

                providers = []
                if self.device.type == "cuda" and "CUDAExecutionProvider" in ort.get_available_providers():
                    providers.append("CUDAExecutionProvider")
                providers.append("CPUExecutionProvider")

                self._ort_session = ort.InferenceSession(onnx_bytes, sess_opt, providers=providers)
            else:
                raise ModelExportError(f"Unsupported model format: {fmt}")

        except Exception as e:
            if isinstance(e, ModelExportError):
                raise
            else:
                raise ModelExportError(f"Model loading error: {str(e)}")

    def predict(self, image: Union[np.ndarray, bytes]) -> List[Dict[str, Any]]:
        import cv2

        if isinstance(image, bytes):
            if len(image) == 0:
                raise InferenceError("Empty image byte data")
            try:
                buf = np.frombuffer(image, dtype=np.uint8)
                image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if image is None:
                    raise InferenceError("Failed to decode image from bytes")
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            except Exception as e:
                raise InferenceError(f"Image decoding error: {str(e)}")

        elif isinstance(image, np.ndarray):
            if image.size == 0:
                raise InferenceError("Empty numpy array")

            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif len(image.shape) == 3:
                if image.shape[2] == 4:
                    image = image[:, :, :3]
                elif image.shape[2] != 3:
                    raise InferenceError(f"Unsupported number of channels: {image.shape[2]}")
            else:
                raise InferenceError(f"Unsupported image shape: {image.shape}")

            if image.dtype != np.uint8:
                if image.dtype in [np.float32, np.float64]:
                    if image.max() <= 1.0:
                        image = (image * 255).astype(np.uint8)
                    else:
                        image = image.astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
        else:
            raise InferenceError(f"Invalid input image type: {type(image)}")

        start = time.perf_counter()
        try:
            if self._model:
                results = self._model.predict(
                    image, imgsz=self._image_size, conf=self.conf_th, device=self.device, verbose=False
                )

                detections = []
                if results and len(results) > 0:
                    result = results[0]
                    if result.boxes is not None and len(result.boxes) > 0:
                        boxes = result.boxes.xyxy.cpu().numpy()
                        scores = result.boxes.conf.cpu().numpy()
                        labels = result.boxes.cls.cpu().numpy().astype(int)

                        for box, score, label in zip(boxes, scores, labels):
                            if score >= self.conf_th and 0 <= label < len(self._classes):
                                class_name = self._classes[label]
                                threshold = self._cls_thresholds.get(class_name, self.conf_th)

                                if score >= threshold:
                                    x1, y1, x2, y2 = box
                                    width = x2 - x1
                                    height = y2 - y1

                                    detections.append({
                                        "bbox": [int(x1), int(y1), int(width), int(height)],
                                        "class": class_name,
                                        "score": float(score),
                                    })
            else:
                input_image = cv2.resize(image, (self._image_size, self._image_size))
                input_image = input_image.transpose(2, 0, 1).astype(np.float32) / 255.0
                input_image = np.expand_dims(input_image, axis=0)

                input_name = self._ort_session.get_inputs()[0].name
                ort_inputs = {input_name: input_image}
                ort_outputs = self._ort_session.run(None, ort_inputs)
                detections = self._process_onnx_output(ort_outputs[0], image.shape[:2])

        except Exception as e:
            raise InferenceError(f"Model inference error: {str(e)}")

        self.stats["frames"] += 1
        self.stats["time"] += time.perf_counter() - start
        return detections

    def _process_onnx_output(self, output: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        detections = []
        output = output[0].T
        max_scores = np.max(output[:, 4:], axis=1)
        mask = max_scores >= self.conf_th
        filtered_output = output[mask]

        orig_h, orig_w = original_shape
        scale_x = orig_w / self._image_size
        scale_y = orig_h / self._image_size

        for detection in filtered_output:
            x_center, y_center, width, height = detection[:4]
            class_scores = detection[4:4 + len(self._classes)]
            class_idx = np.argmax(class_scores)
            confidence = class_scores[class_idx]

            if confidence >= self.conf_th:
                x1 = (x_center - width / 2) * scale_x
                y1 = (y_center - height / 2) * scale_y
                x2 = (x_center + width / 2) * scale_x
                y2 = (y_center + height / 2) * scale_y

                x1 = max(0, min(orig_w, x1))
                y1 = max(0, min(orig_h, y1))
                x2 = max(0, min(orig_w, x2))
                y2 = max(0, min(orig_h, y2))

                w = x2 - x1
                h = y2 - y1

                if w > 0 and h > 0:
                    detections.append({
                        "bbox": [int(x1), int(y1), int(w), int(h)],
                        "class": self._classes[class_idx],
                        "score": float(confidence),
                    })

        return detections

    def fps(self) -> float:
        if self.stats["time"] == 0:
            return 0.0
        return self.stats["frames"] / self.stats["time"]

    def reset_stats(self):
        self.stats = {"frames": 0, "time": 0.0}

    def set_class_thresholds(self, thresholds: Dict[str, float]):
        for class_name, threshold in thresholds.items():
            if class_name not in self._classes:
                raise ValueError(f"Unknown class: {class_name}")
            if not 0.0 <= threshold <= 1.0:
                raise ValueError(f"Threshold must be in range [0, 1], got: {threshold}")
        self._cls_thresholds = thresholds.copy()

    def get_class_names(self) -> List[str]:
        return self._classes.copy()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "architecture": self._arch,
            "model_size": self._model_size,
            "classes": self._classes.copy(),
            "num_classes": len(self._classes),
            "image_size": self._image_size,
            "device": str(self.device),
            "confidence_threshold": self.conf_th,
            "class_thresholds": self._cls_thresholds.copy(),
        }

    def set_confidence_threshold(self, threshold: float):
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in range [0, 1], got: {threshold}")
        self.conf_th = threshold