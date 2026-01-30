#!/usr/bin/env python3
"""
Comprehensive analysis of object fate over time:
- Objects READ (successfully accessed)
- Objects LOST (data loss)
- Objects REMAINING in system
"""

import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime


def parse_complete_snapshot_file(filepath):
    """
    Parse the snapshot file and track all object fates.
    
    Columns:
    0: timestamp (in years)
    1: objects_read_from_cache_since_last_snap
    3: objects_read_from_tubes_since_last_snap  
    10: objects_lost_since_last_snap
    12: total objects in the system
    """
    
    times = []
    cumulative_read_cache = []
    cumulative_read_tubes = []
    cumulative_read_total = []
    cumulative_lost = []
    total_objects_in_system = []
    
    initial_objects = None
    running_read_cache = 0
    running_read_tubes = 0
    running_lost = 0
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Skip header line
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(',')
            if len(parts) < 13:
                continue
            
            try:
                timestamp = float(parts[0])
                objects_read_cache = int(parts[1])
                objects_read_tubes = int(parts[3])
                objects_lost = int(parts[10])
                total_objects = int(parts[12])
                
                # Set initial object count from first data point
                if initial_objects is None and total_objects > 0:
                    initial_objects = total_objects
                
                # Accumulate
                running_read_cache += objects_read_cache
                running_read_tubes += objects_read_tubes
                running_lost += objects_lost
                
                times.append(timestamp)
                cumulative_read_cache.append(running_read_cache)
                cumulative_read_tubes.append(running_read_tubes)
                cumulative_read_total.append(running_read_cache + running_read_tubes)
                cumulative_lost.append(running_lost)
                total_objects_in_system.append(total_objects)
                
            except (ValueError, IndexError) as e:
                continue
    
    # Calculate percentages
    read_cache_pct = []
    read_tubes_pct = []
    read_total_pct = []
    loss_pct = []
    remaining_pct = []
    
    if initial_objects and initial_objects > 0:
        for i in range(len(times)):
            read_cache_pct.append((cumulative_read_cache[i] / initial_objects) * 100)
            read_tubes_pct.append((cumulative_read_tubes[i] / initial_objects) * 100)
            read_total_pct.append((cumulative_read_total[i] / initial_objects) * 100)
            loss_pct.append((cumulative_lost[i] / initial_objects) * 100)
            remaining_pct.append((total_objects_in_system[i] / initial_objects) * 100)
    
    return (times, cumulative_read_cache, cumulative_read_tubes, cumulative_read_total,
            cumulative_lost, total_objects_in_system, initial_objects,
            read_cache_pct, read_tubes_pct, read_total_pct, loss_pct, remaining_pct)


def plot_complete_fate_analysis(times, read_cache, read_tubes, read_total, lost, remaining,
                                initial_objects, read_cache_pct, read_tubes_pct, 
                                read_total_pct, loss_pct, remaining_pct, filename):
    """Create comprehensive visualization of object fates."""
    
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    fig.suptitle(f'Complete Object Fate Analysis Over Time\n{snapshot_name}', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # Plot 1: Stacked Area Chart - Percentage Distribution
    ax1 = fig.add_subplot(gs[0, :])
    ax1.fill_between(times, 0, loss_pct, alpha=0.7, color='#d62728', label='Lost (Data Loss)')
    ax1.fill_between(times, loss_pct, [l + r for l, r in zip(loss_pct, read_total_pct)], 
                     alpha=0.7, color='#2ca02c', label='Read (Successfully Accessed)')
    ax1.fill_between(times, [l + r for l, r in zip(loss_pct, read_total_pct)], 100,
                     alpha=0.7, color='#1f77b4', label='Remaining in System')
    
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Percentage of Initial Objects (%)', fontsize=12)
    ax1.set_title('Object Fate Distribution (100% Stacked)', fontsize=14, fontweight='bold')
    ax1.set_xlim(0, max(times) if times else 10)
    ax1.set_ylim(0, 100)
    ax1.legend(loc='upper right', fontsize=11)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Loss vs Read Comparison
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(times, loss_pct, color='#d62728', linewidth=2.5, label='Lost %', alpha=0.8)
    ax2.plot(times, read_total_pct, color='#2ca02c', linewidth=2.5, label='Read %', alpha=0.8)
    ax2.set_xlabel('Time (years)', fontsize=11)
    ax2.set_ylabel('Percentage (%)', fontsize=11)
    ax2.set_title('Lost vs Successfully Read', fontsize=13, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max(times) if times else 10)
    
    # Plot 3: Read Breakdown (Cache vs Tubes)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(times, read_cache_pct, color='#ff7f0e', linewidth=2, label='Read from Cache', alpha=0.8)
    ax3.plot(times, read_tubes_pct, color='#9467bd', linewidth=2, label='Read from Tubes', alpha=0.8)
    ax3.plot(times, read_total_pct, color='#2ca02c', linewidth=2.5, 
             label='Total Read', alpha=0.8, linestyle='--')
    ax3.set_xlabel('Time (years)', fontsize=11)
    ax3.set_ylabel('Percentage (%)', fontsize=11)
    ax3.set_title('Read Operations Breakdown', fontsize=13, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max(times) if times else 10)
    
    # Plot 4: Remaining Objects %
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.plot(times, remaining_pct, color='#1f77b4', linewidth=2.5, alpha=0.8)
    ax4.fill_between(times, 0, remaining_pct, alpha=0.3, color='#1f77b4')
    ax4.set_xlabel('Time (years)', fontsize=11)
    ax4.set_ylabel('Remaining (%)', fontsize=11)
    ax4.set_title('Objects Still in System', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, max(times) if times else 10)
    ax4.set_ylim(0, 100)
    
    # Plot 5: Absolute Counts
    ax5 = fig.add_subplot(gs[2, :2])
    ax5.plot(times, lost, color='#d62728', linewidth=2, label='Lost Objects', alpha=0.8)
    ax5.plot(times, read_total, color='#2ca02c', linewidth=2, label='Read Objects', alpha=0.8)
    ax5.plot(times, remaining, color='#1f77b4', linewidth=2, label='Remaining Objects', alpha=0.8)
    ax5.set_xlabel('Time (years)', fontsize=11)
    ax5.set_ylabel('Object Count', fontsize=11)
    ax5.set_title('Absolute Object Counts', fontsize=13, fontweight='bold')
    ax5.legend(loc='best', fontsize=10)
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim(0, max(times) if times else 10)
    ax5.ticklabel_format(style='plain', axis='y')
    
    # Plot 6: Summary Statistics
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')
    
    if times and loss_pct and read_total_pct:
        final_time = times[-1]
        final_loss_pct = loss_pct[-1]
        final_read_pct = read_total_pct[-1]
        final_remaining_pct = remaining_pct[-1]
        
        final_lost_count = lost[-1]
        final_read_count = read_total[-1]
        final_remaining_count = remaining[-1]
        
        # Calculate when system exhausted
        exhaust_time = "N/A"
        for i, obj_count in enumerate(remaining):
            if obj_count == 0:
                exhaust_time = f"{times[i]:.2f} yrs"
                break
        
        summary_text = f"""
FINAL ACCOUNTING
━━━━━━━━━━━━━━━━━━━━━━
Initial: {initial_objects:,}

LOST (Data Loss):
  {final_lost_count:,}
  {final_loss_pct:.2f}%

READ (Accessed):
  {final_read_count:,}
  {final_read_pct:.2f}%

REMAINING:
  {final_remaining_count:,}
  {final_remaining_pct:.2f}%
━━━━━━━━━━━━━━━━━━━━━━
Total Accounted:
  {final_lost_count + final_read_count + final_remaining_count:,}
  {final_loss_pct + final_read_pct + final_remaining_pct:.2f}%

System Exhausted:
  {exhaust_time}
        """
        
        ax6.text(0.05, 0.5, summary_text, fontsize=11, family='monospace',
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, pad=1))
    
    plt.tight_layout()
    
    # Save the figure
    output_dir = '/Users/stephanie/Documents/thesis/python_projects/output/object_loss_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'complete_fate_analysis_{snapshot_name}_{timestamp}.png'
    output_path = os.path.join(output_dir, output_filename)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Plot saved to: {output_path}")
    
    return output_path


def print_detailed_summary(times, read_cache, read_tubes, read_total, lost, remaining,
                          initial_objects, read_cache_pct, read_tubes_pct, 
                          read_total_pct, loss_pct, remaining_pct):
    """Print detailed summary statistics."""
    
    if not times:
        print("No data to summarize")
        return
    
    print("\n" + "="*80)
    print("COMPLETE OBJECT FATE ANALYSIS")
    print("="*80)
    
    print(f"\nInitial Objects:           {initial_objects:,}")
    print(f"Time Period:               {times[0]:.2f} - {times[-1]:.2f} years")
    print(f"Number of Snapshots:       {len(times):,}")
    
    # Find when system exhausted
    exhaust_idx = None
    for i, obj_count in enumerate(remaining):
        if obj_count == 0:
            exhaust_idx = i
            break
    
    if exhaust_idx:
        print(f"System Exhausted at:       {times[exhaust_idx]:.2f} years (snapshot {exhaust_idx})")
    
    print(f"\n{'Time':>6} {'Read Cache':>12} {'Read Tubes':>12} {'Total Read':>12} "
          f"{'Lost':>12} {'Remaining':>12}")
    print(f"{'(yrs)':>6} {'Count':>12} {'Count':>12} {'Count':>12} "
          f"{'Count':>12} {'Count':>12}")
    print("-" * 80)
    
    # Print summary at key intervals
    intervals = [0, 1, 2, 3, 5, 7.5, 10]
    for target_time in intervals:
        closest_idx = min(range(len(times)), key=lambda i: abs(times[i] - target_time))
        if abs(times[closest_idx] - target_time) <= 0.5:
            t = times[closest_idx]
            print(f"{t:>6.2f} {read_cache[closest_idx]:>12,} {read_tubes[closest_idx]:>12,} "
                  f"{read_total[closest_idx]:>12,} {lost[closest_idx]:>12,} "
                  f"{remaining[closest_idx]:>12,}")
    
    # Final values
    print("-" * 80)
    print(f"{times[-1]:>6.2f} {read_cache[-1]:>12,} {read_tubes[-1]:>12,} "
          f"{read_total[-1]:>12,} {lost[-1]:>12,} {remaining[-1]:>12,}")
    
    print("\n" + "="*80)
    print("FINAL ACCOUNTING (Percentage of Initial Objects)")
    print("="*80)
    print(f"\nObjects LOST (data loss):        {lost[-1]:>12,}  ({loss_pct[-1]:>6.2f}%)")
    print(f"Objects READ (accessed):         {read_total[-1]:>12,}  ({read_total_pct[-1]:>6.2f}%)")
    print(f"  - Read from Cache:             {read_cache[-1]:>12,}  ({read_cache_pct[-1]:>6.2f}%)")
    print(f"  - Read from Tubes:             {read_tubes[-1]:>12,}  ({read_tubes_pct[-1]:>6.2f}%)")
    print(f"Objects REMAINING:               {remaining[-1]:>12,}  ({remaining_pct[-1]:>6.2f}%)")
    print("-" * 80)
    total_accounted = lost[-1] + read_total[-1] + remaining[-1]
    total_pct = loss_pct[-1] + read_total_pct[-1] + remaining_pct[-1]
    print(f"TOTAL ACCOUNTED:                 {total_accounted:>12,}  ({total_pct:>6.2f}%)")
    print("="*80 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_complete_object_fate.py <snapshot_file>")
        print("\nExample:")
        print("  python analyze_complete_object_fate.py input/snaps/snaps_output_2_20260112_182628.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"Reading snapshot file: {filepath}")
    
    (times, read_cache, read_tubes, read_total, lost, remaining, initial_objects,
     read_cache_pct, read_tubes_pct, read_total_pct, loss_pct, remaining_pct) = \
        parse_complete_snapshot_file(filepath)
    
    if not times:
        print("Error: No valid data found in file")
        sys.exit(1)
    
    print(f"✓ Successfully parsed {len(times)} data points")
    
    # Print detailed summary
    print_detailed_summary(times, read_cache, read_tubes, read_total, lost, remaining,
                          initial_objects, read_cache_pct, read_tubes_pct, 
                          read_total_pct, loss_pct, remaining_pct)
    
    # Create visualization
    print("Creating comprehensive visualization...")
    output_path = plot_complete_fate_analysis(
        times, read_cache, read_tubes, read_total, lost, remaining, initial_objects,
        read_cache_pct, read_tubes_pct, read_total_pct, loss_pct, remaining_pct, filepath)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
