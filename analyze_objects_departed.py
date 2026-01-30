#!/usr/bin/env python3
"""
Analyze the percentage of objects that have departed from the system over time.
This tracks: (Initial Objects - Current Objects) / Initial Objects * 100
"""

import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime


def parse_snapshot_for_departures(filepath):
    """
    Parse snapshot file and calculate departure percentage.
    
    Columns:
    0: timestamp (in years)
    12: total objects in the system
    """
    
    times = []
    objects_in_system = []
    objects_departed = []
    departure_percentage = []
    
    initial_objects = None
    
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
                total_objects = int(parts[12])
                
                # Set initial object count from first data point
                if initial_objects is None and total_objects > 0:
                    initial_objects = total_objects
                
                # Calculate departed objects
                if initial_objects and initial_objects > 0:
                    departed = initial_objects - total_objects
                    departure_pct = (departed / initial_objects) * 100
                else:
                    departed = 0
                    departure_pct = 0.0
                
                times.append(timestamp)
                objects_in_system.append(total_objects)
                objects_departed.append(departed)
                departure_percentage.append(departure_pct)
                
            except (ValueError, IndexError) as e:
                continue
    
    return times, objects_in_system, objects_departed, departure_percentage, initial_objects


def plot_departure_analysis(times, objects_in_system, objects_departed, 
                           departure_percentage, initial_objects, filename):
    """Create visualizations focused on object departures."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    fig.suptitle(f'Objects Departed from System Over Time\n{snapshot_name}', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Plot 1: Departure Percentage - THE MAIN METRIC
    ax1.plot(times, departure_percentage, color='#e74c3c', linewidth=3, alpha=0.9)
    ax1.fill_between(times, 0, departure_percentage, alpha=0.3, color='#e74c3c')
    ax1.set_xlabel('Time (years)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Objects No Longer in System (%)', fontsize=13, fontweight='bold')
    ax1.set_title('Percentage of Objects Departed from System', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, linewidth=1.5)
    ax1.set_xlim(0, max(times) if times else 10)
    ax1.set_ylim(0, 105)
    
    # Add milestone annotations
    if times and departure_percentage:
        milestones = [25, 50, 75, 90, 100]
        for milestone in milestones:
            # Find first time this milestone is reached
            for i, pct in enumerate(departure_percentage):
                if pct >= milestone:
                    ax1.axhline(y=milestone, color='gray', linestyle='--', 
                               linewidth=0.8, alpha=0.4)
                    ax1.text(max(times) * 0.02, milestone + 2, f'{milestone}%', 
                            fontsize=10, color='gray', fontweight='bold')
                    break
        
        # Highlight final value
        final_pct = departure_percentage[-1]
        final_time = times[-1]
        ax1.plot(final_time, final_pct, 'ro', markersize=10, zorder=5)
        ax1.annotate(f'{final_pct:.1f}%\nat {final_time:.2f} yrs', 
                    xy=(final_time, final_pct),
                    xytext=(final_time * 0.7, final_pct * 0.85),
                    fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.7', facecolor='yellow', 
                             edgecolor='red', linewidth=2, alpha=0.9),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    # Plot 2: Objects Remaining vs Departed (Stacked to 100%)
    remaining_pct = [100 - dp for dp in departure_percentage]
    ax2.fill_between(times, 0, remaining_pct, alpha=0.7, color='#3498db', 
                     label='Still in System')
    ax2.fill_between(times, remaining_pct, 100, alpha=0.7, color='#e74c3c', 
                     label='Departed')
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Percentage (%)', fontsize=12)
    ax2.set_title('System Status: Remaining vs Departed', fontsize=13, fontweight='bold')
    ax2.legend(loc='center left', fontsize=11, framealpha=0.9)
    ax2.set_xlim(0, max(times) if times else 10)
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Absolute Counts
    ax3.plot(times, objects_in_system, color='#3498db', linewidth=2.5, 
             label='Objects in System', alpha=0.9)
    ax3.plot(times, objects_departed, color='#e74c3c', linewidth=2.5, 
             label='Objects Departed', alpha=0.9)
    ax3.axhline(y=initial_objects, color='gray', linestyle='--', 
               linewidth=1.5, alpha=0.5, label=f'Initial: {initial_objects:,}')
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Object Count', fontsize=12)
    ax3.set_title('Absolute Object Counts', fontsize=13, fontweight='bold')
    ax3.legend(loc='best', fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max(times) if times else 10)
    ax3.ticklabel_format(style='plain', axis='y')
    
    # Plot 4: Summary Statistics Table
    ax4.axis('off')
    
    if times and departure_percentage:
        # Find key milestones
        milestone_data = []
        milestones = [10, 25, 50, 75, 90, 95, 99, 100]
        
        for milestone in milestones:
            for i, pct in enumerate(departure_percentage):
                if pct >= milestone:
                    milestone_data.append((milestone, times[i], objects_departed[i]))
                    break
        
        # Create summary text
        summary_lines = [
            "DEPARTURE MILESTONES",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Initial Objects: {initial_objects:,}",
            "",
            f"{'Departed%':<12} {'Time (yrs)':<12} {'Count':<15}",
            "─" * 40
        ]
        
        for pct, time, count in milestone_data[:8]:  # Limit to 8 rows
            summary_lines.append(f"{pct:>3}%         {time:>6.2f}       {count:>12,}")
        
        summary_lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"FINAL STATE:",
            f"  Time: {times[-1]:.2f} years",
            f"  Departed: {objects_departed[-1]:,} ({departure_percentage[-1]:.2f}%)",
            f"  Remaining: {objects_in_system[-1]:,} ({100-departure_percentage[-1]:.2f}%)"
        ])
        
        summary_text = '\n'.join(summary_lines)
        
        ax4.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', 
                         alpha=0.9, pad=1, edgecolor='orange', linewidth=2))
    
    plt.tight_layout()
    
    # Save the figure
    output_dir = '/Users/stephanie/Documents/thesis/python_projects/output/object_loss_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'departure_analysis_{snapshot_name}_{timestamp}.png'
    output_path = os.path.join(output_dir, output_filename)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Plot saved to: {output_path}")
    
    return output_path


def print_departure_summary(times, objects_in_system, objects_departed, 
                           departure_percentage, initial_objects):
    """Print summary focused on departures."""
    
    if not times:
        print("No data to summarize")
        return
    
    print("\n" + "="*70)
    print("OBJECTS DEPARTED FROM SYSTEM - SUMMARY")
    print("="*70)
    
    print(f"\nInitial Objects:           {initial_objects:,}")
    print(f"Time Period:               {times[0]:.2f} - {times[-1]:.2f} years")
    print(f"Number of Snapshots:       {len(times):,}")
    
    # Find when system is exhausted (100% departed)
    exhaust_time = None
    for i, pct in enumerate(departure_percentage):
        if pct >= 100.0:
            exhaust_time = times[i]
            break
    
    if exhaust_time:
        print(f"100% Departed at:          {exhaust_time:.2f} years")
    
    print(f"\n{'Time':>6} {'In System':>15} {'Departed':>15} {'Departed %':>12}")
    print(f"{'(yrs)':>6} {'(count)':>15} {'(count)':>15} {'':>12}")
    print("-" * 70)
    
    # Print at key intervals
    intervals = [0, 1, 2, 3, 5, 7.5, 10]
    for target_time in intervals:
        closest_idx = min(range(len(times)), key=lambda i: abs(times[i] - target_time))
        if abs(times[closest_idx] - target_time) <= 0.5:
            t = times[closest_idx]
            in_sys = objects_in_system[closest_idx]
            departed = objects_departed[closest_idx]
            dep_pct = departure_percentage[closest_idx]
            print(f"{t:>6.2f} {in_sys:>15,} {departed:>15,} {dep_pct:>11.2f}%")
    
    # Final values
    print("-" * 70)
    final_time = times[-1]
    final_in_sys = objects_in_system[-1]
    final_departed = objects_departed[-1]
    final_dep_pct = departure_percentage[-1]
    print(f"{final_time:>6.2f} {final_in_sys:>15,} {final_departed:>15,} {final_dep_pct:>11.2f}%")
    
    print("\n" + "="*70)
    print(f"FINAL: {final_dep_pct:.2f}% of objects have departed from the system")
    print("="*70 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_objects_departed.py <snapshot_file>")
        print("\nExample:")
        print("  python analyze_objects_departed.py input/snaps/snaps_output_2_20260112_182628.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"Reading snapshot file: {filepath}")
    
    times, objects_in_system, objects_departed, departure_percentage, initial_objects = \
        parse_snapshot_for_departures(filepath)
    
    if not times:
        print("Error: No valid data found in file")
        sys.exit(1)
    
    print(f"✓ Successfully parsed {len(times)} data points")
    
    # Print summary
    print_departure_summary(times, objects_in_system, objects_departed, 
                           departure_percentage, initial_objects)
    
    # Create visualization
    print("Creating visualization...")
    output_path = plot_departure_analysis(times, objects_in_system, objects_departed,
                                         departure_percentage, initial_objects, filepath)
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
