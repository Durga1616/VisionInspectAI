from ultralytics import YOLO
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "runs"
    / "bottle_defect_improved"
    / "weights"
    / "best.pt"
)

DATA_YAML = BASE_DIR / "data.yaml"

# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 60)
print("Loading improved YOLO model")
print("=" * 60)

model = YOLO(str(MODEL_PATH))

print("Improved YOLO model loaded successfully!")

# ============================================================
# TEST EVALUATION
# ============================================================

print("\n" + "=" * 60)
print("Evaluating improved YOLO on TEST dataset")
print("=" * 60)

results = model.val(
    data=str(DATA_YAML),
    split="test",
    imgsz=640,
    batch=8
)

# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 60)
print("IMPROVED YOLO TEST RESULTS")
print("=" * 60)

print(f"Precision    : {results.box.mp:.4f}")
print(f"Recall       : {results.box.mr:.4f}")
print(f"mAP@0.5      : {results.box.map50:.4f}")
print(f"mAP@0.5:0.95 : {results.box.map:.4f}")

print("=" * 60)