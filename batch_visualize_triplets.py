#!/usr/bin/env python3
"""
Batch process triplets snapshot files with support for:
- objects_3_replicas_pct (triplets_random)
- copysets_3_active_pct, copysets_2_active_pct, etc. (triplets_copysets)
- objects_2_replicas_pct (triplets_clustered_random - max 2 replicas)

Graph 1: Objects in Cache + Replica Distribution (2 or 3 replicas)
Graph 2: Wet Tubes + Lost Objects + Exhausted Tubes
"""

import matplotlib.pyplot as plt
import os
import glob


def detect_columns(filepath):
    """Detect which column structure the file uses."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
        if len(lines) < 3:
            return None
        
        header = lines[2].strip()
        
        # Check for copysets format
        if 'copysets_3_active_pct' in header:
            return 'copysets'
        # Check for 3-replica format
        elif 'objects_3_replicas_pct' in header:
            return 'triplets'
        # Check for 2-replica format (pairwise or triplets_clustered_random)
        elif 'objects_2_replicas_pct' in header:
            return 'pairwise'
        
        return None


def parse_snapshot_file(filepath):
    """Parse a snapshot file and extract all required metrics."""
    
    column_type = detect_columns(filepath)
    if column_type is None:
        return None
    
    times = []
    # Graph 2 metrics
    wet_tubes_pct = []
    m_lost_percent = []
    exhausted_tubes_pct = []
    # Graph 1 metrics
    objects_in_cache_pct = []
    objects_3_replicas_pct = []
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
            
            if len(parts) < 15:
                continue
            
            try:
                time_stamp = int(parts[0])  # time in simulation units
                m_lost = float(parts[9])  # m_lost_percent
                wet_tubes = float(parts[12])  # wet_tubes_pct
                exhausted = float(parts[13])  # exhausted_tubes_pct
                cache = float(parts[14])  # objects_in_cache_pct
                
                # Store raw time stamps - we'll normalize later
                times.append(time_stamp)
                wet_tubes_pct.append(wet_tubes)
                m_lost_percent.append(m_lost)
                exhausted_tubes_pct.append(exhausted)
                objects_in_cache_pct.append(cache)
                
                # Parse replica columns based on type
                if column_type == 'triplets':
                    # objects_3_replicas_pct, objects_2_replicas_pct, objects_1_replicas_pct, objects_0_replicas_pct
                    replicas_3 = float(parts[15])
                    replicas_2 = float(parts[16])
                    replicas_1 = float(parts[17])
                    replicas_0 = float(parts[18])
                elif column_type == 'copysets':
                    # copysets_3_active_pct, copysets_2_active_pct, copysets_1_active_pct, copysets_0_active_pct
                    replicas_3 = float(parts[15])
                    replicas_2 = float(parts[16])
                    replicas_1 = float(parts[17])
                    replicas_0 = float(parts[18])
                else:  # pairwise (max 2 replicas)
                    # objects_2_replicas_pct, objects_1_replicas_pct, objects_0_replicas_pct
                    replicas_3 = 0.0  # No 3-replica data
                    replicas_2 = float(parts[15])
                    replicas_1 = float(parts[16])
                    replicas_0 = float(parts[17])
                
                objects_3_replicas_pct.append(replicas_3)
                objects_2_replicas_pct.append(replicas_2)
                objects_1_replicas_pct.append(replicas_1)
                objects_0_replicas_pct.append(replicas_0)
                
            except (ValueError, IndexError) as e:
                continue
    
    # Normalize time to 10 years: find max time and scale to 10
    if times:
        max_time = max(times)
        times = [(t / max_time) * 10.0 for t in times]
    
    return {
        'times': times,
        'wet_tubes_pct': wet_tubes_pct,
        'm_lost_percent': m_lost_percent,
        'exhausted_tubes_pct': exhausted_tubes_pct,
        'objects_in_cache_pct': objects_in_cache_pct,
        'objects_3_replicas_pct': objects_3_replicas_pct,
        'objects_2_replicas_pct': objects_2_replicas_pct,
        'objects_1_replicas_pct': objects_1_replicas_pct,
        'objects_0_replicas_pct': objects_0_replicas_pct,
        'column_type': column_type
    }


def plot_metrics(data, filename, output_dir):
    """Create two subplots with reorganized metrics."""
    
    times = data['times']
    wet_tubes_pct = data['wet_tubes_pct']
    m_lost_percent = data['m_lost_percent']
    exhausted_tubes_pct = data['exhausted_tubes_pct']
    objects_in_cache_pct = data['objects_in_cache_pct']
    objects_3_replicas_pct = data['objects_3_replicas_pct']
    objects_2_replicas_pct = data['objects_2_replicas_pct']
    objects_1_replicas_pct = data['objects_1_replicas_pct']
    objects_0_replicas_pct = data['objects_0_replicas_pct']
    column_type = data['column_type']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # === SUBPLOT 1: Objects in Cache + Replica Distribution ===
    color1 = 'tab:orange'
    ax1.set_xlabel('Time (years)', fontsize=11)
    ax1.set_ylabel('Objects (%)', fontsize=11)
    
    # Plot cache on primary axis
    line1 = ax1.plot(times, objects_in_cache_pct, color=color1, linewidth=2.5,
                     label='Objects in Cache %', marker='o', markersize=1.5, alpha=0.8, zorder=5)
    
    lines_replica = []
    
    # Plot replica distribution based on column type
    if column_type in ['triplets', 'copysets']:
        # Has 3 replicas
        line_r3 = ax1.plot(times, objects_3_replicas_pct, color='tab:cyan', linewidth=2,
                         label='3 Replicas %' if column_type == 'triplets' else '3 Active Copysets %', 
                         marker='d', markersize=1.2, alpha=0.7)
        lines_replica.extend(line_r3)
    
    line_r2 = ax1.plot(times, objects_2_replicas_pct, color='tab:green', linewidth=2,
                     label='2 Replicas %' if column_type != 'copysets' else '2 Active Copysets %', 
                     marker='s', markersize=1.2, alpha=0.7)
    line_r1 = ax1.plot(times, objects_1_replicas_pct, color='tab:blue', linewidth=2,
                     label='1 Replica %' if column_type != 'copysets' else '1 Active Copyset %', 
                     marker='^', markersize=1.2, alpha=0.7)
    line_r0 = ax1.plot(times, objects_0_replicas_pct, color='tab:red', linewidth=2,
                     label='0 Replicas % (Lost)' if column_type != 'copysets' else '0 Active Copysets %', 
                     marker='v', markersize=1.2, alpha=0.7)
    
    lines_replica.extend(line_r2 + line_r1 + line_r0)
    
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='y')
    
    # Legend for subplot 1
    lines1 = line1 + lines_replica
    labels1 = [l.get_label() for l in lines1]
    ax1.legend(lines1, labels1, loc='best', fontsize=9, ncol=2)
    
    # Set axes
    ax1.set_xlim(0, 10)
    max_cache = max(objects_in_cache_pct) if objects_in_cache_pct else 1
    max_replicas = max(
        max(objects_3_replicas_pct) if objects_3_replicas_pct else 0,
        max(objects_2_replicas_pct) if objects_2_replicas_pct else 0,
        max(objects_1_replicas_pct) if objects_1_replicas_pct else 0,
        max(objects_0_replicas_pct) if objects_0_replicas_pct else 0
    )
    ax1.set_ylim(0, max(max_cache, max_replicas) * 1.1)
    
    ax1.set_title('Cache and Replica Distribution', fontsize=12, fontweight='bold', pad=10)
    
    # === SUBPLOT 2: Wet Tubes + Lost Objects + Exhausted Tubes ===
    ax2.set_xlabel('Time (years)', fontsize=11)
    ax2.set_ylabel('Percentage (%)', fontsize=11)
    
    # Plot all three metrics
    line5 = ax2.plot(times, wet_tubes_pct, color='tab:blue', linewidth=2,
                     label='Wet Tubes %', marker='o', markersize=1.5, alpha=0.7)
    line6 = ax2.plot(times, m_lost_percent, color='tab:red', linewidth=2,
                     label='Lost Objects %', marker='s', markersize=1.5, alpha=0.7)
    line7 = ax2.plot(times, exhausted_tubes_pct, color='tab:purple', linewidth=2,
                     label='Exhausted Tubes %', marker='^', markersize=1.5, alpha=0.7)
    
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='y')
    
    # Legend for subplot 2
    lines2 = line5 + line6 + line7
    labels2 = [l.get_label() for l in lines2]
    ax2.legend(lines2, labels2, loc='best', fontsize=9)
    
    # Set axes
    ax2.set_xlim(0, 10)
    max_tubes = max(
        max(wet_tubes_pct) if wet_tubes_pct else 0,
        max(m_lost_percent) if m_lost_percent else 0,
        max(exhausted_tubes_pct) if exhausted_tubes_pct else 0
    )
    ax2.set_ylim(0, max(max_tubes * 1.1, 1))
    
    ax2.set_title('Wet Tubes, Lost Objects, and Exhausted Tubes', fontsize=12, fontweight='bold', pad=10)
    
    # Overall title
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    fig.suptitle(f'{snapshot_name}', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save the figure
    output_path = os.path.join(output_dir, f'{snapshot_name}_complete_metrics.png')
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
            data = parse_snapshot_file(filepath)
            
            if data is None or not data['times']:
                print(f"  ⚠ Warning: No valid data found in {filename}")
                error_count += 1
                continue
            
            output_path = plot_metrics(data, filepath, output_dir)
            
            print(f"  ✓ Saved: {os.path.basename(output_path)}")
            print(f"    Column type: {data['column_type']}, Data points: {len(data['times'])}, Time range: {data['times'][0]:.2f} to {data['times'][-1]:.2f} years\n")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {filename}: {str(e)}\n")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print("=" * 70)
    print(f"Processing complete!")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(files)}")
    print("=" * 70)


def main():
    import sys
    
    # Check if directory argument provided
    if len(sys.argv) > 1:
        dir_name = sys.argv[1]
    else:
        print("Usage: python batch_visualize_triplets.py <directory_name>")
        print("Example: python batch_visualize_triplets.py triplets_random")
        sys.exit(1)
    
    # Define paths
    base_input = '/Users/stephanie.schustermann/tesis/python_projects/input/snaps'
    base_output = '/Users/stephanie.schustermann/tesis/python_projects/output/complete_metrics'
    
    input_dir = os.path.join(base_input, dir_name)
    output_dir = os.path.join(base_output, dir_name)
    
    print("=" * 70)
    print("Triplets Snapshot Metrics Visualization")
    print("=" * 70)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 70 + "\n")
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()




