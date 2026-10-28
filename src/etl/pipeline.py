from .transform import run as run_transform
from etl.powerbi_service import refresh_powerbi_dataset_from_env
from dotenv import load_dotenv


load_dotenv()


def run_pipeline(pasta_raw, pasta_processed, pasta_archive):
    """Run the full ingestion pipeline by delegating to the direct execution script.

    This keeps the pipeline as a thin wrapper over the transformation script
    that already knows how to load, normalize, concatenate and save results.
    """

    run_transform(pasta_raw, pasta_processed, pasta_archive)
    
    refresh_powerbi_dataset_from_env()
