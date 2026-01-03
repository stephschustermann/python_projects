#!/usr/bin/env python3
"""
Compare metrics across multiple folders for the same parameter configuration.
Each configuration will produce one comparison plot showing all approaches.
"""

import matplotlib.pyplot as plt
import sys
import os
import glob


def parse_snapshot_file(filepath, access_rate):
    """Parse a snapshot file and extract all requested metrics.
    
    Args:
        filepath: Path to the snapshot file
        access_rate: Number of accesses per day (100 or 500)
    """
    
    times = []
    lost_percent = []
    wet_tubes_pct = []
    objects_in_cache_pct = []
    tubes_expired_by_time = []
    tubes_expired_by_reads = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Read the header to get maximum_time_in_simulation
        header_line = lines[1]
        header_parts = header_line.strip().split(', ')
        max_time_simulation = float(header_parts[2])  # maximum_time_in_simulation in days
        
        # Skip the first 2 header lines and the column headers (line 3)
        for line in lines[3:]:
            parts = line.strip().split(', ')
            if len(parts) < 21:
                continue
            
            try:
                # time_stamp is the snapshot number representing number of accesses
                snapshot_num = int(parts[0])
                lost_pct = float(parts[9])
                expired_time = int(parts[12])
                expired_reads = int(parts[13])
                wet_pct = float(parts[14])
                cache_pct = float(parts[16])
                
                # Convert to years:
                # Snapshots taken every 365 accesses
                # accessRate is accesses per day
                # So: days = accesses / accessRate
                # And: years = days / 365
                days = snapshot_num / float(access_rate)
                years = days / 365.0
                
                times.append(years)
                lost_percent.append(lost_pct)
                wet_tubes_pct.append(wet_pct)
                objects_in_cache_pct.append(cache_pct)
                tubes_expired_by_time.append(expired_time)
                tubes_expired_by_reads.append(expired_reads)
            except (ValueError, IndexError) as e:
                continue
    
    return (times, lost_percent, wet_tubes_pct, objects_in_cache_pct, 
            tubes_expired_by_time, tubes_expired_by_reads)


def find_matching_files(folders, pattern):
    """Find files matching the pattern in each folder."""
    files = {}
    for folder_name, folder_path in folders.items():
        matching = glob.glob(os.path.join(folder_path, f"*{pattern}*.txt"))
        if matching:
            files[folder_name] = matching[0]
    return files


def get_short_name(folder_name):
    """Convert folder name to short display name."""
    name_map = {
        'triplets_clustered_random_small_cluster_expiration': 'Triplets Clustered',
        'triplets_copysets_expiration': 'Triplets Copysets',
        'triplets_random_expiration': 'Triplets Random',
        'tube_replication_small_cluster_expiration': 'Tube Replication'
    }
    return name_map.get(folder_name, folder_name)


def plot_folder_comparison(files_dict, config_name, output_dir):
    """Create comparison visualization across folders for a given configuration."""
    
    # Colors for each approach
    colors = {
        'triplets_clustered_random_small_cluster_expiration': 'tab:blue',
        'triplets_copysets_expiration': 'tab:orange',
        'triplets_random_expiration': 'tab:green',
        'tube_replication_small_cluster_expiration': 'tab:red'
    }
    
    # Extract access rate from config name
    import re
    match = re.search(r'accessRate[_\s](\d+)', config_name)
    if match:
        access_rate = int(match.group(1))
    else:
        print(f"  Warning: Could not extract access rate from {config_name}, using default 100")
        access_rate = 100
    
    # Parse all files
    data = {}
    for folder_name, filepath in files_dict.items():
        print(f"  Reading {folder_name} (access_rate={access_rate})...")
        parsed = parse_snapshot_file(filepath, access_rate)
        if parsed[0]:  # if we have data
            data[folder_name] = parsed
    
    if not data:
        print(f"  No valid data found for {config_name}")
        return None
    
    # Create figure with 4 subplots (2 rows, 2 columns)
    fig = plt.figure(figsize=(16, 10))
    
    # Overall title
    fig.suptitle(f'Approach Comparison: {config_name}', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Find the maximum time across all datasets
    max_time = max(max(times) for times, _, _, _, _, _ in data.values())
    
    # 1. Lost Objects Percentage
    ax1 = plt.subplot(2, 2, 1)
    for folder_name, (times, lost_percent, _, _, _, _) in data.items():
        ax1.plot(times, lost_percent, color=colors[folder_name], 
                linewidth=1.2, alpha=0.9, label=get_short_name(folder_name))
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', fontsize=12)
    ax1.set_title('Lost Objects Percentage Over Time', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=10)
    ax1.set_xlim(0, max_time * 1.05)
    ax1.set_ylim(0, 110)
    
    # 2. Wet Tubes Percentage
    ax2 = plt.subplot(2, 2, 2)
    for folder_name, (times, _, wet_tubes_pct, _, _, _) in data.items():
        ax2.plot(times, wet_tubes_pct, color=colors[folder_name], 
                linewidth=1.2, alpha=0.9, label=get_short_name(folder_name))
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=12)
    ax2.set_title('Wet Tubes Percentage Over Time', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best', fontsize=10)
    ax2.set_xlim(0, max_time * 1.05)
    ax2.set_ylim(0, 110)
    
    # 3. Objects in Cache Percentage
    ax3 = plt.subplot(2, 2, 3)
    for folder_name, (times, _, _, objects_in_cache_pct, _, _) in data.items():
        ax3.plot(times, objects_in_cache_pct, color=colors[folder_name], 
                linewidth=1.2, alpha=0.9, label=get_short_name(folder_name))
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=12)
    ax3.set_title('Objects in Cache Percentage Over Time', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='best', fontsize=10)
    ax3.set_xlim(0, max_time * 1.05)
    # Find max cache value across all approaches
    max_cache = max(max(cache_pct) for _, _, _, cache_pct, _, _ in data.values())
    ax3.set_ylim(0, max(max_cache * 1.1, 0.1))
    
    # 4. Tubes Expired (time as dashed, total as solid)
    ax4 = plt.subplot(2, 2, 4)
    for folder_name, (times, _, _, _, tubes_expired_by_time, tubes_expired_by_reads) in data.items():
        tubes_expired_total = [t + r for t, r in zip(tubes_expired_by_time, tubes_expired_by_reads)]
        # Dashed line for time only
        ax4.plot(times, tubes_expired_by_time, color=colors[folder_name], 
                linewidth=1.0, linestyle='--', alpha=0.6)
        # Solid line for total
        ax4.plot(times, tubes_expired_total, color=colors[folder_name], 
                linewidth=1.2, linestyle='-', alpha=0.9, label=get_short_name(folder_name))
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Tubes Expired (count)', fontsize=12)
    ax4.set_title('Tubes Expired Over Time (solid=total, dashed=by time)', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best', fontsize=10)
    ax4.set_xlim(0, max_time * 1.05)
    # Find max expired value
    max_expired = max(max([t + r for t, r in zip(exp_time, exp_reads)]) 
                     for _, _, _, _, exp_time, exp_reads in data.values())
    if max_expired > 0:
        ax4.set_ylim(0, max_expired * 1.1)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save the figure
    os.makedirs(output_dir, exist_ok=True)
    safe_config_name = config_name.replace(' ', '_').replace('/', '_')
    output_path = os.path.join(output_dir, f'comparison_{safe_config_name}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_path}")
    
    plt.close()
    
    return output_path


def main():
    base_path = '/Users/stephanie.schustermann/tesis/python_projects/input/snaps'
    output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_metrics/folder_comparisons'
    
    # Define folders to compare
    folders = {
        'triplets_clustered_random_small_cluster_expiration': os.path.join(base_path, 'triplets_clustered_random_small_cluster_expiration'),
        'triplets_copysets_expiration': os.path.join(base_path, 'triplets_copysets_expiration'),
        'triplets_random_expiration': os.path.join(base_path, 'triplets_random_expiration'),
        'tube_replication_small_cluster_expiration': os.path.join(base_path, 'tube_replication_small_cluster_expiration')
    }
    
    # Define all configurations to compare
    configs = [
        ('maxReads_100_accessRate_100_dist_Uniform', 'maxReads 100, accessRate 100, Uniform'),
        ('maxReads_100_accessRate_100_dist_Zipf', 'maxReads 100, accessRate 100, Zipf'),
        ('maxReads_100_accessRate_500_dist_Uniform', 'maxReads 100, accessRate 500, Uniform'),
        ('maxReads_100_accessRate_500_dist_Zipf', 'maxReads 100, accessRate 500, Zipf'),
        ('maxReads_500_accessRate_100_dist_Uniform', 'maxReads 500, accessRate 100, Uniform'),
        ('maxReads_500_accessRate_100_dist_Zipf', 'maxReads 500, accessRate 100, Zipf'),
        ('maxReads_500_accessRate_500_dist_Uniform', 'maxReads 500, accessRate 500, Uniform'),
        ('maxReads_500_accessRate_500_dist_Zipf', 'maxReads 500, accessRate 500, Zipf'),
    ]
    
    print(f"Comparing {len(folders)} approaches across {len(configs)} configurations...\n")
    
    generated_plots = []
    for pattern, display_name in configs:
        print(f"Processing: {display_name}")
        files_dict = find_matching_files(folders, pattern)
        
        if len(files_dict) < 2:
            print(f"  Warning: Only found {len(files_dict)} matching files, skipping...")
            continue
        
        output_path = plot_folder_comparison(files_dict, display_name, output_dir)
        if output_path:
            generated_plots.append(output_path)
        print()
    
    print(f"✓ Complete! Generated {len(generated_plots)} comparison plots in:")
    print(f"  {output_dir}")


if __name__ == "__main__":
    main()

