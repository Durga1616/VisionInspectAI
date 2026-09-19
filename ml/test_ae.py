from pathlib import Path

import cv2
import numpy as np
import torch

from inference.inspection_pipeline import ConvAutoencoder, DEVICE


MODEL_PATH = "saved_models/bottle_autoencoder.pth"
IMAGE_DIR = Path("dataset/bottle/train/good")
THRESHOLD = 0.00195363


def preprocess(image_path):
    image = cv2.imread(str(image_path))

    image = cv2.resize(image, (224, 224))

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = image.astype(np.float32) / 255.0

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    tensor = torch.from_numpy(image).float()

    return tensor.unsqueeze(0).to(DEVICE)


model = ConvAutoencoder().to(DEVICE)

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )
)

model.eval()

files = sorted(
    IMAGE_DIR.glob("*.png")
)

errors = []

for image_path in files:

    image = preprocess(image_path)

    with torch.no_grad():

        reconstructed = model(image)

        error = torch.mean(
            (image - reconstructed) ** 2
        ).item()

    errors.append(error)


print("=" * 60)
print("BOTTLE AUTOENCODER - TRAINING GOOD IMAGES")
print("=" * 60)

print("Images :", len(errors))
print("Min    :", f"{min(errors):.8f}")
print("Max    :", f"{max(errors):.8f}")
print("Mean   :", f"{np.mean(errors):.8f}")
print("Median :", f"{np.median(errors):.8f}")
print("Threshold :", f"{THRESHOLD:.8f}")

false_positives = sum(
    error > THRESHOLD
    for error in errors
)

print(
    "Above threshold :",
    false_positives
)

print("=" * 60)