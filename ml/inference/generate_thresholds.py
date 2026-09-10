from pathlib import Path
import json
import random

import cv2
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\VisionInspectAI\ml")

DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"
OUTPUT_FILE = BASE_DIR / "inference" / "thresholds.json"


# ============================================================
# SETTINGS
# ============================================================

IMAGE_SIZE = 256
RANDOM_SEED = 42

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# CATEGORIES
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
# AUTOENCODER
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1),
            nn.ReLU(),

            nn.Conv2d(32, 64, 3, 2, 1),
            nn.ReLU(),

            nn.Conv2d(64, 128, 3, 2, 1),
            nn.ReLU(),

            nn.Conv2d(128, 256, 3, 2, 1),
            nn.ReLU()
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(
                256, 128, 3, 2, 1,
                output_padding=1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                128, 64, 3, 2, 1,
                output_padding=1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                64, 32, 3, 2, 1,
                output_padding=1
            ),
            nn.ReLU(),

            nn.ConvTranspose2d(
                32, 3, 3, 2, 1,
                output_padding=1
            ),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


# ============================================================
# IMAGE LOADING
# ============================================================

def load_image(image_path):

    image = cv2.imread(str(image_path))

    if image is None:
        return None

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = cv2.resize(
        image,
        (IMAGE_SIZE, IMAGE_SIZE)
    )

    image = image.astype(
        np.float32
    ) / 255.0

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    tensor = torch.from_numpy(image).float()

    return tensor.unsqueeze(0)


# ============================================================
# RECONSTRUCTION ERROR
# ============================================================

def reconstruction_error(model, image_path):

    image = load_image(image_path)

    if image is None:
        return None

    image = image.to(DEVICE)

    with torch.no_grad():
        reconstructed = model(image)

        error = torch.mean(
            (image - reconstructed) ** 2
        ).item()

    return error


# ============================================================
# IMAGE FILES
# ============================================================

def get_images(folder):

    if not folder.exists():
        return []

    extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp"
    }

    return sorted(
        [
            file
            for file in folder.iterdir()
            if file.is_file()
            and file.suffix.lower() in extensions
        ]
    )


# ============================================================
# FIND BEST THRESHOLD
# ============================================================

def find_best_threshold(errors, labels):

    errors = np.asarray(errors)
    labels = np.asarray(labels)

    minimum = float(errors.min())
    maximum = float(errors.max())

    thresholds_to_test = np.linspace(
        minimum,
        maximum,
        500
    )

    best_threshold = minimum
    best_f1 = -1.0

    for threshold in thresholds_to_test:

        predictions = (
            errors > threshold
        ).astype(int)

        score = f1_score(
            labels,
            predictions,
            zero_division=0
        )

        if score > best_f1:
            best_f1 = score
            best_threshold = float(threshold)

    return best_threshold, best_f1


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("VISIONINSPECT AI")
    print("AUTOENCODER THRESHOLD GENERATION")
    print("=" * 70)

    print("\nDevice:", DEVICE)
    print("Image size:", IMAGE_SIZE)

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    torch.manual_seed(RANDOM_SEED)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    thresholds = {}

    # ========================================================
    # PROCESS ALL CATEGORIES
    # ========================================================

    for index, category in enumerate(
        CATEGORIES,
        start=1
    ):

        print("\n" + "=" * 70)
        print(
            f"[{index}/15] {category.upper()}"
        )
        print("=" * 70)

        model_path = (
            MODEL_DIR
            / f"{category}_autoencoder.pth"
        )

        test_dir = (
            DATASET_DIR
            / category
            / "test"
        )

        if not model_path.exists():

            print("MODEL NOT FOUND:")
            print(model_path)

            continue

        if not test_dir.exists():

            print("TEST DIRECTORY NOT FOUND:")
            print(test_dir)

            continue

        # ----------------------------------------------------
        # Load Autoencoder
        # ----------------------------------------------------

        print("Loading model...")

        model = ConvAutoencoder().to(DEVICE)

        state_dict = torch.load(
            model_path,
            map_location=DEVICE
        )

        model.load_state_dict(state_dict)

        model.eval()

        print("Model loaded successfully.")

        # ----------------------------------------------------
        # Get good images
        # ----------------------------------------------------

        good_dir = test_dir / "good"

        good_images = get_images(good_dir)

        # ----------------------------------------------------
        # Get defect images
        # ----------------------------------------------------

        defect_images = []

        for folder in sorted(test_dir.iterdir()):

            if not folder.is_dir():
                continue

            if folder.name == "good":
                continue

            defect_images.extend(
                get_images(folder)
            )

        print(
            "Good images   :",
            len(good_images)
        )

        print(
            "Defect images :",
            len(defect_images)
        )

        if not good_images or not defect_images:

            print("Not enough data. Skipping.")

            continue

        # ====================================================
        # CREATE LABELED DATA
        # ====================================================

        all_images = []

        for image_path in good_images:
            all_images.append(
                (image_path, 0)
            )

        for image_path in defect_images:
            all_images.append(
                (image_path, 1)
            )

        # ----------------------------------------------------
        # Shuffle
        # ----------------------------------------------------

        rng = random.Random(
            RANDOM_SEED
        )

        rng.shuffle(all_images)

        # ====================================================
        # 50 / 50 SPLIT
        # ====================================================

        split_index = len(all_images) // 2

        validation_data = (
            all_images[:split_index]
        )

        holdout_data = (
            all_images[split_index:]
        )

        print(
            "Validation images :",
            len(validation_data)
        )

        print(
            "Holdout images    :",
            len(holdout_data)
        )

        # ====================================================
        # VALIDATION ERRORS
        # ====================================================

        validation_errors = []
        validation_labels = []

        print("Calculating validation errors...")

        for image_path, label in validation_data:

            error = reconstruction_error(
                model,
                image_path
            )

            if error is None:
                continue

            validation_errors.append(error)
            validation_labels.append(label)

        if (
            len(validation_errors) == 0
            or len(set(validation_labels)) < 2
        ):

            print("Invalid validation data.")

            continue

        # ====================================================
        # FIND THRESHOLD
        # ====================================================

        threshold, validation_f1 = (
            find_best_threshold(
                validation_errors,
                validation_labels
            )
        )

        # ====================================================
        # HOLDOUT EVALUATION
        # ====================================================

        holdout_errors = []
        holdout_labels = []

        for image_path, label in holdout_data:

            error = reconstruction_error(
                model,
                image_path
            )

            if error is None:
                continue

            holdout_errors.append(error)
            holdout_labels.append(label)

        holdout_f1 = 0.0

        if (
            len(holdout_errors) > 0
            and len(set(holdout_labels)) >= 2
        ):

            holdout_predictions = (
                np.asarray(holdout_errors)
                > threshold
            ).astype(int)

            holdout_f1 = f1_score(
                holdout_labels,
                holdout_predictions,
                zero_division=0
            )

        # ====================================================
        # SAVE RESULT
        # ====================================================

        thresholds[category] = {
            "threshold": round(
                threshold,
                8
            ),
            "validation_f1": round(
                validation_f1,
                4
            ),
            "holdout_f1": round(
                holdout_f1,
                4
            )
        }

        print("\nRESULT")
        print("-" * 50)
        print(
            f"Threshold    : {threshold:.8f}"
        )
        print(
            f"Validation F1: {validation_f1:.4f}"
        )
        print(
            f"Holdout F1   : {holdout_f1:.4f}"
        )
        print("-" * 50)

    # ========================================================
    # SAVE JSON
    # ========================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            thresholds,
            file,
            indent=4
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("THRESHOLD GENERATION COMPLETED")
    print("=" * 70)

    print(
        f"\nCompleted: {len(thresholds)}/15"
    )

    for category, values in thresholds.items():

        print(
            f"{category:<15} "
            f"threshold={values['threshold']:.8f} "
            f"validation_F1={values['validation_f1']:.4f} "
            f"holdout_F1={values['holdout_f1']:.4f}"
        )

    print("\nSaved to:")
    print(OUTPUT_FILE)

    print("=" * 70)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()