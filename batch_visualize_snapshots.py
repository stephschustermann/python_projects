#!/usr/bin/env python3
"""
Batch process snapshot files to visualize m_lost_percent and exhausted_tubes_pct over time.
"""

import matplotlib.pyplot as plt
import os
import glob


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
                time_stamp = int(parts[0])  # time in simulation units
                m_lost_percent = float(parts[9])  # m_lost_percent
                exhausted_tubes_pct = float(parts[13])  # exhausted_tubes_pct
                
                # Store raw time stamps - we'll normalize later
                times.append(time_stamp)
                m_lost_percents.append(m_lost_percent)
                exhausted_tubes_pcts.append(exhausted_tubes_pct)
            except (ValueError, IndexError):
                continue
    
    # Normalize time to 10 years: find max time and scale to 10
    if times:
        max_time = max(times)
        times = [(t / max_time) * 10.0 for t in times]
    
    return times, m_lost_percents, exhausted_tubes_pcts


def plot_metrics(times, m_lost_percents, exhausted_tubes_pcts, filename, output_dir):
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
    
    # Set x-axis to show 0 to 10 years
    ax1.set_xlim(0, 10)
    
    # Set both y-axes to start at 0
    max_lost = max(m_lost_percents) if m_lost_percents else 1
    max_exhausted = max(exhausted_tubes_pcts) if exhausted_tubes_pcts else 1
    ax1.set_ylim(0, max_lost * 1.1)  # Add 10% padding at top
    ax2.set_ylim(0, max_exhausted * 1.1)  # Add 10% padding at top
    
    # Adjust layout
    fig.tight_layout()
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{snapshot_name}_metrics.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)  # Close the figure to free memory
    
    return output_path


def process_directory(input_dir, output_dir):
    """Process all .txt files in the input directory."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .txt files in the input directory
    pattern = os.path.join(input_dir, '*.txt')
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"No .txt files found in {input_dir}")
        return
    
    print(f"Found {len(files)} files to process")
    print(f"Output directory: {output_dir}\n")
    
    success_count = 0
    error_count = 0
    
    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i}/{len(files)}] Processing: {filename}")
        
        try:
            times, m_lost_percents, exhausted_tubes_pcts = parse_snapshot_file(filepath)
            
            if not times:
                print(f"  ⚠ Warning: No valid data found in {filename}")
                error_count += 1
                continue
            
            output_path = plot_metrics(times, m_lost_percents, exhausted_tubes_pcts, filepath, output_dir)
            
            print(f"  ✓ Saved: {os.path.basename(output_path)}")
            print(f"    Data points: {len(times)}, Time range: {times[0]:.2f} to {times[-1]:.2f} years")
            print(f"    Lost Objects %: {min(m_lost_percents):.4f}% to {max(m_lost_percents):.4f}%")
            print(f"    Exhausted Tubes %: {min(exhausted_tubes_pcts):.2f}% to {max(exhausted_tubes_pcts):.2f}%\n")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {filename}: {str(e)}\n")
            error_count += 1
    
    print("=" * 70)
    print(f"Processing complete!")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(files)}")
    print("=" * 70)


def main():
    # Define paths
    input_dir = '/Users/stephanie.schustermann/tesis/python_projects/input/snaps/clustered_random_pairwise'
    output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_metrics/clustered_random_pairwise'
    
    print("=" * 70)
    print("Batch Snapshot Visualization")
    print("=" * 70)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 70 + "\n")
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()

