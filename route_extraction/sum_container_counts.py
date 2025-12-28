# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "matplotlib",
#     "numpy",
#     "scipy"
# ]
# ///

import pandas as pd
from pathlib import Path


DATA_DIR = Path('../../NB_hackathon_2025-main/Nilufer_bin_collection_dataset')
GPS_DATA_PATH = DATA_DIR / 'container_counts.csv'

containers = pd.read_csv(GPS_DATA_PATH)

sum = 0
for idx in containers.index:
    row = containers.loc[idx]
    r = row.to_dict().values()
    sum += float(list(r)[-1].split(";")[-1])

print("Total container count:", sum)