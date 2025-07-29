from __future__ import annotations
import io
import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Literal, Union
import torch
from ultralytics import YOLO
import numpy as np
from .exceptions import DatasetError, ModelExportError, ValidationError
from .utils import create_yolo_dataset_files

class Trainer:
    SUPPORTED_MODELS = ("n", "s", "m", "l", "x")

    def __init__(
        self,
        model_size: str = "n",
        epochs: int = 50,
        batch_size: int = 16,
        learning_rate: float = 1e-3,
        image_size: int = 640,
        use_augmentation: bool = True,
        device: Literal["cpu", "cuda"] = "cuda",
        train_confidence: float = 0.3,
    ):
        if model_size not in self.SUPPORTED_MODELS:
            raise ValidationError(f"model_size must be one of {self.SUPPORTED_MODELS}")

        self.model_size = model_size
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = learning_rate
        self.image_size = image_size
        self.augment = use_augmentation
        self.device = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
        self.train_confidence = train_confidence

        self._classes = []
        self._model = None
        self._temp_dir = None
        self._dataset_yaml = None

    def load_dataset(
        self,
        images: List[Union[str, bytes, np.ndarray]],
        annotations_json: Union[str, Dict],
        format: Literal["coco", "custom"] = "coco",
    ):
        anns_dict = json.loads(annotations_json) if isinstance(annotations_json, str) else annotations_json

        if format == "coco":
            from .utils import parse_coco
            per_image, self._classes = parse_coco(anns_dict)
        else:
            raise ValidationError("Only 'coco' format is supported")

        if len(per_image) != len(images):
            raise DatasetError(f"Number of images ({len(images)}) and annotations ({len(per_image)}) don't match")

        if not self._classes:
            raise DatasetError("No classes found")

        self._temp_dir = Path(tempfile.mkdtemp(prefix="yolo_training_"))

        self._dataset_yaml = create_yolo_dataset_files(
            images=images,
            annotations=per_image,
            classes=self._classes,
            output_dir=self._temp_dir,
            image_size=self.image_size
        )

    def train(self, resume: bool = False):
        if not self._dataset_yaml:
            raise DatasetError("Call load_dataset() first")

        model_name = f"yolov8{self.model_size}.pt"
        self._model = YOLO(model_name)

        try:
            self._model.train(
                data=self._dataset_yaml,
                epochs=self.epochs,
                imgsz=self.image_size,
                batch=self.batch_size,
                lr0=self.lr,
                device=self.device.index if self.device.type == "cuda" else "cpu",
                augment=self.augment,
                project=str(self._temp_dir / "runs"),
                name="yolo_training",
                exist_ok=True,
                verbose=False,
                patience=max(10, self.epochs // 5),
                save_period=10,
                plots=False,
                resume=resume,
                conf=self.train_confidence,
            )

            best_model_path = self._temp_dir / "runs" / "yolo_training" / "weights" / "best.pt"
            if best_model_path.exists():
                self._model = YOLO(str(best_model_path))

        except Exception as e:
            raise ModelExportError(f"YOLOv8 training error: {str(e)}")

    def evaluate(self) -> Dict[str, float]:
        if not self._model:
            raise ValidationError("Model not trained")

        try:
            results = self._model.val(
                data=self._dataset_yaml,
                imgsz=self.image_size,
                batch=self.batch_size,
                device=self.device.index if self.device.type == "cuda" else "cpu",
                plots=False,
                verbose=False,
                conf=self.train_confidence,
            )

            metrics_dict = results.results_dict
            mAP50_95 = metrics_dict.get("metrics/mAP50-95(B)", 0.0)
            mAP50 = metrics_dict.get("metrics/mAP50(B)", 0.0)
            precision = metrics_dict.get("metrics/precision(B)", 0.0)
            recall = metrics_dict.get("metrics/recall(B)", 0.0)
            f1 = 2 * precision * recall / (precision + recall + 1e-8) if (precision + recall) > 0 else 0.0

            return {
                "mAP50-95": float(mAP50_95),
                "mAP50": float(mAP50),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
            }
        except:
            return {"mAP50-95": 0.0, "mAP50": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}

    def save_model(self, format: str = "torch") -> io.BytesIO:
        if not self._model:
            raise ModelExportError("Model not trained")

        meta = {
            "architecture": "yolov8",
            "model_size": self.model_size,
            "classes": self._classes,
            "image_size": self.image_size,
            "num_classes": len(self._classes),
            "train_confidence": self.train_confidence,
        }

        stream = io.BytesIO()

        if format == "torch":
            model_path = self._temp_dir / "model_export.pt"
            self._model.save(str(model_path))
            model_data = model_path.read_bytes()
            payload = {"model_data": model_data, "meta": meta}
            torch.save(payload, stream)
        elif format == "onnx":
            onnx_path = self._model.export(format="onnx", imgsz=self.image_size, opset=12, simplify=True, dynamic=False)
            onnx_data = Path(onnx_path).read_bytes()
            stream.write(onnx_data)
            stream.write(json.dumps(meta).encode())
        else:
            raise ModelExportError("format must be 'torch' or 'onnx'")

        stream.seek(0)
        return stream

    def __del__(self):
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
            except:
                pass