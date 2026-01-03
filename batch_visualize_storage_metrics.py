#!/usr/bin/env python3
"""
Batch process snapshot files to visualize wet_tubes_pct, objects_in_cache_pct, 
and replica distribution (objects_2_replicas_pct, objects_1_replicas_pct, objects_0_replicas_pct).
"""

import matplotlib.pyplot as plt
import os
import glob


def parse_snapshot_file(filepath):
    """Parse a snapshot file and extract time and various metrics."""
    
    times = []
    wet_tubes_pct = []
    objects_in_cache_pct = []
    objects_2_replicas_pct = []
    objects_1_replicas_pct = []
    objects_0_replicas_pct = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Skip the first 2 header lines and the column headers
        for line in lines[3:]:
            parts = [p.strip() for p in line.split(',')]
            # Filter out empty parts
            parts = [p for p in parts if p]
            
            if len(parts) < 18:
                continue
            
            try:
                time_stamp = int(parts[0])  # time in simulation units
                wet_tubes = float(parts[12])  # wet_tubes_pct
                cache = float(parts[14])  # objects_in_cache_pct
                replicas_2 = float(parts[15])  # objects_2_replicas_pct
                replicas_1 = float(parts[16])  # objects_1_replicas_pct
                replicas_0 = float(parts[17])  # objects_0_replicas_pct
                
                # Store raw time stamps - we'll normalize later
                times.append(time_stamp)
                wet_tubes_pct.append(wet_tubes)
                objects_in_cache_pct.append(cache)
                objects_2_replicas_pct.append(replicas_2)
                objects_1_replicas_pct.append(replicas_1)
                objects_0_replicas_pct.append(replicas_0)
            except (ValueError, IndexError):
                continue
    
    # Normalize time to 10 years: find max time and scale to 10
    if times:
        max_time = max(times)
        times = [(t / max_time) * 10.0 for t in times]
    
    return times, wet_tubes_pct, objects_in_cache_pct, objects_2_replicas_pct, objects_1_replicas_pct, objects_0_replicas_pct


def plot_metrics(times, wet_tubes_pct, objects_in_cache_pct, objects_2_replicas_pct, 
                 objects_1_replicas_pct, objects_0_replicas_pct, filename, output_dir):
    """Create two subplots: one for wet_tubes vs cache, another for replica distribution."""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # === SUBPLOT 1: Wet Tubes vs Objects in Cache ===
    color1 = 'tab:blue'
    ax1.set_xlabel('Time (years)', fontsize=11)
    ax1.set_ylabel('Wet Tubes (%)', color=color1, fontsize=11)
    line1 = ax1.plot(times, wet_tubes_pct, color=color1, linewidth=2, 
                     label='Wet Tubes %', marker='o', markersize=1.5, alpha=0.7)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Second y-axis for objects in cache
    ax1_twin = ax1.twinx()
    color2 = 'tab:orange'
    ax1_twin.set_ylabel('Objects in Cache (%)', color=color2, fontsize=11)
    line2 = ax1_twin.plot(times, objects_in_cache_pct, color=color2, linewidth=2,
                          label='Objects in Cache %', marker='s', markersize=1.5, alpha=0.7)
    ax1_twin.tick_params(axis='y', labelcolor=color2)
    
    # Combine legends for subplot 1
    lines1 = line1 + line2
    labels1 = [l.get_label() for l in lines1]
    ax1.legend(lines1, labels1, loc='upper left', fontsize=9)
    
    # Set x-axis to 0-10 years
    ax1.set_xlim(0, 10)
    
    # Set both y-axes to start at 0
    max_wet = max(wet_tubes_pct) if wet_tubes_pct else 1
    max_cache = max(objects_in_cache_pct) if objects_in_cache_pct else 1
    ax1.set_ylim(0, max_wet * 1.1)
    ax1_twin.set_ylim(0, max_cache * 1.1)
    
    ax1.set_title('Wet Tubes % vs Objects in Cache %', fontsize=12, fontweight='bold', pad=10)
    
    # === SUBPLOT 2: Replica Distribution ===
    ax2.set_xlabel('Time (years)', fontsize=11)
    ax2.set_ylabel('Objects (%)', fontsize=11)
    
    # Plot all three replica types
    line3 = ax2.plot(times, objects_2_replicas_pct, color='tab:green', linewidth=2,
                     label='2 Replicas %', marker='o', markersize=1.5, alpha=0.7)
    line4 = ax2.plot(times, objects_1_replicas_pct, color='tab:red', linewidth=2,
                     label='1 Replica %', marker='s', markersize=1.5, alpha=0.7)
    line5 = ax2.plot(times, objects_0_replicas_pct, color='tab:purple', linewidth=2,
                     label='0 Replicas %', marker='^', markersize=1.5, alpha=0.7)
    
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='y')
    
    # Legend for subplot 2
    ax2.legend(loc='best', fontsize=9)
    
    # Set x-axis to 0-10 years
    ax2.set_xlim(0, 10)
    
    # Set y-axis to start at 0
    max_replicas = max(
        max(objects_2_replicas_pct) if objects_2_replicas_pct else 0,
        max(objects_1_replicas_pct) if objects_1_replicas_pct else 0,
        max(objects_0_replicas_pct) if objects_0_replicas_pct else 0
    )
    ax2.set_ylim(0, max(max_replicas * 1.1, 1))
    
    ax2.set_title('Replica Distribution Over Time', fontsize=12, fontweight='bold', pad=10)
    
    # Overall title
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    fig.suptitle(f'Storage Metrics: {snapshot_name}', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{snapshot_name}_storage_metrics.png')
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
            times, wet_tubes, cache, rep2, rep1, rep0 = parse_snapshot_file(filepath)
            
            if not times:
                print(f"  ⚠ Warning: No valid data found in {filename}")
                error_count += 1
                continue
            
            output_path = plot_metrics(times, wet_tubes, cache, rep2, rep1, rep0, 
                                      filepath, output_dir)
            
            print(f"  ✓ Saved: {os.path.basename(output_path)}")
            print(f"    Data points: {len(times)}, Time range: {times[0]:.2f} to {times[-1]:.2f} years")
            print(f"    Wet Tubes %: {min(wet_tubes):.2f}% to {max(wet_tubes):.2f}%")
            print(f"    Cache %: {min(cache):.4f}% to {max(cache):.4f}%")
            print(f"    2 Replicas %: {min(rep2):.2f}% to {max(rep2):.2f}%")
            print(f"    0 Replicas %: {min(rep0):.2f}% to {max(rep0):.2f}%\n")
            
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
    output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_storage_metrics/clustered_random_pairwise'
    
    print("=" * 70)
    print("Batch Snapshot Storage Metrics Visualization")
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

