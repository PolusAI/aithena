import logging
import asyncio
from sqlalchemy import create_engine
from sqlmodel import Session, select
import os
import orjson
from collections import defaultdict
import time

from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy
from polus.aithena.clinical_aithena.services.transform import transform_study

# Configuration
# Allow overriding via env var for CI/CD
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/clinical_aithena",
)
TRIAL_INFO_PATH = os.getenv(
    "TRIAL_INFO_PATH",
    "/polus1/schaubnj/clinical-aithena/TrialGPT/dataset/trial_info.json",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("validation")


async def validate_trialgpt_replication_full():
    """
    Validate that our transformation pipeline reproduces the TrialGPT dataset format.

    This script iterates over ALL trials in the TrialGPT dataset JSON and compares
    them against transformed records from our local database.
    """
    if not os.path.exists(TRIAL_INFO_PATH):
        logger.error(f"TrialGPT dataset not found at {TRIAL_INFO_PATH}")
        return

    logger.info(f"Loading full dataset from {TRIAL_INFO_PATH}...")
    start_time = time.time()
    try:
        with open(TRIAL_INFO_PATH, "rb") as f:
            ground_truth_map = orjson.loads(f.read())
    except Exception as e:
        logger.error(f"Failed to load TrialGPT dataset: {e}")
        return

    total_trials = len(ground_truth_map)
    logger.info(f"Loaded {total_trials} trials in {time.time() - start_time:.2f}s")

    # Connect to DB
    engine = create_engine(DATABASE_URL)

    matches = 0
    missing_in_db = 0
    transformation_failures = 0
    validation_failures = 0

    # Track specific field failures
    field_failures = defaultdict(int)

    # Batch size for processing
    BATCH_SIZE = 1000

    # Get all NCT IDs from the dataset
    nct_ids = list(ground_truth_map.keys())
    
    logger.info(f"Starting validation of {total_trials} trials...")

    with Session(engine) as session:
        # Process in chunks to avoid massive query
        for i in range(0, len(nct_ids), BATCH_SIZE):
            chunk_ids = nct_ids[i : i + BATCH_SIZE]

            # Fetch batch from DB
            stmt = select(CTGovStudy).where(
                CTGovStudy.nct_id.in_(chunk_ids),
                CTGovStudy.is_latest.is_(True),
            )
            db_studies = session.exec(stmt).all()
            db_map = {s.nct_id: s for s in db_studies}

            for nct_id in chunk_ids:
                ctgov_study = db_map.get(nct_id)

                if not ctgov_study:
                    missing_in_db += 1
                    continue

                # Transform
                transformed = transform_study(ctgov_study)

                if not transformed:
                    transformation_failures += 1
                    continue

                # Compare
                gt = ground_truth_map.get(nct_id)

                # Validate Key Fields
                t_title = transformed.metadata_json.get("brief_title")
                g_title = gt.get("brief_title")

                t_phase = transformed.metadata_json.get("phase")
                g_phase = gt.get("phase") or ""  # Normalize None to empty string
                if t_phase is None:
                    t_phase = ""

                t_drugs = set(transformed.metadata_json.get("drugs_list", []))
                g_drugs = set(gt.get("drugs_list", []))

                errors = []
                if t_title != g_title:
                    errors.append("Title mismatch")
                    field_failures["brief_title"] += 1
                if t_phase != g_phase:
                    errors.append("Phase mismatch")
                    field_failures["phase"] += 1
                if t_drugs != g_drugs:
                    errors.append("Drugs mismatch")
                    field_failures["drugs_list"] += 1

                if not errors:
                    matches += 1
                else:
                    validation_failures += 1

            # Log progress
            processed = min(i + BATCH_SIZE, total_trials)
            if processed % 5000 == 0:
                logger.info(f"Processed {processed}/{total_trials}...")

    # Summary Report
    print("\n=== Validation Summary ===")
    print(f"Total Trials in Dataset: {total_trials}")
    print(f"Matches: {matches} ({matches/total_trials*100:.1f}%)")
    print(f"Missing in DB: {missing_in_db}")
    print(f"Transformation Failed: {transformation_failures}")
    print(f"Validation Failed: {validation_failures}")
    print("\nField Failures:")
    for field, count in field_failures.items():
        print(f"  {field}: {count}")

    total_processed = matches + validation_failures
    if total_processed > 0:
        accuracy = matches / total_processed
        print(f"\nAccuracy on present data: {accuracy*100:.1f}%")
        
        if accuracy > 0.95:
             print("\n✅ VALIDATION PASSED (Accuracy > 95%)")
        else:
             print(f"\n❌ VALIDATION FAILED (Accuracy {accuracy*100:.1f}% < 95%)")
             exit(1)
    else:
        logger.warning("No data found in local DB to validate")


if __name__ == "__main__":
    asyncio.run(validate_trialgpt_replication_full())
