# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
#     "matplotlib",
#     "seaborn",
#     "numpy",
#     "scipy",
# ]
# ///

"""Analyze vehicle stop durations and create normal distribution graphs by vehicle type."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = Path('../../NB_hackathon_2025-main/Nilufer_bin_collection_dataset')
GPS_DATA_PATH = DATA_DIR / 'all_merged_data.csv'
FLEET_DATA_PATH = DATA_DIR / 'fleet.csv'


def parse_duration_to_seconds(duration_str):
    """Convert HH:MM:SS to total seconds."""
    try:
        parts = duration_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    except:
        return None


def load_and_prepare_data():
    """Load GPS data and fleet data, merge them."""
    logger.info("Loading GPS data...")
    gps_df = pd.read_csv(GPS_DATA_PATH)
    logger.info(f"✓ Loaded {len(gps_df)} GPS records")

    logger.info("Loading fleet data...")
    fleet_df = pd.read_csv(FLEET_DATA_PATH)
    logger.info(f"✓ Loaded {len(fleet_df)} vehicles")

    # Parse stop duration to seconds
    logger.info("Parsing stop durations...")
    gps_df['stop_duration_seconds'] = gps_df['Duraklama Süresi'].apply(parse_duration_to_seconds)

    # Remove invalid durations
    gps_df = gps_df[gps_df['stop_duration_seconds'].notna()]

    # Filter for short stops only (under 5 minutes = 300 seconds)
    # These are the actual collection stops we want to analyze
    gps_df = gps_df[gps_df['stop_duration_seconds'] < 300]

    # Remove very short stops (< 10 seconds) - likely measurement noise
    gps_df = gps_df[gps_df['stop_duration_seconds'] >= 10]

    # Merge with fleet data to get vehicle types
    logger.info("Merging with fleet data...")
    merged_df = gps_df.merge(
        fleet_df[['vehicle_id', 'vehicle_type']],
        on='vehicle_id',
        how='left'
    )

    logger.info(f"✓ Prepared {len(merged_df)} stop records")
    return merged_df


def create_distribution_plots(df):
    """Create normal distribution plots for each vehicle type."""

    # Get unique vehicle types
    vehicle_types = df['vehicle_type'].unique()
    logger.info(f"\nVehicle types found: {list(vehicle_types)}")

    # Set style
    sns.set_style("whitegrid")

    # Create a figure with subplots for each vehicle type
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Stop Duration Normal Distribution by Vehicle Type (< 5 minutes)',
                 fontsize=16, fontweight='bold')

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    for idx, (vehicle_type, color) in enumerate(zip(sorted(vehicle_types), colors)):
        ax = axes[idx]

        # Filter data for this vehicle type
        type_data = df[df['vehicle_type'] == vehicle_type]['stop_duration_seconds']

        logger.info(f"\n{vehicle_type}:")
        logger.info(f"  Total stops: {len(type_data)}")
        logger.info(f"  Mean duration: {type_data.mean():.1f} seconds")
        logger.info(f"  Median duration: {type_data.median():.1f} seconds")
        logger.info(f"  Std deviation: {type_data.std():.1f} seconds")

        # Fit normal distribution
        mu, std = stats.norm.fit(type_data)

        # Create smooth normal distribution curve
        x = np.linspace(0, 300, 500)
        p = stats.norm.pdf(x, mu, std)

        # Fill under the curve for better visualization
        ax.fill_between(x, p, alpha=0.3, color=color)
        ax.plot(x, p, linewidth=3, color=color,
                label=f'μ = {mu:.1f} sec\nσ = {std:.1f} sec')

        # Add vertical line at mean
        ax.axvline(mu, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Mean')

        # Add labels and title
        ax.set_xlabel('Stop Duration (seconds)', fontsize=11)
        ax.set_ylabel('Probability Density', fontsize=11)
        ax.set_title(f'{vehicle_type}\n(n={len(type_data):,} stops)', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 300)

    plt.tight_layout()

    # Save the plot
    output_path = 'stop_duration_distributions.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"\n✓ Plot saved to {output_path}")

    plt.show()


def create_comparison_plot(df):
    """Create a single plot comparing all vehicle types."""

    fig, ax = plt.subplots(figsize=(12, 7))

    vehicle_types = sorted(df['vehicle_type'].unique())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    for vehicle_type, color in zip(vehicle_types, colors):
        type_data = df[df['vehicle_type'] == vehicle_type]['stop_duration_seconds']

        # Fit normal distribution
        mu, std = stats.norm.fit(type_data)

        # Create smooth normal distribution curve
        x = np.linspace(0, 300, 500)
        p = stats.norm.pdf(x, mu, std)

        # Fill under curve and plot
        ax.fill_between(x, p, alpha=0.2, color=color)
        ax.plot(x, p, color=color, linewidth=3,
                label=f'{vehicle_type}\nμ={mu:.1f} sec, σ={std:.1f} sec (n={len(type_data):,})')

    ax.set_xlabel('Stop Duration (seconds)', fontsize=13)
    ax.set_ylabel('Probability Density', fontsize=13)
    ax.set_title('Stop Duration Normal Distribution Comparison by Vehicle Type (< 5 minutes)',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 300)

    plt.tight_layout()

    # Save the plot
    output_path = 'stop_duration_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"✓ Comparison plot saved to {output_path}")

    plt.show()


def calculate_filter_thresholds(df):
    """Calculate suggested filter thresholds for each vehicle type."""

    logger.info("\n" + "=" * 60)
    logger.info("Suggested Filter Thresholds (Mean ± 2 Std Dev)")
    logger.info("=" * 60)

    for vehicle_type in sorted(df['vehicle_type'].unique()):
        type_data = df[df['vehicle_type'] == vehicle_type]['stop_duration_seconds']

        mean = type_data.mean()
        std = type_data.std()

        # 95% of data falls within ±2 standard deviations in normal distribution
        lower_threshold = max(0, mean - 2 * std)
        upper_threshold = mean + 2 * std

        logger.info(f"\n{vehicle_type}:")
        logger.info(f"  Normal range: {lower_threshold:.1f} - {upper_threshold:.1f} seconds")
        logger.info(f"  Stops outside range are potential outliers")

        # Calculate percentage of outliers
        outliers = type_data[(type_data < lower_threshold) | (type_data > upper_threshold)]
        outlier_pct = (len(outliers) / len(type_data)) * 100
        logger.info(f"  Outliers: {len(outliers)} ({outlier_pct:.1f}%)")

    logger.info("=" * 60)


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("Stop Duration Analysis")
    logger.info("=" * 60)

    # Load and prepare data
    df = load_and_prepare_data()

    # Create distribution plots
    logger.info("\nCreating distribution plots...")
    create_distribution_plots(df)

    # Create comparison plot
    logger.info("\nCreating comparison plot...")
    create_comparison_plot(df)

    # Calculate filter thresholds
    calculate_filter_thresholds(df)

    logger.info("\n" + "=" * 60)
    logger.info("✓ Analysis complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
