import matplotlib.pyplot as plt
import numpy as np
import os
import glob

def parse_snapshot_file_detailed(filepath, access_rate=100):
    """Parse a snapshot file and extract multiple metrics over time."""
    time_stamps = []
    lost_objects_pct = []
    wet_tubes_pct = []
    objects_in_cache_pct = []
    tubes_expired_by_time = []
    tubes_expired_by_reads = []
    
    max_reads = None
    initial_tubes = None
    objects_per_tube = None
    
    # Check if file is empty
    if os.path.getsize(filepath) == 0:
        print(f"  WARNING: File is empty, skipping: {os.path.basename(filepath)}")
        return None
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Check if file has enough lines
        if len(lines) < 4:
            print(f"  WARNING: File has insufficient data ({len(lines)} lines), skipping: {os.path.basename(filepath)}")
            return None
        
        # Extract parameters from line 2
        if len(lines) > 1:
            params = [p.strip().rstrip(',') for p in lines[1].strip().split(',')]
            if len(params) >= 8:
                initial_tubes = int(float(params[1]))
                max_reads = int(float(params[3]))
                objects_per_tube = int(float(params[7]))
        
        # Parse data lines (skip header lines)
        for i, line in enumerate(lines[3:], start=3):
            parts = [p.strip().rstrip(',') for p in line.strip().split(',')]
            if len(parts) >= 17:
                try:
                    time_stamp = float(parts[0])
                    lost_pct = float(parts[9])  # m_lost_percent
                    wet_pct = float(parts[14])  # wet_tubes_pct
                    cache_pct = float(parts[16])  # objects_in_cache_pct
                    expired_time = float(parts[12])  # tubes_expired_by_time
                    expired_reads = float(parts[13])  # tubes_expired_by_reads
                    
                    time_stamps.append(time_stamp)
                    lost_objects_pct.append(lost_pct)
                    wet_tubes_pct.append(wet_pct)
                    objects_in_cache_pct.append(cache_pct)
                    tubes_expired_by_time.append(expired_time)
                    tubes_expired_by_reads.append(expired_reads)
                except (ValueError, IndexError):
                    continue
    
    # Check if we got any data
    if len(time_stamps) == 0:
        print(f"  WARNING: No valid data found in file: {os.path.basename(filepath)}")
        return None
    
    # Convert time stamps from reads to years using the correct access rate
    time_in_years = [t / (access_rate * 365) for t in time_stamps]
    
    return {
        'time': time_in_years,
        'lost_objects_pct': lost_objects_pct,
        'wet_tubes_pct': wet_tubes_pct,
        'objects_in_cache_pct': objects_in_cache_pct,
        'tubes_expired_by_time': tubes_expired_by_time,
        'tubes_expired_by_reads': tubes_expired_by_reads,
        'max_reads': max_reads,
        'initial_tubes': initial_tubes,
        'objects_per_tube': objects_per_tube
    }

def get_config_key(filename):
    basename = os.path.basename(filename)
    parts = basename.split('_202')[0]
    return parts

def extract_access_rate(filename):
    """Extract access rate from filename"""
    basename = os.path.basename(filename)
    if 'accessRate_' in basename:
        parts = basename.split('accessRate_')[1].split('_')[0]
        return int(parts)
    return 100

# Four folders to compare
folders = {
    'SHA': '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_sha',
    'Small Cluster': '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_clustered_random_small',
    'Triplets Copysets': '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_triplets_copysets',
    'Tube Replication': '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_tube_replication'
}

# Get files from all folders
all_files = {}
for name, folder in folders.items():
    all_files[name] = sorted(glob.glob(os.path.join(folder, '*.txt')))

# Match files by configuration
file_groups = []
for f1 in all_files['SHA']:
    config = get_config_key(f1)
    group = {'config': config, 'SHA': f1}
    
    # Find matching files in other folders
    for name in ['Small Cluster', 'Triplets Copysets', 'Tube Replication']:
        for f in all_files[name]:
            if get_config_key(f) == config:
                group[name] = f
                break
    
    # Only include if we have at least SHA and one other
    if len(group) >= 3:  # config + SHA + at least one other
        file_groups.append(group)

print(f"Found {len(file_groups)} matching file groups")

# Create output directory
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output/four_way_comparison'
os.makedirs(output_dir, exist_ok=True)

summary_results = []

# Colors for each approach
colors = {
    'SHA': '#A23B72',
    'Small Cluster': '#06A77D',
    'Triplets Copysets': '#F18F01',
    'Tube Replication': '#2E86AB'
}

# Compare each group
for group in file_groups:
    config = group['config']
    print(f"\nComparing: {config}")
    
    access_rate = extract_access_rate(group['SHA'])
    
    # Parse all files, skipping empty ones
    data = {}
    for name in ['SHA', 'Small Cluster', 'Triplets Copysets', 'Tube Replication']:
        if name in group:
            parsed = parse_snapshot_file_detailed(group[name], access_rate)
            if parsed is not None:
                data[name] = parsed
                print(f"  {name}: Tubes={parsed['initial_tubes']}, Cache Max={np.max(parsed['objects_in_cache_pct']):.2f}%")
            else:
                print(f"  {name}: SKIPPED (empty or invalid file)")
    
    # Skip if we don't have enough valid data
    if len(data) < 2:
        print(f"  Skipping {config}: not enough valid files")
        continue
    
    # Store summary results
    result = {'config': config}
    for name in data.keys():
        result[f'{name}_tubes'] = data[name]['initial_tubes']
        result[f'{name}_cache_max'] = np.max(data[name]['objects_in_cache_pct'])
        result[f'{name}_cache_avg'] = np.mean(data[name]['objects_in_cache_pct'])
    summary_results.append(result)
    
    # Create individual comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Four-Way Comparison\n{config}\n(Access Rate: {access_rate} reads/day, 10 years)', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Lost Objects
    ax1 = axes[0, 0]
    for name, d in data.items():
        ax1.plot(d['time'], d['lost_objects_pct'], linewidth=2.5, color=colors[name], 
                 label=f"{name} (Tubes={d['initial_tubes']})", alpha=0.9)
    ax1.set_xlabel('Time (years)', fontsize=11)
    ax1.set_ylabel('Lost Objects (%)', fontsize=11)
    ax1.set_title('Lost Objects %', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=9)
    
    # Plot 2: Wet Tubes
    ax2 = axes[0, 1]
    for name, d in data.items():
        ax2.plot(d['time'], d['wet_tubes_pct'], linewidth=2.5, color=colors[name], 
                 label=name, alpha=0.9)
    ax2.set_xlabel('Time (years)', fontsize=11)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=11)
    ax2.set_title('Wet Tubes %', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best', fontsize=9)
    
    # Plot 3: Objects in Cache
    ax3 = axes[1, 0]
    for name, d in data.items():
        ax3.plot(d['time'], d['objects_in_cache_pct'], linewidth=2.5, color=colors[name], 
                 label=name, alpha=0.9)
    ax3.set_xlabel('Time (years)', fontsize=11)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=11)
    ax3.set_title('Objects in Cache %', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='best', fontsize=9)
    
    # Plot 4: Expired Tubes
    ax4 = axes[1, 1]
    for name, d in data.items():
        # Calculate totals and by-time percentages
        total = [d['tubes_expired_by_time'][i] + d['tubes_expired_by_reads'][i] 
                 for i in range(len(d['time']))]
        pct_total = [(t / d['initial_tubes']) * 100 for t in total]
        pct_by_time = [(t / d['initial_tubes']) * 100 for t in d['tubes_expired_by_time']]
        
        # Plot total (solid) and by time (dashed)
        ax4.plot(d['time'], pct_total, linewidth=2.5, color=colors[name], 
                 label=f"{name} (Total)", alpha=0.9)
        ax4.plot(d['time'], pct_by_time, linewidth=2, color=colors[name], linestyle='--', 
                 label=f"{name} (By Time)", alpha=0.7)
    
    ax4.set_xlabel('Time (years)', fontsize=11)
    ax4.set_ylabel('Expired Tubes (% of Initial)', fontsize=11)
    ax4.set_title('Expired Tubes %', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best', fontsize=8)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'{config}.png')
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    plt.close()

# Create summary chart
print("\n" + "="*80)
print("CREATING SUMMARY COMPARISON")
print("="*80)

if len(summary_results) > 0:
    fig, axes = plt.subplots(2, 2, figsize=(18, 10))
    fig.suptitle('Summary: SHA vs Small Cluster vs Triplets Copysets vs Tube Replication\nAll Configurations', 
                 fontsize=18, fontweight='bold')
    
    configs = [r['config'] for r in summary_results]
    x = np.arange(len(configs))
    width = 0.2
    
    # Determine which approaches we have data for
    approaches = ['SHA', 'Small Cluster', 'Triplets Copysets', 'Tube Replication']
    available_approaches = []
    for approach in approaches:
        if any(f'{approach}_cache_max' in r for r in summary_results):
            available_approaches.append(approach)
    
    # Plot 1: Max Cache %
    ax1 = axes[0, 0]
    for i, approach in enumerate(available_approaches):
        cache_max = [r.get(f'{approach}_cache_max', 0) for r in summary_results]
        offset = (i - len(available_approaches)/2 + 0.5) * width
        ax1.bar(x + offset, cache_max, width, label=approach, color=colors[approach], alpha=0.8)
    ax1.set_ylabel('Max Cache %', fontsize=12, fontweight='bold')
    ax1.set_title('Maximum Cache Percentage', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Plot 2: Avg Cache %
    ax2 = axes[0, 1]
    for i, approach in enumerate(available_approaches):
        cache_avg = [r.get(f'{approach}_cache_avg', 0) for r in summary_results]
        offset = (i - len(available_approaches)/2 + 0.5) * width
        ax2.bar(x + offset, cache_avg, width, label=approach, color=colors[approach], alpha=0.8)
    ax2.set_ylabel('Avg Cache %', fontsize=12, fontweight='bold')
    ax2.set_title('Average Cache Percentage', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # Plot 3: Number of Tubes
    ax3 = axes[1, 0]
    for i, approach in enumerate(available_approaches):
        tubes = [r.get(f'{approach}_tubes', 0) for r in summary_results]
        offset = (i - len(available_approaches)/2 + 0.5) * width
        ax3.bar(x + offset, tubes, width, label=approach, color=colors[approach], alpha=0.8)
    ax3.set_ylabel('Number of Tubes', fontsize=12, fontweight='bold')
    ax3.set_title('Initial Number of Tubes', fontsize=13, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # Plot 4: Cache Ratio Comparison (normalized to SHA)
    ax4 = axes[1, 1]
    sha_cache = [r.get('SHA_cache_max', 1) for r in summary_results]
    for i, approach in enumerate(available_approaches):
        if approach != 'SHA':
            cache_max = [r.get(f'{approach}_cache_max', 0) for r in summary_results]
            ratios = [cache_max[j] / sha_cache[j] if sha_cache[j] > 0 else 1 for j in range(len(sha_cache))]
            offset = (i - len(available_approaches)/2 + 0.5) * width
            ax4.bar(x + offset, ratios, width, label=f'{approach}/SHA', color=colors[approach], alpha=0.8)
    
    ax4.axhline(y=1, color='black', linestyle='--', linewidth=2, label='Equal to SHA')
    ax4.set_ylabel('Ratio', fontsize=12, fontweight='bold')
    ax4.set_title('Cache Performance Ratio vs SHA\n(>1 means better than SHA)', fontsize=13, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    summary_file = os.path.join(output_dir, 'SUMMARY_four_way_comparison.png')
    plt.savefig(summary_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nSummary chart saved to: {summary_file}")
    print(f"Individual comparisons saved to: {output_dir}")
    
    # Print summary table
    print("\n" + "="*140)
    print("SUMMARY TABLE")
    print("="*140)
    header = f"{'Configuration':<45}"
    for approach in available_approaches:
        header += f" {approach:<20}"
    print(header)
    print("-"*140)
    
    for r in summary_results:
        row = f"{r['config']:<45}"
        for approach in available_approaches:
            tubes = r.get(f'{approach}_tubes', 0)
            cache = r.get(f'{approach}_cache_max', 0)
            row += f" T:{tubes:<5} C:{cache:<6.2f}%   "
        print(row)
    print("="*140)
else:
    print("No valid data to create summary comparison")

print("\nComparison complete!")
