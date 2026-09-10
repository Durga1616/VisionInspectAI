import cv2
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid",
    "hazelnut", "leather", "metal_nut", "pill", "screw",
    "tile", "toothbrush", "transistor", "wood", "zipper"
]

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 20
LEARNING_RATE = 0.001


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
            nn.ConvTranspose2d(256, 128, 3, 2, 1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 3, 2, 1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 3, 2, 1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 3, 3, 2, 1, output_padding=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def load_good_images(category):
    good_dir = DATASET_DIR / category / "train" / "good"

    if not good_dir.exists():
        print(f"ERROR: Folder not found: {good_dir}")
        return None

    image_files = sorted(good_dir.glob("*.png"))

    if not image_files:
        print(f"ERROR: No PNG images found for {category}")
        return None

    images = []

    for image_file in image_files:
        image = cv2.imread(str(image_file))

        if image is None:
            continue

        image = cv2.resize(image, IMAGE_SIZE)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = image.astype(np.float32) / 255.0
        images.append(image)

    if not images:
        print(f"ERROR: Could not read images for {category}")
        return None

    images = np.array(images, dtype=np.float32)
    images = np.transpose(images, (0, 3, 1, 2))

    return torch.tensor(images, dtype=torch.float32)


def train_category(category, device):
    print()
    print("=" * 70)
    print(f"TRAINING AUTOENCODER: {category.upper()}")
    print("=" * 70)

    data = load_good_images(category)

    if data is None:
        print(f"Skipping {category}")
        return False

    print(f"Training images found: {len(data)}")

    dataset = TensorDataset(data, data)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    model = ConvAutoencoder().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    model.train()

    for epoch in range(EPOCHS):
        total_loss = 0.0

        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        average_loss = total_loss / len(loader)

        print(
            f"Epoch [{epoch + 1}/{EPOCHS}] "
            f"Loss: {average_loss:.6f}"
        )

    model_path = MODEL_DIR / f"{category}_autoencoder.pth"
    torch.save(model.state_dict(), model_path)

    print(f"Model saved at: {model_path}")
    return True


def main():
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("TRAINING AUTOENCODERS FOR ALL MVTec CATEGORIES")
    print("=" * 70)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    successful = 0

    for category in CATEGORIES:
        if train_category(category, device):
            successful += 1

    print()
    print("=" * 70)
    print("ALL AUTOENCODER TRAINING COMPLETED")
    print("=" * 70)
    print(f"Models trained successfully: {successful}/{len(CATEGORIES)}")

    print()
    print("Saved models:")

    for category in CATEGORIES:
        model_path = MODEL_DIR / f"{category}_autoencoder.pth"

        if model_path.exists():
            print(f"[OK] {model_path.name}")
        else:
            print(f"[MISSING] {model_path.name}")


if __name__ == "__main__":
    main()
