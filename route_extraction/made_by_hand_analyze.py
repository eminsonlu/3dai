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
GPS_DATA_PATH = DATA_DIR / 'all_merged_data.csv'
FLEET_DATA_PATH = DATA_DIR / 'fleet.csv'

gps = pd.read_csv(GPS_DATA_PATH)
print(f"Loaded {len(gps)} GPS records")

fleets = pd.read_csv(FLEET_DATA_PATH)
print(f"Loaded {len(fleets)} fleet records")

vehicle_type_map = fleets.set_index('vehicle_id')['vehicle_type'].to_dict()

EXCLUDE_BOX = {
    'min_lat': 40.26066348022777,
    'max_lat': 40.27566025613571,
    'min_lon': 28.963931377930944,
    'max_lon': 28.980386759010038
}

def is_in_exclude_box(lat, lon):
    """Verilen koordinat hariç tutulacak kutu içinde mi?"""
    return (EXCLUDE_BOX['min_lat'] <= lat <= EXCLUDE_BOX['max_lat'] and
            EXCLUDE_BOX['min_lon'] <= lon <= EXCLUDE_BOX['max_lon'])

container_points = []

descriptions = gps['Açıklama'].values
stop_times = gps['Duraklama Süresi'].values
vehicle_ids = gps['vehicle_id'].values
enlems = gps['Enlem'].values
boylams = gps['Boylam'].values

def time_to_seconds(time_str):
    try:
        parts = str(time_str).split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except:
        return 0

filtered_count = 0
for idx in range(1, len(gps)):
    current_description = descriptions[idx]
    previous_description = descriptions[idx - 1]

    if current_description == "Hareketli" and previous_description == "Duran":
        current_stop_time_str = stop_times[idx]
        current_stop_time = time_to_seconds(current_stop_time_str)

        if current_stop_time > 60:
            enlem = enlems[idx - 1]
            boylam = boylams[idx - 1]

            if is_in_exclude_box(enlem, boylam):
                filtered_count += 1
                continue

            vehicle_id = vehicle_ids[idx - 1]
            vehicle_type = vehicle_type_map.get(vehicle_id, "Unknown")

            container_points.append({
                'Enlem': enlem,
                'Boylam': boylam,
                'vehicle_type': vehicle_type
            })

print(f"\nToplam konteyner noktası bulundu: {len(container_points)}")
print(f"Filtrelenen (hariç tutulan) nokta sayısı: {filtered_count}")

if container_points:
    container_df = pd.DataFrame(container_points)
    output_path = DATA_DIR / 'container_points.csv'
    container_df.to_csv(output_path, index=False)
    print(f"Konteyner noktaları '{output_path}' dosyasına kaydedildi.")

    print("\nİlk 5 konteyner noktası:")
    print(container_df.head())

    print("\nVehicle type'a göre dağılım:")
    print(container_df['vehicle_type'].value_counts())
else:
    print("Hiç konteyner noktası bulunamadı.")