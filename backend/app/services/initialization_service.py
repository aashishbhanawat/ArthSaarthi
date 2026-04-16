import logging
import shutil
import tempfile
import threading

import urllib3

from app.db.initial_data import seed_interest_rates
from app.db.session import SessionLocal
from app.models import Asset
from app.scripts.backfill_transaction_links import run_backfill
from app.services.asset_seeder import AssetSeeder
from app.utils.financial_utils import download_all_sources, process_all_sources

# Suppress InsecureRequestWarning for NSDL connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def _run_initial_seeding():
    """Actually performs the seeding logic in a thread."""
    from app.api.v1.endpoints.system import SeedingStatus, _seeding_state
    logger.info("Background initial seeding thread started.")
    _seeding_state["status"] = SeedingStatus.IN_PROGRESS
    _seeding_state["progress"] = 10
    _seeding_state["message"] = "Fetching reference instruments lists..."

    db = SessionLocal()
    try:
        # 1. Seed Interest Rates
        seed_interest_rates(db)
        db.commit()

        # 2. Sync Assets
        seeder = AssetSeeder(db=db, debug=False)
        temp_dir = tempfile.mkdtemp()
        try:
            # Use consolidated logic
            files = download_all_sources(temp_dir, logger)
            process_all_sources(seeder, files, logger)

            db.commit()
            _seeding_state["status"] = SeedingStatus.COMPLETE
            _seeding_state["progress"] = 100
            _seeding_state["message"] = (
                "Background initial seeding completed successfully!"
            )
            logger.info("Background initial seeding completed successfully.")
        finally:
            shutil.rmtree(temp_dir)
    except Exception as e:
        _seeding_state["status"] = SeedingStatus.FAILED
        _seeding_state["error"] = str(e)
        logger.error(f"Background initial seeding failed: {e}", exc_info=True)
    finally:
        db.close()

def check_and_seed_on_startup():
    """Checks if database is empty and triggers background seeding if so."""
    from app.api.v1.endpoints.system import SeedingStatus, _seeding_state
    db = SessionLocal()
    try:
        count = db.query(Asset).count()
        if count < 10000:
            logger.info(
                f"Assets table has {count} assets (<10000). "
                "Triggering background seeding..."
            )
            _seeding_state["status"] = SeedingStatus.IN_PROGRESS
            _seeding_state["message"] = "Preparing to download and seed data..."
            threading.Thread(target=_run_initial_seeding, daemon=True).start()
        else:
            logger.info(
                f"Database already has {count} assets. Skipping initial seeding."
            )
            _seeding_state["status"] = SeedingStatus.COMPLETE
            _seeding_state["progress"] = 100
            _seeding_state["message"] = "Asset database ready"

        # Always trigger a background backfill for unlinked transactions if any
        # This ensures data consistency for capital gains reports
        threading.Thread(
            target=run_backfill,
            args=(db,),
            daemon=True
        ).start()
    except Exception as e:
        logger.error(f"Error during startup seeding check: {e}")
    finally:
        db.close()
