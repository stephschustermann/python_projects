#!/usr/bin/env python3
"""
Visualize comprehensive metrics from a snapshot file:
- Lost objects (count and percentage)
- Wet tubes (percentage)
- Objects in cache (percentage)
- Expired tubes by reads
- Expired tubes by time
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


def plot_comprehensive_metrics(times, lost_objects, lost_percent, wet_tubes_pct,
                               objects_in_cache_pct, tubes_expired_by_time, 
                               tubes_expired_by_reads, filename):
    """Create comprehensive visualization with multiple subplots."""
    
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    
    # Calculate total expired tubes (time + reads)
    tubes_expired_total = [t + r for t, r in zip(tubes_expired_by_time, tubes_expired_by_reads)]
    
    # Create figure with 4 subplots (2 rows, 2 columns)
    fig = plt.figure(figsize=(16, 10))
    
    # Overall title
    fig.suptitle(f'Comprehensive Metrics Analysis\n{snapshot_name}', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # 1. Lost Objects (Percentage only)
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(times, lost_percent, color='tab:red', linewidth=1.2, alpha=0.9)
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', fontsize=12, color='tab:red')
    ax1.set_title('Lost Objects Percentage Over Time', fontsize=13, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max(times))
    if max(lost_percent) > 0:
        ax1.set_ylim(0, max(lost_percent) * 1.1)
    
    # 2. Wet Tubes (Percentage)
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(times, wet_tubes_pct, color='tab:blue', linewidth=1.2, alpha=0.9)
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=12, color='tab:blue')
    ax2.set_title('Wet Tubes Percentage Over Time', fontsize=13, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='tab:blue')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max(times))
    ax2.set_ylim(0, max(wet_tubes_pct) * 1.1)
    
    # 3. Objects in Cache (Percentage)
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(times, objects_in_cache_pct, color='tab:green', linewidth=1.2, alpha=0.9)
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=12, color='tab:green')
    ax3.set_title('Objects in Cache Percentage Over Time', fontsize=13, fontweight='bold')
    ax3.tick_params(axis='y', labelcolor='tab:green')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max(times))
    ax3.set_ylim(0, max(objects_in_cache_pct) * 1.1)
    
    # 4. Expired Tubes (by time as dashed, total as solid)
    ax4 = plt.subplot(2, 2, 4)
    # Dashed line for expired by time only
    ax4.plot(times, tubes_expired_by_time, color='tab:orange', linewidth=1.2, 
             linestyle='--', alpha=0.9, label='Expired by Time')
    # Solid line for total expired (time + reads)
    ax4.plot(times, tubes_expired_total, color='tab:purple', linewidth=1.2, 
             linestyle='-', alpha=0.9, label='Total Expired (Time + Reads)')
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Tubes Expired (count)', fontsize=12)
    ax4.set_title('Tubes Expired Over Time', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper left', fontsize=10)
    ax4.set_xlim(0, max(times))
    if max(tubes_expired_total) > 0:
        ax4.set_ylim(0, max(tubes_expired_total) * 1.1)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save the figure
    output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_metrics'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{snapshot_name}_comprehensive_metrics.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_comprehensive_metrics.py <snapshot_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"Reading snapshot file: {filepath}")
    (times, lost_objects, lost_percent, wet_tubes_pct, 
     objects_in_cache_pct, tubes_expired_by_time, 
     tubes_expired_by_reads) = parse_snapshot_file(filepath)
    
    if not times:
        print("Error: No valid data found in file")
        sys.exit(1)
    
    # Calculate total expired tubes
    tubes_expired_total = [t + r for t, r in zip(tubes_expired_by_time, tubes_expired_by_reads)]
    
    print(f"\nFound {len(times)} data points")
    print(f"Time range: {times[0]:.2f} to {times[-1]:.2f} years")
    print(f"\nMetric Ranges:")
    print(f"  Lost Objects %: {min(lost_percent):.4f}% to {max(lost_percent):.4f}%")
    print(f"  Wet Tubes %: {min(wet_tubes_pct):.2f}% to {max(wet_tubes_pct):.2f}%")
    print(f"  Objects in Cache %: {min(objects_in_cache_pct):.4f}% to {max(objects_in_cache_pct):.4f}%")
    print(f"  Tubes Expired by Time: {min(tubes_expired_by_time)} to {max(tubes_expired_by_time)}")
    print(f"  Tubes Expired by Reads: {min(tubes_expired_by_reads)} to {max(tubes_expired_by_reads)}")
    print(f"  Total Tubes Expired: {min(tubes_expired_total)} to {max(tubes_expired_total)}")
    
    print("\nGenerating comprehensive metrics visualization...")
    output_path = plot_comprehensive_metrics(times, lost_objects, lost_percent, 
                                            wet_tubes_pct, objects_in_cache_pct, 
                                            tubes_expired_by_time, tubes_expired_by_reads,
                                            filepath)
    
    print(f"\n✓ Visualization complete!")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()

