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

    logger.info("Preprocessing data for swaps and invalid values...")
    pin_df["latitude"] = pd.to_numeric(pin_df["latitude"], errors='coerce')
    pin_df["longitude"] = pd.to_numeric(pin_df["longitude"], errors='coerce')

    # Detect and Fix Swaps (India bounds: Lat 6-38, Long 68-98)
    # We use some buffer: if Lat > 45 (unlikely for India) and Long < 40 (likely Lat)
    swapped_mask = (pin_df["latitude"] > 45) & (pin_df["longitude"] < 40)
    if swapped_mask.any():
        logger.info(f"Fixing {swapped_mask.sum()} swapped coordinates...")
        pin_df.loc[swapped_mask, ["latitude", "longitude"]] = pin_df.loc[swapped_mask, ["longitude", "latitude"]].values

    # Store original but cleaned coords
    pin_df["orig_lat"] = pin_df["latitude"]
    pin_df["orig_lng"] = pin_df["longitude"]

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
    gdf["centroid_lat"] = gdf.centroid.y
    gdf["centroid_lng"] = gdf.centroid.x

    district_geo = gdf[[STATE_COL, DISTRICT_COL, "centroid_lat", "centroid_lng"]].copy()

    # Normalize text for join
    district_geo["state_norm"] = normalize_text(district_geo[STATE_COL])
    district_geo["district_norm"] = normalize_text(district_geo[DISTRICT_COL])

    pin_df["state_norm"] = normalize_text(pin_df["statename"])
    pin_df["district_norm"] = normalize_text(pin_df["district"])

    logger.info("Merging district centroids into pin_district data...")
    merged = pin_df.merge(
        district_geo[["state_norm", "district_norm", "centroid_lat", "centroid_lng"]],
        on=["state_norm", "district_norm"],
        how="left"
    )

    # -------------------------------------------------------------------------
    # COORDINATE RESOLUTION STRATEGY
    # 1. Use Shapefile centroid (highest priority for spatial consistency)
    # 2. If no shapefile match, use original coordinate if valid
    # 3. If neither, fallback to the mean of existing valid coordinates for that district
    # -------------------------------------------------------------------------
    
    logger.info("Resolving final coordinates...")
    
    # Check if coords are in India bounds
    def is_valid_india(lat, lng):
        return (6 <= lat <= 38) and (68 <= lng <= 98)

    merged["is_orig_valid"] = merged.apply(lambda r: is_valid_india(r["orig_lat"], r["orig_lng"]), axis=1)
    
    # Start with centroid
    merged["latitude"] = merged["centroid_lat"]
    merged["longitude"] = merged["centroid_lng"]

    # Fill missing with original if valid
    mask_missing = merged["latitude"].isna()
    merged.loc[mask_missing & merged["is_orig_valid"], "latitude"] = merged.loc[mask_missing & merged["is_orig_valid"], "orig_lat"]
    merged.loc[mask_missing & merged["is_orig_valid"], "longitude"] = merged.loc[mask_missing & merged["is_orig_valid"], "orig_lng"]

    # Fallback to District Mean for remaining NaNs
    mask_still_missing = merged["latitude"].isna()
    if mask_still_missing.any():
        logger.info("Falling back to district-level means for missing coordinates...")
        # Calculate means per district from valid original coords
        dist_means = merged[merged["is_orig_valid"]].groupby(["state_norm", "district_norm"])[["orig_lat", "orig_lng"]].mean()
        
        # This is a bit slow on 165k rows, but manageable
        merged = merged.set_index(["state_norm", "district_norm"])
        merged.update(dist_means.rename(columns={"orig_lat": "latitude", "orig_lng": "longitude"}), overwrite=False)
        merged = merged.reset_index()

    # Drop all internal helper columns
    cols_to_drop = [
        "state_norm", "district_norm", "orig_lat", "orig_lng", 
        "centroid_lat", "centroid_lng", "is_orig_valid"
    ]
    merged.drop(columns=cols_to_drop, inplace=True, errors="ignore")

    logger.info("Saving pin_district_fixed.csv...")
    merged.to_csv(OUTPUT_PATH, index=False)

    logger.info("✅ pin_district_fixed.csv generated successfully")
    logger.info(f"Total rows: {len(merged)}")

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
