#!/usr/bin/env python3
"""
Create comparison graphs across triplets folders.
Handles different column structures:
- triplets_random: objects_3_replicas_pct
- triplets_copysets: copysets_3_active_pct
- triplets_clustered_random: only 2 replicas (pairwise format)
"""

import matplotlib.pyplot as plt
import os
import glob
import re
from collections import defaultdict


def extract_config_from_filename(filename):
    """Extract configuration parameters from filename, excluding timestamp."""
    match = re.search(r'maxReads_(\d+)_accessRate_(\d+)_dist_([A-Za-z]+)', filename)
    if match:
        return f"maxReads_{match.group(1)}_accessRate_{match.group(2)}_dist_{match.group(3)}"
    return None


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
    """Parse a snapshot file and extract comparison metrics."""
    
    column_type = detect_columns(filepath)
    if column_type is None:
        return None
    
    times = []
    m_lost_percent = []
    wet_tubes_pct = []
    objects_in_cache_pct = []
    objects_0_replicas_pct = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Skip the first 2 header lines and the column headers
        for line in lines[3:]:
            parts = [p.strip() for p in line.split(',')]
            parts = [p for p in parts if p]
            
            if len(parts) < 15:
                continue
            
            try:
                time_stamp = int(parts[0])
                m_lost = float(parts[9])
                wet_tubes = float(parts[12])
                cache = float(parts[14])
                
                # Get 0-replicas column based on type
                if column_type == 'triplets':
                    replicas_0 = float(parts[18])  # objects_0_replicas_pct
                elif column_type == 'copysets':
                    replicas_0 = float(parts[18])  # copysets_0_active_pct
                else:  # pairwise
                    replicas_0 = float(parts[17])  # objects_0_replicas_pct
                
                times.append(time_stamp)
                m_lost_percent.append(m_lost)
                wet_tubes_pct.append(wet_tubes)
                objects_in_cache_pct.append(cache)
                objects_0_replicas_pct.append(replicas_0)
                
            except (ValueError, IndexError):
                continue
    
    # Normalize time to 10 years
    if times:
        max_time = max(times)
        times = [(t / max_time) * 10.0 for t in times]
    
    return {
        'times': times,
        'm_lost_percent': m_lost_percent,
        'wet_tubes_pct': wet_tubes_pct,
        'objects_in_cache_pct': objects_in_cache_pct,
        'objects_0_replicas_pct': objects_0_replicas_pct
    }


def plot_comparison(config_data, config_key, directories, output_dir):
    """Create comparison plot for a specific configuration across directories."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
    
    # Dynamic colors
    color_palette = ['tab:blue', 'tab:green', 'tab:orange', 'tab:red', 'tab:purple', 'tab:brown']
    colors = {}
    for i, dir_name in enumerate(directories):
        colors[dir_name] = color_palette[i % len(color_palette)]
    
    # Create readable labels with cluster sizes
    labels = {}
    for dir_name in directories:
        parts = dir_name.split('_')
        if 'big' in parts and 'cluster' in parts:
            labels[dir_name] = 'Clustered Random (cluster size 507)'
        elif 'small' in parts and 'cluster' in parts:
            labels[dir_name] = 'Clustered Random (cluster size 3)'
        elif 'clustered' in parts and 'random' in parts:
            labels[dir_name] = 'Clustered Random (cluster size 9)'
        elif 'copysets' in parts:
            labels[dir_name] = 'Copysets'
        elif 'random' in parts and 'clustered' not in parts:
            labels[dir_name] = 'Random'
        else:
            labels[dir_name] = ' '.join(word.capitalize() for word in parts)
    
    # Plot each directory's data
    for dir_name in directories:
        if dir_name not in config_data:
            continue
        
        data = config_data[dir_name]
        color = colors[dir_name]
        label = labels[dir_name]
        
        # Subplot 1: Lost Objects %
        ax1.plot(data['times'], data['m_lost_percent'], 
                color=color, label=label, linewidth=2, alpha=0.8)
        
        # Subplot 2: Wet Tubes %
        ax2.plot(data['times'], data['wet_tubes_pct'],
                color=color, label=label, linewidth=2, alpha=0.8)
        
        # Subplot 3: Objects in Cache %
        ax3.plot(data['times'], data['objects_in_cache_pct'],
                color=color, label=label, linewidth=2, alpha=0.8)
        
        # Subplot 4: Objects with 0 Replicas %
        ax4.plot(data['times'], data['objects_0_replicas_pct'],
                color=color, label=label, linewidth=2, alpha=0.8)
    
    # Configure subplots
    for ax, title in [(ax1, 'Lost Objects %'), 
                      (ax2, 'Wet Tubes %'),
                      (ax3, 'Objects in Cache %'),
                      (ax4, 'Objects with 0 Replicas %')]:
        ax.set_xlabel('Time (years)', fontsize=11)
        ax.set_ylabel('Percentage (%)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        ax.set_xlim(0, 10)
        ax.set_ylim(bottom=0)
    
    # Overall title
    fig.suptitle(f'Comparison: {config_key}', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save
    output_path = os.path.join(output_dir, f'comparison_{config_key}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def main():
    import sys
    
    base_input = '/Users/stephanie.schustermann/tesis/python_projects/input/snaps'
    
    # Check if custom directories provided
    if len(sys.argv) > 1:
        directories = sys.argv[1].split(',')
        output_subdir = directories[0].split('_')[0] + '_comparisons'
    else:
        directories = ['triplets_clustered_random', 'triplets_copysets', 'triplets_random']
        output_subdir = 'triplets_comparisons'
    
    output_dir = f'/Users/stephanie.schustermann/tesis/python_projects/output/{output_subdir}'
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("Creating Folder Comparison Visualizations")
    print("=" * 70)
    print(f"Comparing directories: {', '.join(directories)}")
    print(f"Output directory: {output_dir}\n")
    
    # Collect all files by configuration
    configs = defaultdict(dict)
    
    for dir_name in directories:
        input_dir = os.path.join(base_input, dir_name)
        
        if not os.path.exists(input_dir):
            print(f"Warning: Directory not found: {input_dir}")
            continue
        
        files = glob.glob(os.path.join(input_dir, '*.txt'))
        
        for filepath in files:
            filename = os.path.basename(filepath)
            config_key = extract_config_from_filename(filename)
            
            if config_key:
                configs[config_key][dir_name] = filepath
    
    print(f"Found {len(configs)} unique configurations\n")
    
    # Process each configuration
    success_count = 0
    
    for i, (config_key, dir_files) in enumerate(sorted(configs.items()), 1):
        print(f"[{i}/{len(configs)}] Config: {config_key}")
        
        # Check which directories have this config
        available_dirs = list(dir_files.keys())
        print(f"  Available in: {', '.join(available_dirs)}")
        
        if len(available_dirs) < 2:
            print(f"  ⚠ Skipping: Only available in {len(available_dirs)} directory")
            continue
        
        try:
            # Parse data from each directory
            config_data = {}
            
            for dir_name, filepath in dir_files.items():
                data = parse_snapshot_file(filepath)
                if data and data['times']:
                    config_data[dir_name] = data
            
            if len(config_data) < 2:
                print(f"  ⚠ Skipping: Valid data only in {len(config_data)} directory")
                continue
            
            # Create comparison plot
            output_path = plot_comparison(config_data, config_key, directories, output_dir)
            print(f"  ✓ Saved: {os.path.basename(output_path)}\n")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print(f"Processing complete!")
    print(f"  Successful: {success_count} comparison files")
    print("=" * 70)


if __name__ == "__main__":
    main()

