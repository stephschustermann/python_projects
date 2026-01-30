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
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
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

# Folders to compare
folder1 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_sha'
folder2 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_clustered_random_small'

# Get all files from both folders
files1 = sorted(glob.glob(os.path.join(folder1, '*.txt')))
files2 = sorted(glob.glob(os.path.join(folder2, '*.txt')))

# Extract configuration from filename
def get_config_key(filename):
    basename = os.path.basename(filename)
    # Extract everything before the timestamp
    parts = basename.split('_202')[0]  # Split before timestamp
    return parts

def extract_access_rate(filename):
    """Extract access rate from filename like 'maxReads_100_accessRate_500_...'"""
    basename = os.path.basename(filename)
    if 'accessRate_' in basename:
        parts = basename.split('accessRate_')[1].split('_')[0]
        return int(parts)
    return 100  # Default

# Match files by configuration
file_pairs = []
for f1 in files1:
    config1 = get_config_key(f1)
    for f2 in files2:
        config2 = get_config_key(f2)
        if config1 == config2:
            file_pairs.append((f1, f2, config1))
            break

print(f"Found {len(file_pairs)} matching file pairs")

# Create summary comparison for all pairs
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output/folder_comparisons'
os.makedirs(output_dir, exist_ok=True)

summary_results = []

for f1, f2, config in file_pairs:
    print(f"\nComparing: {config}")
    
    # Extract access rate from filename
    access_rate1 = extract_access_rate(f1)
    access_rate2 = extract_access_rate(f2)
    
    data1 = parse_snapshot_file_detailed(f1, access_rate1)
    data2 = parse_snapshot_file_detailed(f2, access_rate2)
    
    # Calculate summary statistics
    result = {
        'config': config,
        'sha_tubes': data1['initial_tubes'],
        'clustered_tubes': data2['initial_tubes'],
        'sha_cache_max': np.max(data1['objects_in_cache_pct']),
        'clustered_cache_max': np.max(data2['objects_in_cache_pct']),
        'sha_cache_avg': np.mean(data1['objects_in_cache_pct']),
        'clustered_cache_avg': np.mean(data2['objects_in_cache_pct']),
        'sha_lost_final': data1['lost_objects_pct'][-1] if data1['lost_objects_pct'] else 0,
        'clustered_lost_final': data2['lost_objects_pct'][-1] if data2['lost_objects_pct'] else 0,
    }
    summary_results.append(result)
    
    # Create individual comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Comparison: SHA vs Clustered Random Small\n{config}\n(Access Rate: {access_rate1} reads/day, 10 years)', 
                 fontsize=16, fontweight='bold')
    
    # Colors
    color1 = '#A23B72'  # SHA
    color2 = '#06A77D'  # Clustered
    
    # Plot 1: Lost Objects
    ax1 = axes[0, 0]
    ax1.plot(data1['time'], data1['lost_objects_pct'], linewidth=2.5, color=color1, 
             label=f"SHA (Tubes={data1['initial_tubes']})", alpha=0.9)
    ax1.plot(data2['time'], data2['lost_objects_pct'], linewidth=2.5, color=color2, 
             label=f"Clustered (Tubes={data2['initial_tubes']})", alpha=0.9)
    ax1.set_xlabel('Time (years)', fontsize=11)
    ax1.set_ylabel('Lost Objects (%)', fontsize=11)
    ax1.set_title('Lost Objects %', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=9)
    
    # Plot 2: Wet Tubes
    ax2 = axes[0, 1]
    ax2.plot(data1['time'], data1['wet_tubes_pct'], linewidth=2.5, color=color1, 
             label="SHA", alpha=0.9)
    ax2.plot(data2['time'], data2['wet_tubes_pct'], linewidth=2.5, color=color2, 
             label="Clustered", alpha=0.9)
    ax2.set_xlabel('Time (years)', fontsize=11)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=11)
    ax2.set_title('Wet Tubes %', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best', fontsize=9)
    
    # Plot 3: Objects in Cache
    ax3 = axes[1, 0]
    ax3.plot(data1['time'], data1['objects_in_cache_pct'], linewidth=2.5, color=color1, 
             label="SHA", alpha=0.9)
    ax3.plot(data2['time'], data2['objects_in_cache_pct'], linewidth=2.5, color=color2, 
             label="Clustered", alpha=0.9)
    ax3.set_xlabel('Time (years)', fontsize=11)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=11)
    ax3.set_title('Objects in Cache %', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='best', fontsize=9)
    
    # Plot 4: Expired Tubes
    ax4 = axes[1, 1]
    total1 = [data1['tubes_expired_by_time'][i] + data1['tubes_expired_by_reads'][i] 
              for i in range(len(data1['time']))]
    total2 = [data2['tubes_expired_by_time'][i] + data2['tubes_expired_by_reads'][i] 
              for i in range(len(data2['time']))]
    pct1_total = [(t / data1['initial_tubes']) * 100 for t in total1]
    pct2_total = [(t / data2['initial_tubes']) * 100 for t in total2]
    
    # Calculate expired by time percentages
    pct1_by_time = [(t / data1['initial_tubes']) * 100 for t in data1['tubes_expired_by_time']]
    pct2_by_time = [(t / data2['initial_tubes']) * 100 for t in data2['tubes_expired_by_time']]
    
    # Plot total expired (solid lines)
    ax4.plot(data1['time'], pct1_total, linewidth=2.5, color=color1, 
             label="SHA (Total)", alpha=0.9)
    ax4.plot(data2['time'], pct2_total, linewidth=2.5, color=color2, 
             label="Clustered (Total)", alpha=0.9)
    
    # Plot expired by time (dashed lines)
    ax4.plot(data1['time'], pct1_by_time, linewidth=2, color=color1, 
             linestyle='--', label="SHA (By Time)", alpha=0.7)
    ax4.plot(data2['time'], pct2_by_time, linewidth=2, color=color2, 
             linestyle='--', label="Clustered (By Time)", alpha=0.7)
    
    ax4.set_xlabel('Time (years)', fontsize=11)
    ax4.set_ylabel('Expired Tubes (% of Initial)', fontsize=11)
    ax4.set_title('Expired Tubes %', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best', fontsize=9)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'{config}.png')
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    plt.close()
    
    print(f"  SHA: Tubes={data1['initial_tubes']}, Cache Max={result['sha_cache_max']:.2f}%")
    print(f"  Clustered: Tubes={data2['initial_tubes']}, Cache Max={result['clustered_cache_max']:.2f}%")

# Create summary comparison chart
print("\n" + "="*80)
print("CREATING SUMMARY COMPARISON")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle('Summary Comparison: SHA vs Clustered Random Small\nAll Configurations', 
             fontsize=18, fontweight='bold')

configs = [r['config'] for r in summary_results]
x = np.arange(len(configs))
width = 0.35

# Plot 1: Max Cache %
ax1 = axes[0, 0]
sha_cache_max = [r['sha_cache_max'] for r in summary_results]
clustered_cache_max = [r['clustered_cache_max'] for r in summary_results]
ax1.bar(x - width/2, sha_cache_max, width, label='SHA', color='#A23B72', alpha=0.8)
ax1.bar(x + width/2, clustered_cache_max, width, label='Clustered', color='#06A77D', alpha=0.8)
ax1.set_ylabel('Max Cache %', fontsize=12, fontweight='bold')
ax1.set_title('Maximum Cache Percentage', fontsize=13, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Plot 2: Avg Cache %
ax2 = axes[0, 1]
sha_cache_avg = [r['sha_cache_avg'] for r in summary_results]
clustered_cache_avg = [r['clustered_cache_avg'] for r in summary_results]
ax2.bar(x - width/2, sha_cache_avg, width, label='SHA', color='#A23B72', alpha=0.8)
ax2.bar(x + width/2, clustered_cache_avg, width, label='Clustered', color='#06A77D', alpha=0.8)
ax2.set_ylabel('Avg Cache %', fontsize=12, fontweight='bold')
ax2.set_title('Average Cache Percentage', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# Plot 3: Final Lost Objects %
ax3 = axes[1, 0]
sha_lost = [r['sha_lost_final'] for r in summary_results]
clustered_lost = [r['clustered_lost_final'] for r in summary_results]
ax3.bar(x - width/2, sha_lost, width, label='SHA', color='#A23B72', alpha=0.8)
ax3.bar(x + width/2, clustered_lost, width, label='Clustered', color='#06A77D', alpha=0.8)
ax3.set_ylabel('Lost Objects %', fontsize=12, fontweight='bold')
ax3.set_title('Final Lost Objects Percentage', fontsize=13, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax3.legend()
ax3.grid(axis='y', alpha=0.3)

# Plot 4: Cache Performance Ratio (Clustered/SHA)
ax4 = axes[1, 1]
cache_ratio = [r['clustered_cache_max'] / r['sha_cache_max'] if r['sha_cache_max'] > 0 else 0 
               for r in summary_results]
colors = ['#06A77D' if r > 1 else '#A23B72' for r in cache_ratio]
ax4.bar(x, cache_ratio, color=colors, alpha=0.8)
ax4.axhline(y=1, color='black', linestyle='--', linewidth=2, label='Equal Performance')
ax4.set_ylabel('Ratio (Clustered/SHA)', fontsize=12, fontweight='bold')
ax4.set_title('Cache Performance Ratio\n(>1 means Clustered is better)', fontsize=13, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax4.legend()
ax4.grid(axis='y', alpha=0.3)

plt.tight_layout()
summary_file = os.path.join(output_dir, 'SUMMARY_comparison.png')
plt.savefig(summary_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"\nSummary chart saved to: {summary_file}")
print(f"Individual comparisons saved to: {output_dir}")

# Print summary table
print("\n" + "="*100)
print("SUMMARY TABLE")
print("="*100)
print(f"{'Configuration':<45} {'SHA Tubes':<12} {'Clust Tubes':<12} {'SHA Cache%':<12} {'Clust Cache%':<12} {'Ratio':<10}")
print("-"*100)
for r in summary_results:
    ratio = r['clustered_cache_max'] / r['sha_cache_max'] if r['sha_cache_max'] > 0 else 0
    print(f"{r['config']:<45} {r['sha_tubes']:<12} {r['clustered_tubes']:<12} "
          f"{r['sha_cache_max']:<12.3f} {r['clustered_cache_max']:<12.3f} {ratio:<10.3f}")

print("="*100)

