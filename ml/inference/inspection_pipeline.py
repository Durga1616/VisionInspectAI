import json
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

from PIL import Image
from torchvision import models, transforms
from ultralytics import YOLO

from inference.quality_assessment import (
    assess_quality,
    analyze_image_quality
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
YOLO_DIR = BASE_DIR / "yolo"

THRESHOLDS_FILE = (
    BASE_DIR / "inference" / "thresholds.json"
)

MODEL_SELECTION_FILE = (
    BASE_DIR / "classification" / "model_selection.json"
)

CLASSIFICATION_MODELS_DIR = (
    BASE_DIR / "classification" / "saved_models"
)

IMAGE_SIZE = 256

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# SUPPORTED CATEGORIES
# ============================================================

CATEGORIES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper"
]


# ============================================================
# AUTOENCODER ARCHITECTURE
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):

        super().__init__()

        self.encoder = nn.Sequential(

            nn.Conv2d(
                3,
                32,
                3,
                2,
                1
            ),

            nn.ReLU(),

            nn.Conv2d(
                32,
                64,
                3,
                2,
                1
            ),

            nn.ReLU(),

            nn.Conv2d(
                64,
                128,
                3,
                2,
                1
            ),

            nn.ReLU(),

            nn.Conv2d(
                128,
                256,
                3,
                2,
                1
            ),

            nn.ReLU()
        )

        self.decoder = nn.Sequential(

            nn.ConvTranspose2d(
                256,
                128,
                3,
                2,
                1,
                output_padding=1
            ),

            nn.ReLU(),

            nn.ConvTranspose2d(
                128,
                64,
                3,
                2,
                1,
                output_padding=1
            ),

            nn.ReLU(),

            nn.ConvTranspose2d(
                64,
                32,
                3,
                2,
                1,
                output_padding=1
            ),

            nn.ReLU(),

            nn.ConvTranspose2d(
                32,
                3,
                3,
                2,
                1,
                output_padding=1
            ),

            nn.Sigmoid()
        )

    def forward(self, x):

        encoded = self.encoder(x)

        decoded = self.decoder(encoded)

        return decoded


# ============================================================
# LOAD THRESHOLDS
# ============================================================

def load_thresholds():

    if not THRESHOLDS_FILE.exists():

        raise FileNotFoundError(
            f"Threshold file not found:\n"
            f"{THRESHOLDS_FILE}"
        )

    with open(
        THRESHOLDS_FILE,
        "r"
    ) as file:

        thresholds = json.load(file)

    return thresholds


# ============================================================
# GET CATEGORY THRESHOLD
# ============================================================

def get_category_threshold(
    thresholds,
    category
):

    if category not in thresholds:

        raise ValueError(
            f"No threshold found for category: "
            f"{category}"
        )

    value = thresholds[category]

    if isinstance(
        value,
        (int, float)
    ):

        return float(value)

    if isinstance(
        value,
        dict
    ):

        if "threshold" in value:

            return float(
                value["threshold"]
            )

    raise ValueError(
        f"Invalid threshold format for category: "
        f"{category}"
    )


# ============================================================
# LOAD AUTOENCODER
# ============================================================

def load_autoencoder(category):

    model_path = (
        SAVED_MODELS_DIR
        / f"{category}_autoencoder.pth"
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"Autoencoder model not found:\n"
            f"{model_path}"
        )

    model = ConvAutoencoder()

    state_dict = torch.load(
        model_path,
        map_location=DEVICE
    )

    model.load_state_dict(
        state_dict
    )

    model.to(DEVICE)

    model.eval()

    return model


# ============================================================
# PREPROCESS IMAGE FOR AUTOENCODER
# ============================================================

def preprocess_image(image_path):

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            f"Unable to read image:\n"
            f"{image_path}"
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = cv2.resize(
        image,
        (
            IMAGE_SIZE,
            IMAGE_SIZE
        )
    )

    image = (
        image.astype(
            np.float32
        )
        / 255.0
    )

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    image = np.expand_dims(
        image,
        axis=0
    )

    tensor = torch.from_numpy(
        image
    ).to(DEVICE)

    return tensor


# ============================================================
# AUTOENCODER ANOMALY DETECTION
# ============================================================

def detect_anomaly(
    model,
    image_tensor,
    threshold
):

    with torch.no_grad():

        reconstructed = model(
            image_tensor
        )

        error = torch.mean(
            (
                image_tensor
                - reconstructed
            ) ** 2
        ).item()

    if error > threshold:

        status = "DEFECT"

    else:

        status = "GOOD"

    return status, error


# ============================================================
# GET YOLO MODEL PATH
# ============================================================

def get_yolo_model_path(category):

    if category == "bottle":

        path = (
            YOLO_DIR
            / "runs"
            / "bottle_defect_improved"
            / "weights"
            / "best.pt"
        )

    elif category in [
        "toothbrush",
        "transistor",
        "screw"
    ]:

        path = (
            YOLO_DIR
            / "runs"
            / f"{category}_defect_retrained"
            / "weights"
            / "best.pt"
        )

    else:

        path = (
            YOLO_DIR
            / "runs"
            / f"{category}_defect"
            / "weights"
            / "best.pt"
        )

    return path


# ============================================================
# YOLO DEFECT LOCALIZATION
# ============================================================

def localize_defect(
    category,
    image_path
):

    model_path = get_yolo_model_path(
        category
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"YOLO model not found:\n"
            f"{model_path}"
        )

    model = YOLO(
        str(model_path)
    )

    results = model.predict(
        source=str(image_path),

        # Keep high resolution for small manufacturing defects
        imgsz=800,

        # Lower confidence to avoid missing weak defects
        conf=0.05,

        # Remove highly overlapping duplicate boxes
        iou=0.45,

        # Allow multiple defects in one image
        max_det=20,

        verbose=False
    )

    detections = []

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            coordinates = (
                box.xyxy[0]
                .cpu()
                .numpy()
                .tolist()
            )

            confidence = float(
                box.conf[0]
                .cpu()
                .item()
            )

            x1, y1, x2, y2 = coordinates

            if x2 <= x1 or y2 <= y1:
                continue

            detections.append({

                "class": "defect",

                "confidence": round(
                    confidence,
                    4
                ),

                "bbox": {

                    "x1": round(
                        x1,
                        2
                    ),

                    "y1": round(
                        y1,
                        2
                    ),

                    "x2": round(
                        x2,
                        2
                    ),

                    "y2": round(
                        y2,
                        2
                    )
                }
            })

    return detections


# ============================================================
# LOAD MODEL SELECTION
# ============================================================

def load_model_selection():

    if not MODEL_SELECTION_FILE.exists():

        raise FileNotFoundError(
            f"Model selection file not found:\n"
            f"{MODEL_SELECTION_FILE}"
        )

    with open(
        MODEL_SELECTION_FILE,
        "r"
    ) as file:

        selection = json.load(file)

    return selection


# ============================================================
# CREATE RESNET18 CLASSIFIER
# ============================================================

def create_classifier(
    num_classes
):

    model = models.resnet18(
        weights=None
    )

    model.fc = nn.Sequential(

        nn.Dropout(0.3),

        nn.Linear(
            model.fc.in_features,
            num_classes
        )
    )

    return model


# ============================================================
# LOAD RESNET18 CLASSIFIER
# ============================================================

def load_classifier(category):

    model_selection = (
        load_model_selection()
    )

    if category not in model_selection:

        raise ValueError(
            f"No classifier selected for "
            f"category: {category}"
        )

    model_filename = (
        model_selection[category]
    )

    model_path = (
        CLASSIFICATION_MODELS_DIR
        / model_filename
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"Classifier model not found:\n"
            f"{model_path}"
        )

    checkpoint = torch.load(
        model_path,
        map_location=DEVICE
    )

    class_names = checkpoint.get(
        "class_names"
    )

    if not class_names:

        raise ValueError(
            f"class_names not found in classifier "
            f"checkpoint:\n{model_path}"
        )

    model = create_classifier(
        len(class_names)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(DEVICE)

    model.eval()

    return (
        model,
        class_names,
        model_filename
    )


# ============================================================
# CLASSIFIER PREPROCESSING
# ============================================================

classifier_transform = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(

        mean=[
            0.485,
            0.456,
            0.406
        ],

        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# CLASSIFY DEFECT
#
# CHANGE 2:
# Classify the YOLO defect crop instead of the whole image.
# ============================================================

def classify_defect(
    category,
    image_path,
    bbox=None
):

    (
        model,
        class_names,
        model_filename
    ) = load_classifier(
        category
    )

    image = Image.open(
        image_path
    ).convert("RGB")

    # ========================================================
    # CROP DETECTED DEFECT
    # ========================================================

    if bbox is not None:

        x1 = max(
            0,
            int(bbox["x1"])
        )

        y1 = max(
            0,
            int(bbox["y1"])
        )

        x2 = min(
            image.width,
            int(bbox["x2"])
        )

        y2 = min(
            image.height,
            int(bbox["y2"])
        )

        if x2 > x1 and y2 > y1:

            image = image.crop(
                (
                    x1,
                    y1,
                    x2,
                    y2
                )
            )

    image_tensor = (
        classifier_transform(
            image
        )
        .unsqueeze(0)
        .to(DEVICE)
    )

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        confidence, predicted_index = (
            torch.max(
                probabilities,
                dim=1
            )
        )

    predicted_index = (
        predicted_index.item()
    )

    confidence = (
        confidence.item()
    )

    defect_type = class_names[
        predicted_index
    ]

    return {

        "defect_type":
            defect_type,

        "confidence":
            round(
                confidence,
                4
            ),

        "model":
            model_filename
    }


# ============================================================
# COMPLETE INSPECTION PIPELINE
# ============================================================

def inspect_image(
    image_path,
    category
):

    category = (
        category
        .lower()
        .strip()
    )

    if category not in CATEGORIES:

        raise ValueError(
            f"Invalid category: {category}\n"
            f"Available categories: {CATEGORIES}"
        )

    image_path = Path(
        image_path
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found:\n"
            f"{image_path}"
        )

    # ========================================================
    # IMAGE QUALITY ANALYSIS
    # ========================================================

    print()
    print("IMAGE QUALITY ANALYSIS")
    print("-" * 70)

    image_quality = analyze_image_quality(
        image_path
    )

    print(
        f"Resolution : {image_quality['resolution']}"
    )

    print(
        f"Brightness : {image_quality['brightness']}"
    )

    print(
        f"Contrast   : {image_quality['contrast']}"
    )

    print(
        f"Sharpness  : {image_quality['sharpness']}"
    )

    print(
        f"Noise      : {image_quality['noise']}"
    )

    print(
        f"Quality    : {image_quality['quality_score']}"
    )

    print(
        f"Status     : {image_quality['quality_status']}"
    )

    print()
    print("=" * 70)
    print("VISIONINSPECT AI - INSPECTION")
    print("=" * 70)

    print(
        f"Category : {category}"
    )

    print(
        f"Image    : {image_path}"
    )

    print(
        f"Device   : {DEVICE}"
    )


    # ========================================================
    # STEP 1: LOAD THRESHOLD
    # ========================================================

    thresholds = load_thresholds()

    threshold = get_category_threshold(
        thresholds,
        category
    )


    # ========================================================
    # STEP 2: AUTOENCODER
    # ========================================================

    print()
    print("AUTOENCODER")
    print("-" * 70)

    print(
        f"Threshold : {threshold:.8f}"
    )

    autoencoder = load_autoencoder(
        category
    )


    # ========================================================
    # STEP 3: PREPROCESS
    # ========================================================

    image_tensor = preprocess_image(
        image_path
    )


    # ========================================================
    # STEP 4: ANOMALY DETECTION
    # ========================================================

    status, reconstruction_error = (
        detect_anomaly(
            autoencoder,
            image_tensor,
            threshold
        )
    )

    print(
        f"Error     : "
        f"{reconstruction_error:.8f}"
    )

    print(
        f"Decision  : {status}"
    )


    # ========================================================
    # GOOD PRODUCT
    # ========================================================

    if status == "GOOD":

        print()
        print("FINAL RESULT")
        print("-" * 70)

        print(
            "Status       : GOOD"
        )

        print(
            "YOLO         : Not required"
        )

        print(
            "Classifier   : Not required"
        )

        print(
            "Defects      : 0"
        )

        return {

            "category":
                category,

            "status":
                "GOOD",

            "reconstruction_error":
                round(
                    reconstruction_error,
                    8
                ),

            "threshold":
                round(
                    threshold,
                    8
                ),

            "quality_assessment": {

                "severity": {

                    "score": 0,

                    "level": "Low",

                    "components": {

                        "size": 0,

                        "location": 0,

                        "defect_type": 0,

                        "confidence": 0
                    }
                },

                "quality_decision":
                    "PASS",

                "recommendation":
                    "No defect detected. "
                    "Product passes inspection."
            },

            "defects": [],

            "image_quality":
                image_quality
        }


    # ========================================================
    # DEFECT → YOLO
    # ========================================================

    print()
    print("YOLO LOCALIZATION")
    print("-" * 70)

    detections = localize_defect(
        category,
        image_path
    )

    print(
        f"Detections : "
        f"{len(detections)}"
    )

    for index, detection in enumerate(
        detections,
        start=1
    ):

        print()

        print(
            f"Defect {index}"
        )

        print(
            f"Confidence : "
            f"{detection['confidence']}"
        )

        print(
            f"BBox       : "
            f"{detection['bbox']}"
        )


    # ========================================================
    # DEFECT → RESNET18
    #
    # CHANGE 3:
    # Classify every YOLO detection separately.
    # ========================================================

    print()
    print("DEFECT CLASSIFICATION")
    print("-" * 70)

    for index, detection in enumerate(
        detections,
        start=1
    ):

        classification = classify_defect(
            category,
            image_path,
            detection["bbox"]
        )

        detection["defect_type"] = (
            classification["defect_type"]
        )

        detection[
            "classification_confidence"
        ] = (
            classification["confidence"]
        )

        detection[
            "classification_model"
        ] = (
            classification["model"]
        )

        print(
            f"Defect {index}: "
            f"{detection['defect_type']} "
            f"("
            f"{detection['classification_confidence']:.2%}"
            f")"
        )


    # ========================================================
    # QUALITY ASSESSMENT
    # ========================================================

    print()
    print("QUALITY ASSESSMENT")
    print("-" * 70)

    if detections:

        # Assess the most confident detection
        primary_detection = max(
            detections,
            key=lambda d: d["confidence"]
        )

        quality_result = assess_quality(
            image_path,
            primary_detection
        )

    else:

        quality_result = {

            "severity": {

                "score": 0,

                "level": "Low",

                "components": {

                    "size": 0,

                    "location": 0,

                    "defect_type": 0,

                    "confidence": 0
                }
            },

            "quality_decision":
                "FAIL",

            "recommendation":
                "Defect detected but no "
                "location was identified. "
                "Manual inspection required."
        }


    print(
        f"Severity Score : "
        f"{quality_result['severity']['score']}"
    )

    print(
        f"Severity Level : "
        f"{quality_result['severity']['level']}"
    )

    print(
        f"Quality Decision : "
        f"{quality_result['quality_decision']}"
    )

    print(
        f"Recommendation : "
        f"{quality_result['recommendation']}"
    )


    # ========================================================
    # PRIMARY CLASSIFICATION
    # ========================================================

    if detections:

        primary_detection = max(
            detections,
            key=lambda d: d["confidence"]
        )

        primary_defect_type = (
            primary_detection["defect_type"]
        )

        primary_classification_confidence = (
            primary_detection[
                "classification_confidence"
            ]
        )

        primary_classification_model = (
            primary_detection[
                "classification_model"
            ]
        )

    else:

        primary_defect_type = "unknown"

        primary_classification_confidence = 0

        primary_classification_model = None


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("FINAL RESULT")
    print("-" * 70)

    print(
        "Status       : DEFECT"
    )

    print(
        f"Defect count : "
        f"{len(detections)}"
    )

    print(
        f"Defect type  : "
        f"{primary_defect_type}"
    )

    print(
        f"Classification confidence : "
        f"{primary_classification_confidence}"
    )

    print(
        f"Severity      : "
        f"{quality_result['severity']['level']}"
    )

    print(
        f"Severity score: "
        f"{quality_result['severity']['score']}"
    )

    print(
        f"Decision      : "
        f"{quality_result['quality_decision']}"
    )


    return {

        "category":
            category,

        "status":
            "DEFECT",

        "reconstruction_error":
            round(
                reconstruction_error,
                8
            ),

        "threshold":
            round(
                threshold,
                8
            ),

        "classification": {

            "defect_type":
                primary_defect_type,

            "confidence":
                primary_classification_confidence,

            "model":
                primary_classification_model
        },

        "quality_assessment":
            quality_result,

        "defects":
            detections,

        "image_quality":
            image_quality
    }


# ============================================================
# TEST ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("ML INSPECTION PIPELINE TEST")
    print("=" * 70)

    print()
    print("Available categories:")

    for category in CATEGORIES:

        print(
            f" - {category}"
        )

    print()

    category = input(
        "Enter product category: "
    ).strip().lower()

    image_path = input(
        "Enter image path: "
    ).strip().strip('"')

    try:

        result = inspect_image(
            image_path,
            category
        )

        print()
        print("=" * 70)
        print("PIPELINE RESULT")
        print("=" * 70)

        print(
            json.dumps(
                result,
                indent=4
            )
        )

    except Exception as error:

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(error)