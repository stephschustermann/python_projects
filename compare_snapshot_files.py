#!/usr/bin/env python3
"""
Compare two snapshot files side by side with all metrics.
"""

import matplotlib.pyplot as plt
import sys
import os


def parse_snapshot_file(filepath, access_rate=None):
    """Parse a snapshot file and extract all requested metrics.
    
    Args:
        filepath: Path to the snapshot file
        access_rate: Number of accesses per day (if None, will try to extract from filename)
    """
    
    # Try to extract access rate from filename if not provided
    if access_rate is None:
        import re
        match = re.search(r'accessRate[_\s](\d+)', filepath)
        if match:
            access_rate = int(match.group(1))
        else:
            # Default fallback - will use time_stamp as days directly
            access_rate = 1
            print(f"Warning: Could not extract access rate from {filepath}, assuming 1")
    
    times = []
    lost_objects = []
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
                # time_stamp is actually the snapshot number (0, 365, 730, etc.)
                # which represents number of accesses, not days
                snapshot_num = int(parts[0])
                lost_obj = int(parts[8])
                lost_pct = float(parts[9])
                expired_time = int(parts[12])
                expired_reads = int(parts[13])
                wet_pct = float(parts[14])
                cache_pct = float(parts[16])
                
                # Convert snapshot number to years:
                # snapshot_num = number of accesses
                # days = snapshot_num / access_rate
                # years = days / (max_time_simulation / 10)
                days = snapshot_num / access_rate
                years = days / (max_time_simulation / 10.0)
                
                times.append(years)
                lost_objects.append(lost_obj)
                lost_percent.append(lost_pct)
                wet_tubes_pct.append(wet_pct)
                objects_in_cache_pct.append(cache_pct)
                tubes_expired_by_time.append(expired_time)
                tubes_expired_by_reads.append(expired_reads)
            except (ValueError, IndexError) as e:
                continue
    
    return (times, lost_objects, lost_percent, wet_tubes_pct, 
            objects_in_cache_pct, tubes_expired_by_time, tubes_expired_by_reads)


def plot_comparison(data1, data2, file1, file2):
    """Create comparison visualization with 4 subplots comparing both files."""
    
    name1 = os.path.basename(file1).replace('.txt', '')
    name2 = os.path.basename(file2).replace('.txt', '')
    
    times1, _, lost_percent1, wet_tubes_pct1, objects_in_cache_pct1, tubes_expired_by_time1, tubes_expired_by_reads1 = data1
    times2, _, lost_percent2, wet_tubes_pct2, objects_in_cache_pct2, tubes_expired_by_time2, tubes_expired_by_reads2 = data2
    
    # Calculate total expired tubes
    tubes_expired_total1 = [t + r for t, r in zip(tubes_expired_by_time1, tubes_expired_by_reads1)]
    tubes_expired_total2 = [t + r for t, r in zip(tubes_expired_by_time2, tubes_expired_by_reads2)]
    
    # Create figure with 4 subplots (2 rows, 2 columns)
    fig = plt.figure(figsize=(16, 10))
    
    # Overall title
    fig.suptitle(f'Comparison: {name1} vs {name2}', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # 1. Lost Objects Percentage Comparison
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(times1, lost_percent1, color='tab:red', linewidth=1.2, alpha=0.9, label=name1)
    ax1.plot(times2, lost_percent2, color='tab:orange', linewidth=1.2, alpha=0.9, linestyle='--', label=name2)
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', fontsize=12)
    ax1.set_title('Lost Objects Percentage Over Time', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=9)
    ax1.set_xlim(0, max(max(times1), max(times2)))
    ax1.set_ylim(0, 110)
    
    # 2. Wet Tubes Percentage Comparison
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(times1, wet_tubes_pct1, color='tab:blue', linewidth=1.2, alpha=0.9, label=name1)
    ax2.plot(times2, wet_tubes_pct2, color='tab:cyan', linewidth=1.2, alpha=0.9, linestyle='--', label=name2)
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=12)
    ax2.set_title('Wet Tubes Percentage Over Time', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best', fontsize=9)
    ax2.set_xlim(0, max(max(times1), max(times2)))
    ax2.set_ylim(0, 110)
    
    # 3. Objects in Cache Percentage Comparison
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(times1, objects_in_cache_pct1, color='tab:green', linewidth=1.2, alpha=0.9, label=name1)
    ax3.plot(times2, objects_in_cache_pct2, color='darkgreen', linewidth=1.2, alpha=0.9, linestyle='--', label=name2)
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=12)
    ax3.set_title('Objects in Cache Percentage Over Time', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='best', fontsize=9)
    ax3.set_xlim(0, max(max(times1), max(times2)))
    max_cache = max(max(objects_in_cache_pct1), max(objects_in_cache_pct2))
    ax3.set_ylim(0, max_cache * 1.1)
    
    # 4. Tubes Expired Comparison (with both time and total for each file)
    ax4 = plt.subplot(2, 2, 4)
    # File 1 - dashed for time only, solid for total
    ax4.plot(times1, tubes_expired_by_time1, color='tab:red', linewidth=1.2, 
             linestyle='--', alpha=0.7, label=f'{name1} - Expired by Time')
    ax4.plot(times1, tubes_expired_total1, color='tab:red', linewidth=1.2, 
             linestyle='-', alpha=0.9, label=f'{name1} - Total Expired')
    # File 2 - dashed for time only, solid for total
    ax4.plot(times2, tubes_expired_by_time2, color='tab:blue', linewidth=1.2, 
             linestyle='--', alpha=0.7, label=f'{name2} - Expired by Time')
    ax4.plot(times2, tubes_expired_total2, color='tab:blue', linewidth=1.2, 
             linestyle='-', alpha=0.9, label=f'{name2} - Total Expired')
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Tubes Expired (count)', fontsize=12)
    ax4.set_title('Tubes Expired Over Time', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best', fontsize=8)
    ax4.set_xlim(0, max(max(times1), max(times2)))
    max_expired = max(max(tubes_expired_total1), max(tubes_expired_total2))
    if max_expired > 0:
        ax4.set_ylim(0, max_expired * 1.1)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save the figure
    output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_metrics'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'comparison_{name1}_vs_{name2}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Comparison plot saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_snapshot_files.py <snapshot_file1> <snapshot_file2>")
        sys.exit(1)
    
    filepath1 = sys.argv[1]
    filepath2 = sys.argv[2]
    
    if not os.path.exists(filepath1):
        print(f"Error: File not found: {filepath1}")
        sys.exit(1)
    
    if not os.path.exists(filepath2):
        print(f"Error: File not found: {filepath2}")
        sys.exit(1)
    
    print(f"Reading first snapshot file: {filepath1}")
    data1 = parse_snapshot_file(filepath1)
    
    print(f"Reading second snapshot file: {filepath2}")
    data2 = parse_snapshot_file(filepath2)
    
    if not data1[0] or not data2[0]:
        print("Error: No valid data found in one or both files")
        sys.exit(1)
    
    times1, _, lost_percent1, wet_tubes_pct1, objects_in_cache_pct1, tubes_expired_by_time1, tubes_expired_by_reads1 = data1
    times2, _, lost_percent2, wet_tubes_pct2, objects_in_cache_pct2, tubes_expired_by_time2, tubes_expired_by_reads2 = data2
    
    print(f"\nFile 1: {len(times1)} data points, time range: {times1[0]:.2f} to {times1[-1]:.2f} years")
    print(f"  Cache max: {max(objects_in_cache_pct1):.4f}%, Tubes expired by time: {max(tubes_expired_by_time1)}, by reads: {max(tubes_expired_by_reads1)}")
    
    print(f"\nFile 2: {len(times2)} data points, time range: {times2[0]:.2f} to {times2[-1]:.2f} years")
    print(f"  Cache max: {max(objects_in_cache_pct2):.4f}%, Tubes expired by time: {max(tubes_expired_by_time2)}, by reads: {max(tubes_expired_by_reads2)}")
    
    print("\nGenerating comparison visualization...")
    output_path = plot_comparison(data1, data2, filepath1, filepath2)
    
    print(f"\n✓ Comparison complete!")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()

