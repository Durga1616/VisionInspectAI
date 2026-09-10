import os
import sys
import uuid
import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)

from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.connection import get_db
from models.inspection import Inspection


# ============================================================
# ML PIPELINE IMPORT
# ============================================================

# Path to D:\VisionInspectAI\ml
ML_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "ml"
    )
)

if ML_DIR not in sys.path:
    sys.path.append(ML_DIR)


try:

    from inference.inspection_pipeline import (
        inspect_image
    )

except Exception as error:

    print(
        f"ML pipeline import error: {error}"
    )

    inspect_image = None


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"]
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "uploads"
    )
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}


# ============================================================
# UPLOAD + ML INSPECTION
# ============================================================

@router.post("/upload")
async def upload_inspection_image(

    file: UploadFile = File(...),

    category: str = "bottle",

    current_user: dict = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )
):

    # --------------------------------------------------------
    # Validate image type
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPEG, PNG and WEBP "
                "images are allowed"
            )
        )


    # --------------------------------------------------------
    # Validate category
    # --------------------------------------------------------

    category = (
        category
        .lower()
        .strip()
    )

    allowed_categories = [

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


    if category not in allowed_categories:

        raise HTTPException(

            status_code=400,

            detail=(
                f"Invalid category '{category}'. "
                f"Available categories: "
                f"{allowed_categories}"
            )
        )


    # --------------------------------------------------------
    # Generate unique filename
    # --------------------------------------------------------

    extension = os.path.splitext(
        file.filename
    )[1].lower()


    stored_filename = (
        f"{uuid.uuid4()}{extension}"
    )


    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )


    # --------------------------------------------------------
    # Read uploaded image
    # --------------------------------------------------------

    contents = await file.read()


    if len(contents) == 0:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )


    # --------------------------------------------------------
    # Save image
    # --------------------------------------------------------

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(
            contents
        )


    # --------------------------------------------------------
    # Create inspection record
    # --------------------------------------------------------

    inspection = Inspection(

        filename=file.filename,

        stored_filename=stored_filename,

        user_id=int(
            current_user["user_id"]
        ),

        role=current_user["role"],

        status="processing",

        result=None
    )


    db.add(
        inspection
    )

    db.commit()

    db.refresh(
        inspection
    )


    # ========================================================
    # RUN ML PIPELINE
    # ========================================================

    if inspect_image is None:

        inspection.status = "failed"

        inspection.result = json.dumps({

            "error":
                "ML inspection pipeline "
                "could not be imported"
        })

        db.commit()

        raise HTTPException(

            status_code=500,

            detail=(
                "ML inspection pipeline "
                "is unavailable"
            )
        )


    try:

        # ----------------------------------------------------
        # Autoencoder → YOLO → ResNet18
        # → Severity → PASS/FAIL
        # ----------------------------------------------------

        ml_result = inspect_image(

            file_path,

            category
        )


        # ----------------------------------------------------
        # Save ML result
        # ----------------------------------------------------

        inspection.status = (
            "completed"
        )

        inspection.result = json.dumps(
            ml_result
        )

        db.commit()

        db.refresh(
            inspection
        )


    except Exception as error:

        inspection.status = (
            "failed"
        )

        inspection.result = json.dumps({

            "error": str(error)

        })

        db.commit()

        raise HTTPException(

            status_code=500,

            detail=(
                f"ML inspection failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message":
            "Inspection completed successfully",

        "inspection_id":
            str(inspection.id),

        "filename":
            inspection.filename,

        "category":
            category,

        "status":
            inspection.status,

        "result":
            ml_result
    }


# ============================================================
# GET INSPECTION HISTORY
# ============================================================

@router.get("/")
def get_inspections(

    current_user: dict = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )
):

    user_id = int(
        current_user["user_id"]
    )


    inspections = (

        db.query(
            Inspection
        )

        .filter(
            Inspection.user_id == user_id
        )

        .order_by(
            Inspection.created_at.desc()
        )

        .all()
    )


    results = []


    for inspection in inspections:

        parsed_result = None


        if inspection.result:

            try:

                parsed_result = json.loads(
                    inspection.result
                )

            except Exception:

                parsed_result = inspection.result


        results.append({

            "id":
                str(inspection.id),

            "filename":
                inspection.filename,

            "stored_filename":
                inspection.stored_filename,

            "user_id":
                inspection.user_id,

            "role":
                inspection.role,

            "status":
                inspection.status,

            "result":
                parsed_result,

            "created_at":
                inspection.created_at
        })


    return results