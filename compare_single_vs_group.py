#!/usr/bin/env python3
"""
Script to compare tube status and lost objects between single_read_pairwise and group_read_pairwise runs.

Compares:
1. Lost reads percentage over time
2. Terminated tubes over time

For matching pairs of files from the two different approaches.
"""

import re
import matplotlib.pyplot as plt
from collections import defaultdict
import sys
import os
import glob


def extract_params_from_filename(filename):
    """
    Extract parameters from filename to match files.
    Returns: (maxReads, accessRate, dist) or None
    """
    basename = os.path.basename(filename)
    match = re.search(r'maxReads_(\d+)_accessRate_(\d+)_dist_(\w+)_\d{8}_\d{6}\.txt', basename)
    if match:
        return (match.group(1), match.group(2), match.group(3))
    return None


def parse_snaps_file(filename):
    """
    Parse the snaps file to get lost objects percentage over time.
    
    Returns:
        tuple: (years, lost_percentages, initial_tubes)
    """
    years = []
    lost_percentages = []
    max_time = None
    initial_tubes = None
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        # Parse header to get initial_tubes and max_time_in_simulation
        if len(lines) > 1:
            header_parts = lines[1].strip().split(', ')
            if len(header_parts) > 2:
                try:
                    initial_tubes = int(header_parts[1])
                    max_time = float(header_parts[2])
                except ValueError:
                    pass
        
        # Skip header lines (first 4 lines)
        for line in lines[4:]:
            parts = line.strip().split(', ')
            if len(parts) >= 10:
                try:
                    timestamp = int(parts[0])
                    lost_percent = float(parts[9])
                    
                    # Convert timestamp to years
                    if max_time:
                        year = (timestamp / max_time) * 10
                    else:
                        year = timestamp / 182625 * 10  # Fallback
                    
                    years.append(year)
                    lost_percentages.append(lost_percent)
                except (ValueError, IndexError):
                    continue
    
    return years, lost_percentages, initial_tubes


def parse_log_file(filename, initial_tubes_from_snaps=None):
    """
    Parse the log file and track tube terminations over time.
    
    Returns:
        tuple: (years_terminated, counts_terminated, initial_tubes, 
                actual_total_tubes, final_terminated, synthesis_count)
    """
    terminated_tubes = set()
    all_tubes_seen = set()
    synthesis_count = 0
    
    terminated_by_year = defaultdict(int)
    
    initial_tubes = initial_tubes_from_snaps if initial_tubes_from_snaps else 2304
    
    line_count = 0
    with open(filename, 'r') as f:
        for line in f:
            line_count += 1
            line = line.strip()
            
            # Parse synthesis from cache events
            if "synthesis from cache" in line:
                match = re.search(r'time:\s*(\d+),\s*year:\s*(\d+),\s*synthesis from cache', line)
                if match:
                    synthesis_count += 1
            
            # Parse last read events (tube termination)
            elif "last read" in line:
                match = re.search(r'time:\s*(\d+),\s*year:\s*(\d+),\s*last read.*tube number:\s*(\d+)', line)
                if match:
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
    
    # Convert to sorted lists
    years_terminated = sorted(terminated_by_year.keys())
    counts_terminated = [terminated_by_year[y] for y in years_terminated]
    
    actual_total_tubes = len(all_tubes_seen)
    
    return (years_terminated, counts_terminated, 
            initial_tubes, actual_total_tubes, 
            len(terminated_tubes), synthesis_count)


def plot_comparison(single_data, group_data, params, output_filename):
    """
    Create comparison plots for single vs group read approaches.
    
    Args:
        single_data: tuple of (years_terminated, counts_terminated, years_lost, 
                              lost_percentages, initial_tubes, actual_total_tubes, 
                              final_terminated, synthesis_count)
        group_data: same structure as single_data
        params: (maxReads, accessRate, dist)
        output_filename: path to save the plot
    """
    (s_years_term, s_counts_term, s_years_lost, s_lost_pct, 
     s_init_tubes, s_total_tubes, s_final_term, s_synth) = single_data
    
    (g_years_term, g_counts_term, g_years_lost, g_lost_pct,
     g_init_tubes, g_total_tubes, g_final_term, g_synth) = group_data
    
    maxReads, accessRate, dist = params
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # Plot 1: Terminated Tubes Comparison
    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Number of Terminated Tubes', fontsize=14, fontweight='bold')
    ax1.set_title(f'Terminated Tubes Over Time - {dist} Distribution\n' +
                  f'(maxReads={maxReads}, accessRate={accessRate})', 
                  fontsize=16, fontweight='bold', pad=20)
    
    # Add starting point at year 0 if not present
    if s_years_term and s_years_term[0] != 0:
        s_years_term = [0] + s_years_term
        s_counts_term = [0] + s_counts_term
    if g_years_term and g_years_term[0] != 0:
        g_years_term = [0] + g_years_term
        g_counts_term = [0] + g_counts_term
    
    # Plot single read approach
    ax1.step(s_years_term, s_counts_term, where='post', color='tab:blue', 
             linewidth=4, label='Single Read Pairwise', zorder=5, alpha=0.9)
    ax1.plot(s_years_term, s_counts_term, color='tab:blue', marker='o', 
             markersize=8, linestyle='', markevery=1, zorder=6,
             markerfacecolor='tab:blue', markeredgewidth=2, markeredgecolor='white')
    
    # Plot group read approach
    ax1.step(g_years_term, g_counts_term, where='post', color='tab:orange', 
             linewidth=4, label='Group Read Pairwise', zorder=4, alpha=0.9)
    ax1.plot(g_years_term, g_counts_term, color='tab:orange', marker='s', 
             markersize=8, linestyle='', markevery=1, zorder=5,
             markerfacecolor='tab:orange', markeredgewidth=2, markeredgecolor='white')
    
    ax1.set_xlim(0, 10)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax1.legend(loc='upper left', fontsize=12, framealpha=0.95, edgecolor='black')
    
    # Add statistics text box for terminated tubes
    s_pct_term = (s_final_term / s_total_tubes) * 100 if s_total_tubes > 0 else 0
    g_pct_term = (g_final_term / g_total_tubes) * 100 if g_total_tubes > 0 else 0
    
    stats_text_tubes = (f'Single Read:\n'
                       f'  Terminated: {s_final_term}/{s_total_tubes} ({s_pct_term:.1f}%)\n'
                       f'  Synthesized: {s_synth}\n\n'
                       f'Group Read:\n'
                       f'  Terminated: {g_final_term}/{g_total_tubes} ({g_pct_term:.1f}%)\n'
                       f'  Synthesized: {g_synth}')
    
    ax1.text(0.98, 0.48, stats_text_tubes,
             transform=ax1.transAxes, fontsize=10, verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightyellow', 
                      alpha=0.95, edgecolor='black', linewidth=1.5))
    
    # Plot 2: Lost Objects Percentage Comparison
    ax2.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Lost Objects (%)', fontsize=14, fontweight='bold')
    ax2.set_title('Lost Objects Over Time', fontsize=16, fontweight='bold', pad=20)
    
    # Plot lost objects
    ax2.plot(s_years_lost, s_lost_pct, color='tab:red', linewidth=3, 
             label='Single Read Pairwise', alpha=0.8, marker='o', markersize=4)
    ax2.plot(g_years_lost, g_lost_pct, color='tab:purple', linewidth=3, 
             label='Group Read Pairwise', alpha=0.8, marker='s', markersize=4)
    
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, max(max(s_lost_pct + [0]), max(g_lost_pct + [0])) * 1.1)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax2.legend(loc='upper left', fontsize=12, framealpha=0.95, edgecolor='black')
    
    # Add statistics text box for lost objects
    s_final_lost = s_lost_pct[-1] if s_lost_pct else 0
    g_final_lost = g_lost_pct[-1] if g_lost_pct else 0
    diff_lost = s_final_lost - g_final_lost
    
    stats_text_lost = (f'Final Lost Objects:\n'
                      f'  Single Read: {s_final_lost:.2f}%\n'
                      f'  Group Read: {g_final_lost:.2f}%\n'
                      f'  Difference: {diff_lost:+.2f}%')
    
    ax2.text(0.98, 0.98, stats_text_lost,
             transform=ax2.transAxes, fontsize=10, verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightblue', 
                      alpha=0.95, edgecolor='black', linewidth=1.5))
    
    fig.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_filename}")
    
    # Print summary statistics
    print("\n" + "="*70)
    print(f"COMPARISON SUMMARY - {dist} (maxReads={maxReads}, accessRate={accessRate})")
    print("="*70)
    print("TERMINATED TUBES:")
    print(f"  Single Read: {s_final_term}/{s_total_tubes} ({s_pct_term:.1f}%)")
    print(f"  Group Read:  {g_final_term}/{g_total_tubes} ({g_pct_term:.1f}%)")
    print(f"  Difference:  {s_final_term - g_final_term:+d} tubes ({s_pct_term - g_pct_term:+.1f}%)")
    print()
    print("SYNTHESIZED TUBES:")
    print(f"  Single Read: {s_synth}")
    print(f"  Group Read:  {g_synth}")
    print(f"  Difference:  {s_synth - g_synth:+d}")
    print()
    print("LOST OBJECTS:")
    print(f"  Single Read: {s_final_lost:.2f}%")
    print(f"  Group Read:  {g_final_lost:.2f}%")
    print(f"  Difference:  {diff_lost:+.2f}%")
    print("="*70)


def find_matching_files(base_path):
    """
    Find matching pairs of files between single_read_pairwise and group_read_pairwise.
    
    Returns:
        list of tuples: [(params, single_snap, single_log, group_snap, group_log), ...]
    """
    single_snaps_path = os.path.join(base_path, "input/snaps/single_read_pairwise")
    group_snaps_path = os.path.join(base_path, "input/snaps/group_read_pairwise")
    single_logs_path = os.path.join(base_path, "input/logs/single_read_pairwise")
    group_logs_path = os.path.join(base_path, "input/logs/group_read_pairwise")
    
    # Get all single read files
    single_snaps = glob.glob(os.path.join(single_snaps_path, "*.txt"))
    
    matches = []
    
    for single_snap in single_snaps:
        params = extract_params_from_filename(single_snap)
        if not params:
            continue
        
        maxReads, accessRate, dist = params
        
        # Find corresponding files
        single_log_pattern = os.path.join(single_logs_path, 
                                          f"maxReads_{maxReads}_accessRate_{accessRate}_dist_{dist}_*.txt")
        group_snap_pattern = os.path.join(group_snaps_path, 
                                          f"maxReads_{maxReads}_accessRate_{accessRate}_dist_{dist}_*.txt")
        group_log_pattern = os.path.join(group_logs_path, 
                                         f"maxReads_{maxReads}_accessRate_{accessRate}_dist_{dist}_*.txt")
        
        single_logs = glob.glob(single_log_pattern)
        group_snaps = glob.glob(group_snap_pattern)
        group_logs = glob.glob(group_log_pattern)
        
        if single_logs and group_snaps and group_logs:
            matches.append((params, single_snap, single_logs[0], group_snaps[0], group_logs[0]))
            print(f"Found match for: maxReads={maxReads}, accessRate={accessRate}, dist={dist}")
    
    return matches


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_single_vs_group.py <base_path> [output_dir]")
        print("\nExample:")
        print("  python compare_single_vs_group.py . output/comparisons")
        print("\nThis will compare all matching files from single_read_pairwise and group_read_pairwise folders.")
        sys.exit(1)
    
    base_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/comparisons"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all matching file pairs
    print("Searching for matching files...")
    matches = find_matching_files(base_path)
    
    if not matches:
        print("No matching file pairs found!")
        sys.exit(1)
    
    print(f"\nFound {len(matches)} matching pairs. Processing...")
    
    # Process each match
    for params, single_snap, single_log, group_snap, group_log in matches:
        maxReads, accessRate, dist = params
        print(f"\n{'='*70}")
        print(f"Processing: maxReads={maxReads}, accessRate={accessRate}, dist={dist}")
        print(f"{'='*70}")
        
        # Parse single read files
        print("\nParsing SINGLE READ files...")
        print(f"  Snaps: {os.path.basename(single_snap)}")
        s_years_lost, s_lost_pct, s_init_tubes = parse_snaps_file(single_snap)
        print(f"  Logs: {os.path.basename(single_log)}")
        (s_years_term, s_counts_term, _, s_total_tubes, 
         s_final_term, s_synth) = parse_log_file(single_log, s_init_tubes)
        
        # Parse group read files
        print("\nParsing GROUP READ files...")
        print(f"  Snaps: {os.path.basename(group_snap)}")
        g_years_lost, g_lost_pct, g_init_tubes = parse_snaps_file(group_snap)
        print(f"  Logs: {os.path.basename(group_log)}")
        (g_years_term, g_counts_term, _, g_total_tubes, 
         g_final_term, g_synth) = parse_log_file(group_log, g_init_tubes)
        
        # Create comparison plot
        output_filename = os.path.join(output_dir, 
                                      f"comparison_maxReads_{maxReads}_accessRate_{accessRate}_dist_{dist}.png")
        
        single_data = (s_years_term, s_counts_term, s_years_lost, s_lost_pct,
                      s_init_tubes, s_total_tubes, s_final_term, s_synth)
        group_data = (g_years_term, g_counts_term, g_years_lost, g_lost_pct,
                     g_init_tubes, g_total_tubes, g_final_term, g_synth)
        
        plot_comparison(single_data, group_data, params, output_filename)
    
    print(f"\n{'='*70}")
    print(f"All comparisons complete! Plots saved to: {output_dir}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()




