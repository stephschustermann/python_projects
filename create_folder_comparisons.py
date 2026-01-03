#!/usr/bin/env python3
"""
Create comparison visualizations across multiple directories for the same configuration.
Each comparison will show the same metrics for pairwise_clustered_random, pairwise_copysets, and pairwise_random.
"""

import matplotlib.pyplot as plt
import os
import glob
import re


def parse_snapshot_file(filepath):
    """Parse a snapshot file and extract all required metrics."""
    
    times = []
    wet_tubes_pct = []
    m_lost_percent = []
    exhausted_tubes_pct = []
    objects_in_cache_pct = []
    objects_2_replicas_pct = []
    objects_1_replicas_pct = []
    objects_0_replicas_pct = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        for line in lines[3:]:
            parts = [p.strip() for p in line.split(',')]
            parts = [p for p in parts if p]
            
            if len(parts) < 18:
                continue
            
            try:
                time_stamp = int(parts[0])
                m_lost = float(parts[9])
                wet_tubes = float(parts[12])
                exhausted = float(parts[13])
                cache = float(parts[14])
                replicas_2 = float(parts[15])
                replicas_1 = float(parts[16])
                replicas_0 = float(parts[17])
                
                times.append(time_stamp)
                wet_tubes_pct.append(wet_tubes)
                m_lost_percent.append(m_lost)
                exhausted_tubes_pct.append(exhausted)
                objects_in_cache_pct.append(cache)
                objects_2_replicas_pct.append(replicas_2)
                objects_1_replicas_pct.append(replicas_1)
                objects_0_replicas_pct.append(replicas_0)
            except (ValueError, IndexError):
                continue
    
    # Normalize time to 10 years
    if times:
        max_time = max(times)
        times = [(t / max_time) * 10.0 for t in times]
    
    return (times, wet_tubes_pct, m_lost_percent, exhausted_tubes_pct,
            objects_in_cache_pct, objects_2_replicas_pct, objects_1_replicas_pct, objects_0_replicas_pct)


def extract_config_from_filename(filename):
    """Extract configuration parameters from filename."""
    # Pattern: maxReads_XXX_accessRate_XXX_dist_XXX_TIMESTAMP.txt
    # We only care about the configuration, not the timestamp
    # Use [A-Za-z]+ instead of \w+ to match only letters (not digits or underscores)
    match = re.search(r'maxReads_(\d+)_accessRate_(\d+)_dist_([A-Za-z]+)', filename)
    if match:
        max_reads = match.group(1)
        access_rate = match.group(2)
        dist = match.group(3)
        return {
            'maxReads': max_reads,
            'accessRate': access_rate,
            'dist': dist,
            'config_key': f"maxReads_{max_reads}_accessRate_{access_rate}_dist_{dist}"
        }
    return None


def find_matching_files(base_dir, directories):
    """Find matching configuration files across directories."""
    
    configs = {}
    
    for dir_name in directories:
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.exists(dir_path):
            continue
        
        files = glob.glob(os.path.join(dir_path, '*.txt'))
        
        for filepath in files:
            filename = os.path.basename(filepath)
            config = extract_config_from_filename(filename)
            
            if config:
                # Use ONLY the config_key (without timestamp) as the dictionary key
                config_key = config['config_key']
                
                if config_key not in configs:
                    configs[config_key] = {
                        'maxReads': config['maxReads'],
                        'accessRate': config['accessRate'],
                        'dist': config['dist'],
                        'files': {}
                    }
                
                # Store the file path for this directory
                configs[config_key]['files'][dir_name] = filepath
    
    return configs


def plot_comparison(config_data, config_key, directories, output_dir):
    """Create comparison plot for a specific configuration across directories."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
    
    # Dynamic colors - assign colors based on available directories
    color_palette = ['tab:blue', 'tab:green', 'tab:orange', 'tab:red', 'tab:purple', 'tab:brown']
    colors = {}
    for i, dir_name in enumerate(directories):
        colors[dir_name] = color_palette[i % len(color_palette)]
    
    # Create readable labels from directory names
    labels = {}
    for dir_name in directories:
        # Convert directory name to readable label
        # e.g., "pairwise_clustered_random" -> "Clustered Random"
        # e.g., "triplets_copysets" -> "Copysets"
        parts = dir_name.split('_')
        if 'clustered' in parts and 'random' in parts:
            labels[dir_name] = 'Clustered Random'
        elif 'copysets' in parts:
            labels[dir_name] = 'Copysets'
        elif 'random' in parts:
            labels[dir_name] = 'Random'
        else:
            # Fallback: capitalize and join
            labels[dir_name] = ' '.join(word.capitalize() for word in parts)
    
    # Parse data for all directories
    all_data = {}
    for dir_name in directories:
        if dir_name in config_data['files']:
            filepath = config_data['files'][dir_name]
            data = parse_snapshot_file(filepath)
            all_data[dir_name] = data
    
    if not all_data:
        return None
    
    # === SUBPLOT 1: Lost Objects % ===
    for dir_name, data in all_data.items():
        times, _, m_lost, _, _, _, _, _ = data
        ax1.plot(times, m_lost, color=colors[dir_name], linewidth=2,
                label=labels[dir_name], alpha=0.8)
    
    ax1.set_xlabel('Time (years)', fontsize=10)
    ax1.set_ylabel('Lost Objects (%)', fontsize=10)
    ax1.set_title('Lost Objects %', fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, None)
    
    # === SUBPLOT 2: Exhausted Tubes % ===
    for dir_name, data in all_data.items():
        times, _, _, exhausted, _, _, _, _ = data
        ax2.plot(times, exhausted, color=colors[dir_name], linewidth=2,
                label=labels[dir_name], alpha=0.8)
    
    ax2.set_xlabel('Time (years)', fontsize=10)
    ax2.set_ylabel('Exhausted Tubes (%)', fontsize=10)
    ax2.set_title('Exhausted Tubes %', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, None)
    
    # === SUBPLOT 3: Objects in Cache % ===
    for dir_name, data in all_data.items():
        times, _, _, _, cache, _, _, _ = data
        ax3.plot(times, cache, color=colors[dir_name], linewidth=2,
                label=labels[dir_name], alpha=0.8)
    
    ax3.set_xlabel('Time (years)', fontsize=10)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=10)
    ax3.set_title('Objects in Cache %', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, None)
    
    # === SUBPLOT 4: 0 Replicas % (Lost) ===
    for dir_name, data in all_data.items():
        times, _, _, _, _, _, _, rep0 = data
        ax4.plot(times, rep0, color=colors[dir_name], linewidth=2,
                label=labels[dir_name], alpha=0.8)
    
    ax4.set_xlabel('Time (years)', fontsize=10)
    ax4.set_ylabel('Objects with 0 Replicas (%)', fontsize=10)
    ax4.set_title('Objects with 0 Replicas %', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=9)
    ax4.set_xlim(0, 10)
    ax4.set_ylim(0, None)
    
    # Overall title
    title = f"Comparison: maxReads={config_data['maxReads']}, accessRate={config_data['accessRate']}, dist={config_data['dist']}"
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
    
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
        # Expecting comma-separated directory names
        directories = sys.argv[1].split(',')
        # Use first directory name as part of output folder
        output_subdir = directories[0].split('_')[0] + '_comparisons'
    else:
        directories = ['pairwise_clustered_random', 'pairwise_copysets', 'pairwise_random']
        output_subdir = 'pairwise_comparisons'
    
    output_dir = f'/Users/stephanie.schustermann/tesis/python_projects/output/{output_subdir}'
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("Creating Folder Comparison Visualizations")
    print("=" * 70)
    print(f"Comparing directories: {', '.join(directories)}")
    print(f"Output directory: {output_dir}\n")
    
    # Find all matching configurations
    configs = find_matching_files(base_input, directories)
    
    print(f"Found {len(configs)} unique configurations\n")
    
    success_count = 0
    
    # Sort configs by key
    for i, (config_key, config_data) in enumerate(sorted(configs.items()), 1):
        print(f"[{i}/{len(configs)}] Config: {config_key}")
        
        # Check how many directories have this config
        available_dirs = list(config_data['files'].keys())
        print(f"  Available in: {', '.join(available_dirs)}")
        
        if len(available_dirs) < 2:
            print(f"  ⚠ Skipping: Only available in {len(available_dirs)} directory")
            continue
        
        try:
            output_path = plot_comparison(config_data, config_key, directories, output_dir)
            if output_path:
                print(f"  ✓ Saved: {os.path.basename(output_path)}\n")
                success_count += 1
        except Exception as e:
            print(f"  ✗ Error: {str(e)}\n")
    
    print("=" * 70)
    print(f"Processing complete!")
    print(f"  Successful: {success_count} comparison files")
    print("=" * 70)


if __name__ == "__main__":
    main()

