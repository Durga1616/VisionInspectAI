import cv2
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"

CATEGORIES = ["bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather", "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper"]
IMAGE_SIZE = (224, 224)

class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(64, 128, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(128, 256, 3, 2, 1), nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 3, 2, 1, output_padding=1), nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 3, 2, 1, output_padding=1), nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 3, 2, 1, output_padding=1), nn.ReLU(),
            nn.ConvTranspose2d(32, 3, 3, 2, 1, output_padding=1), nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

def load_image(path):
    image = cv2.imread(str(path))
    if image is None:
        return None
    image = cv2.resize(image, IMAGE_SIZE)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))
    return torch.tensor(image, dtype=torch.float32).unsqueeze(0)

def reconstruction_error(model, path, device):
    image = load_image(path)
    if image is None:
        return None
    image = image.to(device)
    with torch.no_grad():
        reconstructed = model(image)
        return torch.mean((image - reconstructed) ** 2).item()

def calculate_threshold(model, category, device):
    train_dir = DATASET_DIR / category / "train" / "good"
    scores = []
    for path in sorted(train_dir.glob("*.png")):
        score = reconstruction_error(model, path, device)
        if score is not None:
            scores.append(score)
    if not scores:
        return None
    return float(np.mean(scores) + 2 * np.std(scores))

def evaluate_category(category, device):
    print()
    print("=" * 70)
    print(f"EVALUATING: {category.upper()}")
    print("=" * 70)

    model_path = MODEL_DIR / f"{category}_autoencoder.pth"
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return None

    model = ConvAutoencoder().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print("Model loaded successfully.")

    threshold = calculate_threshold(model, category, device)
    if threshold is None:
        print("Could not calculate threshold.")
        return None

    print(f"Anomaly threshold: {threshold:.6f}")

    test_dir = DATASET_DIR / category / "test"
    good_files = sorted((test_dir / "good").glob("*.png"))
    defect_dirs = sorted([p for p in test_dir.iterdir() if p.is_dir() and p.name != "good"])

    y_true, y_pred = [], []

    print(f"Good test images: {len(good_files)}")
    for path in good_files:
        score = reconstruction_error(model, path, device)
        if score is not None:
            y_true.append(0)
            y_pred.append(1 if score > threshold else 0)

    defect_count = 0
    for defect_dir in defect_dirs:
        files = sorted(defect_dir.glob("*.png"))
        defect_count += len(files)
        for path in files:
            score = reconstruction_error(model, path, device)
            if score is not None:
                y_true.append(1)
                y_pred.append(1 if score > threshold else 0)

    print(f"Defect test images: {defect_count}")

    result = {
        "category": category,
        "threshold": threshold,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }

    print(f"Accuracy  : {result['accuracy']:.4f}")
    print(f"Precision : {result['precision']:.4f}")
    print(f"Recall    : {result['recall']:.4f}")
    print(f"F1 Score  : {result['f1']:.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    return result

def main():
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("ALL-CATEGORY AUTOENCODER EVALUATION")
    print("=" * 70)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    results = []
    for category in CATEGORIES:
        result = evaluate_category(category, device)
        if result is not None:
            results.append(result)

    print()
    print("=" * 90)
    print("FINAL AUTOENCODER RESULTS")
    print("=" * 90)
    print(f"{'Category':<15}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1':<12}")
    print("-" * 90)

    for r in results:
        print(f"{r['category']:<15}{r['accuracy']:<12.4f}{r['precision']:<12.4f}{r['recall']:<12.4f}{r['f1']:<12.4f}")

    print("=" * 90)

if __name__ == "__main__":
    main()
