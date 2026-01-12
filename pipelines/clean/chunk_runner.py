import pandas as pd
from pathlib import Path
from tqdm import tqdm


def process_csv_with_fallback(
    input_path: Path,
    output_path: Path,
    clean_fn,
    pin_ref,
    chunksize: int = 200_000,
    small_file_threshold: int = 300_000
):
    """
    Automatically switches between:
    - full read (small files)
    - chunked processing (large files)
    """
    if output_path.exists():
        output_path.unlink()

    # Count rows cheaply
    with open(input_path, "r", encoding="utf-8") as f:
        total_rows = sum(1 for _ in f) - 1  # minus header

    print(f"[INFO] Rows detected: {total_rows:,}")

    # -------- SMALL FILE (fallback) --------
    if total_rows <= small_file_threshold:
        print("[MODE] Small file → full in-memory processing")

        df = pd.read_csv(input_path)
        cleaned = clean_fn(df, pin_ref)
        cleaned.to_csv(output_path, index=False)

        print(f"[DONE] Written → {output_path}")
        return

    # -------- LARGE FILE (chunked) --------
    print("[MODE] Large file → chunked processing")

    first_chunk = True
    reader = pd.read_csv(input_path, chunksize=chunksize)

    for chunk in tqdm(
        reader,
        total=(total_rows // chunksize) + 1,
        desc=f"Cleaning {input_path.name}"
    ):
        cleaned = clean_fn(chunk, pin_ref)

        cleaned.to_csv(
            output_path,
            mode="w" if first_chunk else "a",
            index=False,
            header=first_chunk
        )

        first_chunk = False

    print(f"[DONE] Written → {output_path}")
