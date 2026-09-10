import cv2
import numpy as np
from pathlib import Path


# ==========================================
# CONFIGURATION
# ==========================================

IMAGE_SIZE = (224, 224)


# ==========================================
# IMAGE PREPROCESSING FUNCTION
# ==========================================

def preprocess_image(input_path, output_path):

    # Read image
    image = cv2.imread(str(input_path))

    if image is None:
        raise ValueError(
            f"Could not read image: {input_path}"
        )

    # Resize image
    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    # Convert BGR to RGB
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # Normalize pixel values
    # 0-255 → 0-1
    normalized = (
        image.astype(np.float32) / 255.0
    )

    # Convert normalized image back to
    # 8-bit format for saving
    processed = (
        normalized * 255
    ).astype(np.uint8)

    # Create output directory
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Convert RGB → BGR
    # because OpenCV saves images in BGR
    processed_bgr = cv2.cvtColor(
        processed,
        cv2.COLOR_RGB2BGR
    )

    # Save processed image
    success = cv2.imwrite(
        str(output_path),
        processed_bgr
    )

    if not success:
        raise IOError(
            f"Could not save image: {output_path}"
        )

    # Return normalized image
    return normalized


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    # ======================================
    # PROJECT ROOT
    # ======================================

    # Project structure:
    #
    # D:\VisionInspectAI
    # ├── ml
    # │   ├── dataset
    # │   └── preprocessing
    # │       └── preprocess.py
    #
    # parents[2] gives:
    # D:\VisionInspectAI

    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )


    # ======================================
    # DATASET DIRECTORY
    # ======================================

    dataset_dir = (
        project_root
        / "ml"
        / "dataset"
    )


    # ======================================
    # OUTPUT DIRECTORY
    # ======================================

    output_dir = (
        project_root
        / "ml"
        / "processed"
    )


    # ======================================
    # BOTTLE CATEGORY
    # ======================================

    bottle_dir = (
        dataset_dir
        / "bottle"
    )


    # ======================================
    # TRAINING DATA
    # ======================================

    # MVTec AD training images are
    # normal/good images.

    train_good_dir = (
        bottle_dir
        / "train"
        / "good"
    )


    # ======================================
    # CHECK DIRECTORY
    # ======================================

    if not train_good_dir.exists():

        raise FileNotFoundError(
            f"Training directory not found: "
            f"{train_good_dir}"
        )


    # ======================================
    # FIND PNG IMAGES
    # ======================================

    images = list(
        train_good_dir.glob("*.png")
    )


    # ======================================
    # CHECK IMAGES
    # ======================================

    if not images:

        raise FileNotFoundError(
            f"No training images found in "
            f"{train_good_dir}"
        )


    # ======================================
    # SELECT FIRST IMAGE
    # ======================================

    input_image = images[0]


    # ======================================
    # OUTPUT IMAGE
    # ======================================

    output_image = (
        output_dir
        / "bottle_sample.png"
    )


    # ======================================
    # PREPROCESS IMAGE
    # ======================================

    normalized = preprocess_image(
        input_image,
        output_image
    )


    # ======================================
    # DISPLAY RESULTS
    # ======================================

    print()
    print("================================")
    print("MVTec AD PREPROCESSING SUCCESS")
    print("================================")

    print(
        f"Input image : {input_image}"
    )

    print(
        f"Output image: {output_image}"
    )

    print(
        f"Image size  : "
        f"{IMAGE_SIZE[0]} x "
        f"{IMAGE_SIZE[1]}"
    )

    print(
        f"Pixel range : "
        f"{normalized.min():.2f} - "
        f"{normalized.max():.2f}"
    )

    print(
        f"Data type   : "
        f"{normalized.dtype}"
    )

    print(
        f"Total training images available: "
        f"{len(images)}"
    )

    print("================================")