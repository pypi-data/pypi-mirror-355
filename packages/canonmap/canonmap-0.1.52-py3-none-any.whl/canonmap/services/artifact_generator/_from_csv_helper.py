# canonmap/services/artifact_generator/_from_csv_helper.py

from typing import Optional

import pandas as pd
import chardet

from canonmap.utils.logger import get_logger

logger = get_logger()

def convert_csv_to_df(
        csv_path: str,
        num_rows: Optional[int] = None
):
    logger.info(f"Generating artifact from CSV: {csv_path}")
    df = _load_csv(csv_path)
    if num_rows:
        logger.info(f"Using first {num_rows} rows")
        df = df.head(num_rows)
    return df

def _load_csv(csv_path: str) -> pd.DataFrame:
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1']
    for enc in encodings:
        try:
            return pd.read_csv(csv_path, low_memory=False, encoding=enc)
        except UnicodeDecodeError:
            continue
    # fallback to chardet
    with open(csv_path, 'rb') as f:
        raw_data = f.read()
        detected = chardet.detect(raw_data).get('encoding')
        if detected:
            return pd.read_csv(csv_path, low_memory=False, encoding=detected)
    raise UnicodeDecodeError("utf-8", b'', 0, 1, "Could not decode CSV file")