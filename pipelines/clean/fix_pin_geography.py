import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

PIN_DISTRICT_PATH = BASE_DIR / "data" / "reference" / "pin_district.csv"
SHAPEFILE_PATH = BASE_DIR / "data" / "reference" / "gis" / "2011_Dist.shp"
OUTPUT_PATH = BASE_DIR / "data" / "reference" / "pin_district_fixed.csv"

# -----------------------------------------------------------------------------
def normalize_text(s: pd.Series) -> pd.Series:
    """Normalize text for reliable joins."""
    return (
        s.astype(str)
         .str.lower()
         .str.strip()
         .str.replace(r"\s+", " ", regex=True)
    )

# -----------------------------------------------------------------------------
def main():
    logger.info("Loading pin_district.csv...")
    pin_df = pd.read_csv(PIN_DISTRICT_PATH)

    required_cols = {"pincode", "district", "statename"}
    if not required_cols.issubset(pin_df.columns):
        raise ValueError(
            f"pin_district.csv must contain columns: {required_cols}"
        )

    logger.info("Loading Census 2011 district shapefile...")
    gdf = gpd.read_file(SHAPEFILE_PATH)

    # ✅ ACTUAL column names from your shapefile
    STATE_COL = "ST_NM"
    DISTRICT_COL = "DISTRICT"

    if STATE_COL not in gdf.columns or DISTRICT_COL not in gdf.columns:
        raise ValueError(
            f"Expected columns '{STATE_COL}' and '{DISTRICT_COL}' not found. "
            f"Found columns: {list(gdf.columns)}"
        )

    # Ensure WGS84
    if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
        logger.info("Reprojecting shapefile to EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)

    logger.info("Computing district centroids...")
    gdf["centroid"] = gdf.geometry.centroid
    gdf["latitude"] = gdf.centroid.y
    gdf["longitude"] = gdf.centroid.x

    district_geo = gdf[[STATE_COL, DISTRICT_COL, "latitude", "longitude"]].copy()

    # Normalize text for join
    district_geo["state_norm"] = normalize_text(district_geo[STATE_COL])
    district_geo["district_norm"] = normalize_text(district_geo[DISTRICT_COL])

    pin_df["state_norm"] = normalize_text(pin_df["statename"])
    pin_df["district_norm"] = normalize_text(pin_df["district"])

    logger.info("Merging district centroids into pin_district data...")
    merged = pin_df.merge(
        district_geo[["state_norm", "district_norm", "latitude", "longitude"]],
        on=["state_norm", "district_norm"],
        how="left"
    )

    # Drop helper columns
    merged.drop(columns=["state_norm", "district_norm"], inplace=True)

    # Overwrite lat/long with centroid values
    merged["latitude"] = merged["latitude_y"]
    merged["longitude"] = merged["longitude_y"]

    merged.drop(
        columns=["latitude_x", "longitude_x", "latitude_y", "longitude_y"],
        inplace=True,
        errors="ignore"
    )

    # Sanity check: India bounds
    invalid = merged[
        (~merged["latitude"].between(6, 38)) |
        (~merged["longitude"].between(68, 98))
    ]

    if len(invalid) > 0:
        logger.warning(
            f"{len(invalid)} rows have invalid coordinates "
            "(likely post-2011 district names)"
        )

    logger.info("Saving pin_district_fixed.csv...")
    merged.to_csv(OUTPUT_PATH, index=False)

    logger.info("✅ pin_district_fixed.csv generated successfully")
    logger.info(f"Total rows: {len(merged)}")

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
