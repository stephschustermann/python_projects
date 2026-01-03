#!/usr/bin/env python3
"""
Script to track tube status, lost objects percentage, and copysets distribution over time (with triplets).

Tracks:
1. Number of terminated tubes (last read) over time
2. Percentage of lost objects over time
3. Copysets distribution (copysets_3, copysets_2, copysets_1, copysets_0) over time
"""

import re
import matplotlib.pyplot as plt
from collections import defaultdict
import sys
import csv

def parse_snaps_file(filename):
    """
    Parse the snaps file to get lost objects percentage and copysets data over time.
    
    Returns:
        tuple: (years, lost_percentages, copysets_3_pct, copysets_2_pct, copysets_1_pct, copysets_0_pct, initial_tubes)
    """
    years = []
    lost_percentages = []
    copysets_3_pct = []
    copysets_2_pct = []
    copysets_1_pct = []
    copysets_0_pct = []
    max_time = None
    initial_tubes = None
    
    print(f"Parsing snaps file: {filename}")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        # Parse header to get max_time_in_simulation (line 2, column 3) and initial_tubes (column 2)
        if len(lines) > 1:
            header_parts = lines[1].strip().split(', ')
            if len(header_parts) > 2:
                try:
                    initial_tubes = int(header_parts[1])
                    max_time = float(header_parts[2])
                    print(f"  Initial tubes: {initial_tubes}")
                    print(f"  Maximum simulation time: {max_time}")
                except ValueError:
                    pass
        
        # Skip header lines (first 4 lines)
        for line in lines[4:]:
            # Remove trailing comma if present
            line_clean = line.strip().rstrip(',').strip()
            parts = line_clean.split(', ')
            if len(parts) >= 16:  # Need at least 16 columns for triplets copysets data
                try:
                    timestamp = int(parts[0])
                    lost_percent = float(parts[9])
                    cs3_pct = float(parts[12])
                    cs2_pct = float(parts[13])
                    cs1_pct = float(parts[14])
                    cs0_pct = float(parts[15])
                    
                    # Convert timestamp to years
                    # max_time corresponds to 10 years
                    if max_time:
                        year = (timestamp / max_time) * 10
                    else:
                        year = timestamp / 182625 * 10  # Fallback
                    
                    years.append(year)
                    lost_percentages.append(lost_percent)
                    copysets_3_pct.append(cs3_pct)
                    copysets_2_pct.append(cs2_pct)
                    copysets_1_pct.append(cs1_pct)
                    copysets_0_pct.append(cs0_pct)
                except (ValueError, IndexError):
                    continue
    
    print(f"  Loaded {len(years)} snapshots with triplets copysets data")
    return years, lost_percentages, copysets_3_pct, copysets_2_pct, copysets_1_pct, copysets_0_pct, initial_tubes


def parse_log_file(filename, initial_tubes_from_snaps=None):
    """
    Parse the log file and track tube terminations and creations over time.
    
    Returns:
        tuple: (years_terminated, counts_terminated, years_created, counts_created, 
                initial_tubes, actual_total_tubes, final_terminated, synthesis_count)
    """
    # Data structures to track state
    terminated_tubes = set()  # Set of tube numbers that have been terminated
    all_tubes_seen = set()  # All tube numbers seen in the simulation
    synthesis_count = 0  # Count of synthesis from cache events
    
    # Time series data (year -> count)
    terminated_by_year = defaultdict(int)
    created_by_year = defaultdict(int)
    
    # Metadata - use initial tubes from snaps file if available
    initial_tubes = initial_tubes_from_snaps if initial_tubes_from_snaps else 3042
    
    print(f"Parsing log file: {filename}")
    print("This may take a while for large files...")
    
    line_count = 0
    with open(filename, 'r') as f:
        for line in f:
            line_count += 1
            if line_count % 100000 == 0:
                print(f"  Processed {line_count:,} lines...")
            
            line = line.strip()
            
            # Parse initialization to get total objects
            if "number of objects in tube:" in line:
                match = re.search(r'number of objects in tube:\s*(\d+)', line)
                if match:
                    objects_per_tube = int(match.group(1))
            
            # Parse synthesis from cache events (tube creation)
            if "synthesis from cache" in line:
                match = re.search(r'time:\s*(\d+),\s*year:\s*(\d+),\s*synthesis from cache', line)
                if match:
                    time = int(match.group(1))
                    year = int(match.group(2))
                    synthesis_count += 1
                    # Track cumulative tube count (initial + synthesized)
                    created_by_year[year] = initial_tubes + synthesis_count
            
            # Parse last read events (tube termination)
            elif "last read" in line:
                match = re.search(r'time:\s*(\d+),\s*year:\s*(\d+),\s*last read.*tube number:\s*(\d+)', line)
                if match:
                    time = int(match.group(1))
                    year = int(match.group(2))
                    tube_number = int(match.group(3))
                    
                    all_tubes_seen.add(tube_number)
                    if tube_number not in terminated_tubes:
                        terminated_tubes.add(tube_number)
                        terminated_by_year[year] = len(terminated_tubes)
            
            # Parse read events to track tube numbers
            elif "read, object number:" in line and "tube number:" in line:
                match = re.search(r'tube number:\s*(\d+)', line)
                if match:
                    tube_number = int(match.group(1))
                    all_tubes_seen.add(tube_number)
    
    print(f"  Total lines processed: {line_count:,}")
    print(f"  Initial tubes: {initial_tubes}")
    print(f"  Tubes synthesized from cache: {synthesis_count}")
    print(f"  Total unique tubes seen: {len(all_tubes_seen)}")
    print(f"  Total terminated tubes: {len(terminated_tubes)}")
    
    # Add year 0 with initial tubes count
    created_by_year[0] = initial_tubes
    
    # Convert to sorted lists for plotting
    years_terminated = sorted(terminated_by_year.keys())
    counts_terminated = [terminated_by_year[y] for y in years_terminated]
    
    years_created = sorted(created_by_year.keys())
    counts_created = [created_by_year[y] for y in years_created]
    
    # Use the actual number of tubes seen
    actual_total_tubes = len(all_tubes_seen)
    
    return (years_terminated, counts_terminated, 
            years_created, counts_created,
            initial_tubes, actual_total_tubes, len(terminated_tubes), synthesis_count)


def plot_unified_results(years_terminated, counts_terminated, 
                         years_created, counts_created,
                         years_lost, lost_percentages,
                         copysets_3_pct, copysets_2_pct, copysets_1_pct, copysets_0_pct,
                         initial_tubes, actual_total_tubes, 
                         final_terminated, synthesis_count,
                         output_filename):
    """
    Create a unified plot showing tube terminations, tube creations, lost objects percentage,
    and copysets distribution (with triplets) over time on the same graph with dual Y-axes.
    """
    fig, ax1 = plt.subplots(figsize=(16, 8))
    
    # Plot 1: Tube counts over time (left Y-axis)
    color_tubes = 'tab:blue'
    color_created = 'tab:green'
    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Number of Tubes', fontsize=14, fontweight='bold', color='black')
    
    # Add starting point at year 0 for terminated tubes if not present
    if years_terminated and years_terminated[0] != 0:
        years_terminated = [0] + years_terminated
        counts_terminated = [0] + counts_terminated
    
    # Plot terminated tubes with step plot (post style - stays flat then jumps vertically)
    ax1.step(years_terminated, counts_terminated, where='post', color=color_tubes, 
             linewidth=4, label='Terminated tubes', zorder=5, alpha=0.9)
    # Add markers at the actual data points
    ax1.plot(years_terminated, counts_terminated, color=color_tubes, marker='o', 
             markersize=8, linestyle='', markevery=1, zorder=6, 
             markerfacecolor=color_tubes, markeredgewidth=2, markeredgecolor='white')
    
    # Plot created tubes (cumulative)
    ax1.plot(years_created, counts_created, color=color_created, linewidth=3, 
             marker='s', markersize=6, label='Total tubes (initial + synthesized)', 
             markevery=1, linestyle='--', zorder=2)
    
    ax1.tick_params(axis='y', labelcolor='black', labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    
    # Reference line for initial tubes
    ax1.axhline(y=initial_tubes, color='darkred', linestyle=':', linewidth=1.5, 
                label=f'Initial tubes ({initial_tubes})', alpha=0.6, zorder=1)
    
    # Set limits for better scale
    max_tubes = max(initial_tubes + 500, actual_total_tubes + 200)
    ax1.set_ylim(0, max_tubes)
    ax1.set_xlim(0, 10)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.7, zorder=0)
    
    # Create second Y-axis for percentages (lost objects and copysets)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Percentage (%)', fontsize=14, fontweight='bold', color='black')
    
    # Plot lost objects percentage
    color_lost = 'tab:red'
    ax2.plot(years_lost, lost_percentages, color=color_lost, linewidth=2.5, 
             label='Lost objects %', alpha=0.7, zorder=3)
    
    # Plot copysets percentages (triplets)
    ax2.plot(years_lost, copysets_3_pct, color='tab:cyan', linewidth=2, 
             label='Copysets 3 active %', alpha=0.8, linestyle='-', zorder=4)
    ax2.plot(years_lost, copysets_2_pct, color='tab:purple', linewidth=2, 
             label='Copysets 2 active %', alpha=0.8, linestyle='-', zorder=4)
    ax2.plot(years_lost, copysets_1_pct, color='tab:orange', linewidth=2, 
             label='Copysets 1 active %', alpha=0.8, linestyle='-', zorder=4)
    ax2.plot(years_lost, copysets_0_pct, color='tab:brown', linewidth=2, 
             label='Copysets 0 active %', alpha=0.8, linestyle='-', zorder=4)
    
    ax2.tick_params(axis='y', labelcolor='black', labelsize=12)
    ax2.set_ylim(0, 105)
    
    # Title
    plt.title('Tube Lifecycle, Lost Objects, and Copysets Distribution (Triplets) Over Time', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Combine legends from both axes and place outside the plot area
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, 
               loc='upper left', bbox_to_anchor=(1.15, 1.0),
               fontsize=10, framealpha=0.95, edgecolor='black')
    
    # Add statistics text box
    percentage_terminated = (final_terminated / actual_total_tubes) * 100
    final_lost_percent = lost_percentages[-1] if lost_percentages else 0
    final_cs3 = copysets_3_pct[-1] if copysets_3_pct else 0
    final_cs2 = copysets_2_pct[-1] if copysets_2_pct else 0
    final_cs1 = copysets_1_pct[-1] if copysets_1_pct else 0
    final_cs0 = copysets_0_pct[-1] if copysets_0_pct else 0
    
    stats_text = f'Final Statistics:\n' \
                 f'• Initial tubes: {initial_tubes}\n' \
                 f'• Synthesized: {synthesis_count}\n' \
                 f'• Terminated: {final_terminated}/{actual_total_tubes} ({percentage_terminated:.1f}%)\n' \
                 f'• Lost objects: {final_lost_percent:.2f}%\n' \
                 f'• Copysets 3: {final_cs3:.1f}%\n' \
                 f'• Copysets 2: {final_cs2:.1f}%\n' \
                 f'• Copysets 1: {final_cs1:.1f}%\n' \
                 f'• Copysets 0: {final_cs0:.1f}%'
    
    ax1.text(0.98, 0.35, stats_text,
             transform=ax1.transAxes, fontsize=10, verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightyellow', 
                      alpha=0.95, edgecolor='black', linewidth=1.5))
    
    fig.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_filename}")
    
    # Print summary statistics
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    print(f"Initial tubes: {initial_tubes}")
    print(f"Tubes synthesized from cache: {synthesis_count}")
    print(f"Total unique tubes seen: {actual_total_tubes}")
    print(f"Tubes terminated (last read): {final_terminated} ({percentage_terminated:.1f}%)")
    print(f"Tubes still active: {actual_total_tubes - final_terminated} ({100-percentage_terminated:.1f}%)")
    print()
    print(f"Final lost objects: {final_lost_percent:.2f}%")
    print(f"Final copysets 3 active: {final_cs3:.1f}%")
    print(f"Final copysets 2 active: {final_cs2:.1f}%")
    print(f"Final copysets 1 active: {final_cs1:.1f}%")
    print(f"Final copysets 0 active: {final_cs0:.1f}%")
    print("="*70)


def main():
    if len(sys.argv) < 3:
        print("Usage: python track_tube_status_with_triplets.py <input_log_file> <input_snaps_file> [output_plot_file]")
        print("\nExample:")
        print("  python track_tube_status_with_triplets.py input/logs/triplets_with_copysets_track/maxReads_100_accessRate_100_dist_Uniform_20251220_220847.txt input/snaps/triplets_with_copysets_track/maxReads_100_accessRate_100_dist_Uniform_20251220_220847.txt")
        sys.exit(1)
    
    log_file = sys.argv[1]
    snaps_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "output/tube_status_with_triplets.png"
    
    # Parse the snaps file first to get initial_tubes
    years_lost, lost_percentages, copysets_3_pct, copysets_2_pct, copysets_1_pct, copysets_0_pct, initial_tubes = parse_snaps_file(snaps_file)
    
    # Parse the log file for tube terminations
    (years_terminated, counts_terminated, 
     years_created, counts_created,
     initial_tubes_from_log, actual_total_tubes, 
     final_terminated, synthesis_count) = parse_log_file(log_file, initial_tubes)
    
    # Create the unified plot
    plot_unified_results(years_terminated, counts_terminated, 
                        years_created, counts_created,
                        years_lost, lost_percentages,
                        copysets_3_pct, copysets_2_pct, copysets_1_pct, copysets_0_pct,
                        initial_tubes, actual_total_tubes,
                        final_terminated, synthesis_count,
                        output_file)
    
    print("\nDone!")


if __name__ == "__main__":
    main()




