#!/usr/bin/env python3
"""
Visualize m_lost_percent and exhausted_tubes_pct from a snapshot file over time.
"""

import matplotlib.pyplot as plt
import sys
import os


def parse_snapshot_file(filepath):
    """Parse a snapshot file and extract time, m_lost_percent, and exhausted_tubes_pct."""
    
    times = []
    m_lost_percents = []
    exhausted_tubes_pcts = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Skip the first 2 header lines and the column headers
        for line in lines[3:]:
            parts = line.strip().split(', ')
            if len(parts) < 14:
                continue
            
            try:
                time_stamp = int(parts[0])  # time in days
                m_lost_percent = float(parts[9])  # m_lost_percent
                exhausted_tubes_pct = float(parts[13])  # exhausted_tubes_pct
                
                # Convert days to years (divide by 36500 to get 10 years from 365000 days)
                times.append(time_stamp / 36500.0)
                m_lost_percents.append(m_lost_percent)
                exhausted_tubes_pcts.append(exhausted_tubes_pct)
            except (ValueError, IndexError):
                continue
    
    return times, m_lost_percents, exhausted_tubes_pcts


def plot_metrics(times, m_lost_percents, exhausted_tubes_pcts, filename):
    """Create a dual-axis plot for the two metrics."""
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Plot m_lost_percent on primary y-axis
    color1 = 'tab:red'
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', color=color1, fontsize=12)
    line1 = ax1.plot(times, m_lost_percents, color=color1, linewidth=2, 
                     label='Lost Objects %', marker='o', markersize=2, alpha=0.7)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Create second y-axis for exhausted_tubes_pct
    ax2 = ax1.twinx()
    color2 = 'tab:blue'
    ax2.set_ylabel('Exhausted Tubes (%)', color=color2, fontsize=12)
    line2 = ax2.plot(times, exhausted_tubes_pcts, color=color2, linewidth=2,
                     label='Exhausted Tubes %', marker='s', markersize=2, alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    plt.title(f'Lost Objects % and Exhausted Tubes % Over Time\n{snapshot_name}', 
              fontsize=14, fontweight='bold', pad=20)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=10)
    
    # Set x-axis to start at 0 and go to the maximum time in the data
    ax1.set_xlim(0, max(times))
    
    # Set both y-axes to start at 0
    ax1.set_ylim(0, max(m_lost_percents) * 1.1)  # Add 10% padding at top
    ax2.set_ylim(0, max(exhausted_tubes_pcts) * 1.1)  # Add 10% padding at top
    
    # Adjust layout
    fig.tight_layout()
    
    # Save the figure
    output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_metrics'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{snapshot_name}_metrics.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_snapshot_metrics.py <snapshot_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"Reading snapshot file: {filepath}")
    times, m_lost_percents, exhausted_tubes_pcts = parse_snapshot_file(filepath)
    
    if not times:
        print("Error: No valid data found in file")
        sys.exit(1)
    
    print(f"Found {len(times)} data points")
    print(f"Time range: {times[0]:.2f} to {times[-1]:.2f} years")
    print(f"Lost Objects % range: {min(m_lost_percents):.4f}% to {max(m_lost_percents):.4f}%")
    print(f"Exhausted Tubes % range: {min(exhausted_tubes_pcts):.2f}% to {max(exhausted_tubes_pcts):.2f}%")
    
    output_path = plot_metrics(times, m_lost_percents, exhausted_tubes_pcts, filepath)
    print(f"\nVisualization complete!")


if __name__ == "__main__":
    main()

