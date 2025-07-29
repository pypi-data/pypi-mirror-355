from __future__ import annotations
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import cv2
import numpy as np
from .exceptions import DatasetError

def parse_coco(annotations_json: Dict) -> Tuple[List[Dict], List[str]]:
    if not isinstance(annotations_json, dict):
        raise DatasetError("Annotations must be a dictionary")

    for key in ["images", "annotations", "categories"]:
        if key not in annotations_json:
            raise DatasetError(f"Missing key '{key}' in COCO annotations")

    if not annotations_json["images"] or not annotations_json["categories"]:
        raise DatasetError("Images or categories list is empty")

    categories = sorted(annotations_json["categories"], key=lambda x: x["id"])
    classes = [cat["name"] for cat in categories]
    cat_id_to_idx = {cat["id"]: idx for idx, cat in enumerate(categories)}

    anns_by_image = {}
    for ann in annotations_json["annotations"]:
        if "image_id" in ann and "category_id" in ann and "bbox" in ann:
            image_id = ann["image_id"]
            anns_by_image.setdefault(image_id, []).append(ann)

    per_image = []
    for img_info in annotations_json["images"]:
        img_id = img_info["id"]
        boxes, labels = [], []

        for ann in anns_by_image.get(img_id, []):
            try:
                x, y, w, h = ann["bbox"]
                x1, y1, x2, y2 = x, y, x + w, y + h

                if x2 <= x1 or y2 <= y1 or x1 < 0 or y1 < 0:
                    continue

                if "width" in img_info and "height" in img_info:
                    img_w, img_h = img_info["width"], img_info["height"]
                    if x2 > img_w or y2 > img_h:
                        x2 = min(x2, img_w)
                        y2 = min(y2, img_h)
                        if x2 <= x1 or y2 <= y1:
                            continue

                category_id = ann["category_id"]
                if category_id in cat_id_to_idx:
                    boxes.append([x1, y1, x2, y2])
                    labels.append(cat_id_to_idx[category_id])
            except:
                continue

        per_image.append({
            "file_name": img_info.get("file_name", f"image_{img_id}"),
            "boxes": boxes,
            "labels": labels
        })

    if not classes:
        raise DatasetError("No valid classes found")

    return per_image, classes

def create_yolo_dataset_files(
    images: List[Union[str, bytes, np.ndarray]],
    annotations: List[Dict[str, Any]],
    classes: List[str],
    output_dir: Path,
    image_size: int = 640
) -> str:
    train_img_dir = output_dir / "images" / "train"
    val_img_dir = output_dir / "images" / "val"
    train_lbl_dir = output_dir / "labels" / "train"
    val_lbl_dir = output_dir / "labels" / "val"

    for directory in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    data_pairs = list(zip(images, annotations))
    random.shuffle(data_pairs)

    split_idx = int(len(data_pairs) * 0.8)
    train_pairs = data_pairs[:split_idx] if split_idx > 0 else data_pairs
    val_pairs = data_pairs[split_idx:] if len(data_pairs) > 1 else data_pairs[:1]

    def process_pairs(pairs, img_dir, lbl_dir):
        processed = 0
        for idx, (img, ann) in enumerate(pairs):
            try:
                if isinstance(img, str):
                    img_path = Path(img)
                    if not img_path.exists():
                        continue
                    img_array = cv2.imread(str(img_path))
                    if img_array is None:
                        continue
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                    filename = img_path.stem
                elif isinstance(img, bytes):
                    buf = np.frombuffer(img, dtype=np.uint8)
                    img_array = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                    if img_array is None:
                        continue
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                    filename = f"image_{idx:06d}"
                else:
                    img_array = img.copy()
                    if len(img_array.shape) != 3 or img_array.shape[2] != 3:
                        continue
                    filename = f"image_{idx:06d}"

                img_filename = f"{filename}.jpg"
                img_save_path = img_dir / img_filename
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

                if not cv2.imwrite(str(img_save_path), img_bgr):
                    continue

                img_height, img_width = img_array.shape[:2]
                yolo_lines = []

                for box, label in zip(ann.get('boxes', []), ann.get('labels', [])):
                    if 0 <= label < len(classes):
                        x1, y1, x2, y2 = box
                        center_x = (x1 + x2) / 2 / img_width
                        center_y = (y1 + y2) / 2 / img_height
                        width = (x2 - x1) / img_width
                        height = (y2 - y1) / img_height

                        if 0 <= center_x <= 1 and 0 <= center_y <= 1 and 0 < width <= 1 and 0 < height <= 1:
                            yolo_lines.append(f"{label} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")

                lbl_filename = f"{filename}.txt"
                lbl_save_path = lbl_dir / lbl_filename

                with lbl_save_path.open("w") as f:
                    f.write("\n".join(yolo_lines))

                processed += 1
            except:
                continue
        return processed

    train_count = process_pairs(train_pairs, train_img_dir, train_lbl_dir)
    val_count = process_pairs(val_pairs, val_img_dir, val_lbl_dir)

    yaml_content = f"""path: {output_dir.absolute()}
train: images/train
val: images/val
nc: {len(classes)}
names: {classes}
"""

    yaml_path = output_dir / "data.yaml"
    with yaml_path.open("w", encoding="utf-8") as f:
        f.write(yaml_content)

    return str(yaml_path)