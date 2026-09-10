import cv2
import numpy as np
import torch
import torch.nn as nn

from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"


# ============================================================
# MVTec CATEGORIES
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
    "zipper",
]


# ============================================================
# SETTINGS
# ============================================================

IMAGE_SIZE = (224, 224)

# Percentage of test data used to select threshold
VALIDATION_RATIO = 0.5

# Threshold search range
THRESHOLD_POINTS = 100


# ============================================================
# AUTOENCODER
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):

        super().__init__()

        self.encoder = nn.Sequential(

            nn.Conv2d(
                3, 32,
                kernel_size=3,
                stride=2,
                padding=1
            ),
            nn.ReLU(),

            nn.Conv2d(
                32, 64,
                kernel_size=3,
                stride=2,
                padding=1
            ),
            nn.ReLU(),

            nn.Conv2d(
                64, 128,
                kernel_size=3,
                stride=2,
                padding=1
            ),
            nn.ReLU(),

            nn.Conv2d(
                128, 256,
                kernel_size=3,
                stride=2,
                padding=1
            ),
            nn.ReLU(),
        )

        self.decoder = nn.Sequential(

            nn.ConvTranspose2d(
                256, 128,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                128, 64,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                64, 32,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                32, 3,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.Sigmoid(),
        )

    def forward(self, x):

        encoded = self.encoder(x)

        decoded = self.decoder(encoded)

        return decoded


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def load_image(image_path):

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        return None

    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = image.astype(
        np.float32
    ) / 255.0

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    tensor = torch.tensor(
        image,
        dtype=torch.float32
    )

    return tensor.unsqueeze(0)


# ============================================================
# RECONSTRUCTION ERROR
# ============================================================

def reconstruction_error(
    model,
    image_path,
    device
):

    image = load_image(
        image_path
    )

    if image is None:

        return None

    image = image.to(device)

    with torch.no_grad():

        reconstructed = model(
            image
        )

        error = torch.mean(
            (image - reconstructed) ** 2
        )

    return error.item()


# ============================================================
# COLLECT TEST SCORES
# ============================================================

def collect_test_scores(
    model,
    category,
    device
):

    test_dir = (
        DATASET_DIR
        / category
        / "test"
    )

    samples = []

    # --------------------------------------------------------
    # GOOD IMAGES
    # --------------------------------------------------------

    good_dir = test_dir / "good"

    for image_path in sorted(
        good_dir.glob("*.png")
    ):

        score = reconstruction_error(
            model,
            image_path,
            device
        )

        if score is not None:

            samples.append(
                (score, 0)
            )

    # --------------------------------------------------------
    # DEFECT IMAGES
    # --------------------------------------------------------

    defect_dirs = sorted(
        [
            folder
            for folder in test_dir.iterdir()
            if folder.is_dir()
            and folder.name != "good"
        ]
    )

    for defect_dir in defect_dirs:

        for image_path in sorted(
            defect_dir.glob("*.png")
        ):

            score = reconstruction_error(
                model,
                image_path,
                device
            )

            if score is not None:

                samples.append(
                    (score, 1)
                )

    return samples


# ============================================================
# FIND BEST THRESHOLD
# ============================================================

def find_best_threshold(
    scores,
    labels
):

    minimum = min(scores)

    maximum = max(scores)

    thresholds = np.linspace(
        minimum,
        maximum,
        THRESHOLD_POINTS
    )

    best_threshold = thresholds[0]

    best_f1 = -1.0

    for threshold in thresholds:

        predictions = [
            1 if score > threshold else 0
            for score in scores
        ]

        f1 = f1_score(
            labels,
            predictions,
            zero_division=0
        )

        if f1 > best_f1:

            best_f1 = f1

            best_threshold = threshold

    return best_threshold


# ============================================================
# EVALUATE USING THRESHOLD
# ============================================================

def calculate_metrics(
    scores,
    labels,
    threshold
):

    predictions = [
        1 if score > threshold else 0
        for score in scores
    ]

    accuracy = accuracy_score(
        labels,
        predictions
    )

    precision = precision_score(
        labels,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0
    )

    return (
        accuracy,
        precision,
        recall,
        f1
    )


# ============================================================
# EVALUATE ONE CATEGORY
# ============================================================

def evaluate_category(
    category,
    device
):

    print()
    print("=" * 70)

    print(
        f"OPTIMIZING: {category.upper()}"
    )

    print("=" * 70)

    model_path = (
        MODEL_DIR
        / f"{category}_autoencoder.pth"
    )

    if not model_path.exists():

        print(
            f"MODEL NOT FOUND: {model_path}"
        )

        return None

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    model = ConvAutoencoder().to(
        device
    )

    model.load_state_dict(
        torch.load(
            model_path,
            map_location=device
        )
    )

    model.eval()

    print(
        "Model loaded successfully."
    )

    # --------------------------------------------------------
    # COLLECT SCORES
    # --------------------------------------------------------

    samples = collect_test_scores(
        model,
        category,
        device
    )

    if len(samples) < 4:

        print(
            "Not enough test samples."
        )

        return None

    # --------------------------------------------------------
    # SHUFFLE
    # --------------------------------------------------------

    rng = np.random.default_rng(
        seed=42
    )

    rng.shuffle(samples)

    scores = np.array(
        [item[0] for item in samples]
    )

    labels = np.array(
        [item[1] for item in samples]
    )

    # --------------------------------------------------------
    # SPLIT TEST DATA
    # --------------------------------------------------------

    split_index = int(
        len(samples)
        * VALIDATION_RATIO
    )

    validation_scores = (
        scores[:split_index]
    )

    validation_labels = (
        labels[:split_index]
    )

    test_scores = (
        scores[split_index:]
    )

    test_labels = (
        labels[split_index:]
    )

    print(
        f"Validation samples: "
        f"{len(validation_scores)}"
    )

    print(
        f"Final test samples: "
        f"{len(test_scores)}"
    )

    # --------------------------------------------------------
    # FIND BEST THRESHOLD
    # --------------------------------------------------------

    threshold = find_best_threshold(
        validation_scores,
        validation_labels
    )

    print(
        f"Optimized threshold: "
        f"{threshold:.6f}"
    )

    # --------------------------------------------------------
    # FINAL TEST METRICS
    # --------------------------------------------------------

    (
        accuracy,
        precision,
        recall,
        f1
    ) = calculate_metrics(
        test_scores,
        test_labels,
        threshold
    )

    print()
    print(
        "FINAL HELD-OUT TEST RESULTS"
    )

    print(
        f"Accuracy  : {accuracy:.4f}"
    )

    print(
        f"Precision : {precision:.4f}"
    )

    print(
        f"Recall    : {recall:.4f}"
    )

    print(
        f"F1 Score  : {f1:.4f}"
    )

    return {
        "category": category,
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "VISIONINSPECT AI"
    )

    print(
        "OPTIMIZED AUTOENCODER THRESHOLD EVALUATION"
    )

    print("=" * 70)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"Device: {device}"
    )

    results = []

    # --------------------------------------------------------
    # ALL 15 CATEGORIES
    # --------------------------------------------------------

    for category in CATEGORIES:

        result = evaluate_category(
            category,
            device
        )

        if result is not None:

            results.append(
                result
            )

    # --------------------------------------------------------
    # FINAL TABLE
    # --------------------------------------------------------

    print()
    print("=" * 90)

    print(
        "OPTIMIZED AUTOENCODER RESULTS"
    )

    print("=" * 90)

    print(
        f"{'Category':<15}"
        f"{'Accuracy':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
    )

    print("-" * 90)

    for result in results:

        print(
            f"{result['category']:<15}"
            f"{result['accuracy']:<12.4f}"
            f"{result['precision']:<12.4f}"
            f"{result['recall']:<12.4f}"
            f"{result['f1']:<12.4f}"
        )

    print("=" * 90)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main() 