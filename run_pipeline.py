import subprocess
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PIPELINES = [
    "pipelines/ingest.py",
    "pipelines/clean.py",
    "pipelines/aggregate.py",
    "pipelines/feature_engineering.py",
    "pipelines/forecast.py",
    "pipelines/recommend.py"
]

def run_pipeline(script_path):
    logger.info(f">>> Running {script_path}...")
    try:
        # Use sys.executable to ensure we use the same python environment
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=True, text=True)
        logger.info(f"Successfully completed {script_path}")
        # Optional: Log the last few lines of output if needed
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_path}:")
        logger.error(e.stderr)
        return False

def main():
    logger.info("Starting UIDAI Load Predictor Pipeline Orchestration")
    
    for pipeline in PIPELINES:
        success = run_pipeline(pipeline)
        if not success:
            logger.error(f"Pipeline failed at {pipeline}. Aborting.")
            sys.exit(1)
            
    logger.info("All pipeline steps completed successfully!")

if __name__ == "__main__":
    main()
