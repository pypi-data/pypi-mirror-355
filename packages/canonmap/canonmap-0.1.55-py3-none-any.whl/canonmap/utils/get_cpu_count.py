import multiprocessing

from canonmap.utils.logger import get_logger

logger = get_logger()

def get_cpu_count():
    count = multiprocessing.cpu_count()
    logger.info(f"Detected {count} CPU cores for parallel processing.")
    return count