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

# Three folders to compare
folder1 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_sha'
folder2 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_clustered_random_small'
folder3 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/bug_fix_clustered_randome_big'

# Get files
files1 = sorted(glob.glob(os.path.join(folder1, '*.txt')))
files2 = sorted(glob.glob(os.path.join(folder2, '*.txt')))
files3 = sorted(glob.glob(os.path.join(folder3, '*.txt')))

# Match files by configuration
file_triples = []
for f1 in files1:
    config1 = get_config_key(f1)
    f2_match = None
    f3_match = None
    
    for f2 in files2:
        if get_config_key(f2) == config1:
            f2_match = f2
            break
    
    for f3 in files3:
        if get_config_key(f3) == config1:
            f3_match = f3
            break
    
    if f2_match and f3_match:
        file_triples.append((f1, f2_match, f3_match, config1))

print(f"Found {len(file_triples)} matching file triples")

# Create output directory
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output/three_way_comparison'
os.makedirs(output_dir, exist_ok=True)

summary_results = []

# Compare each triple
for f1, f2, f3, config in file_triples:
    print(f"\nComparing: {config}")
    
    access_rate = extract_access_rate(f1)
    
    data1 = parse_snapshot_file_detailed(f1, access_rate)
    data2 = parse_snapshot_file_detailed(f2, access_rate)
    data3 = parse_snapshot_file_detailed(f3, access_rate)
    
    result = {
        'config': config,
        'sha_tubes': data1['initial_tubes'],
        'small_tubes': data2['initial_tubes'],
        'big_tubes': data3['initial_tubes'],
        'sha_cache_max': np.max(data1['objects_in_cache_pct']) if len(data1['objects_in_cache_pct']) > 0 else 0,
        'small_cache_max': np.max(data2['objects_in_cache_pct']) if len(data2['objects_in_cache_pct']) > 0 else 0,
        'big_cache_max': np.max(data3['objects_in_cache_pct']) if len(data3['objects_in_cache_pct']) > 0 else 0,
        'sha_cache_avg': np.mean(data1['objects_in_cache_pct']) if len(data1['objects_in_cache_pct']) > 0 else 0,
        'small_cache_avg': np.mean(data2['objects_in_cache_pct']) if len(data2['objects_in_cache_pct']) > 0 else 0,
        'big_cache_avg': np.mean(data3['objects_in_cache_pct']) if len(data3['objects_in_cache_pct']) > 0 else 0,
    }
    summary_results.append(result)
    
    # Create individual comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Three-Way Comparison: SHA vs Small Cluster vs Big Cluster\n{config}\n(Access Rate: {access_rate} reads/day, 10 years)', 
                 fontsize=16, fontweight='bold')
    
    # Colors
    color1 = '#A23B72'  # SHA
    color2 = '#06A77D'  # Small Cluster
    color3 = '#F18F01'  # Big Cluster
    
    # Plot 1: Lost Objects
    ax1 = axes[0, 0]
    ax1.plot(data1['time'], data1['lost_objects_pct'], linewidth=2.5, color=color1, 
             label=f"SHA (Tubes={data1['initial_tubes']})", alpha=0.9)
    ax1.plot(data2['time'], data2['lost_objects_pct'], linewidth=2.5, color=color2, 
             label=f"Small Cluster (Tubes={data2['initial_tubes']})", alpha=0.9)
    ax1.plot(data3['time'], data3['lost_objects_pct'], linewidth=2.5, color=color3, 
             label=f"Big Cluster (Tubes={data3['initial_tubes']})", alpha=0.9)
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
             label="Small Cluster", alpha=0.9)
    ax2.plot(data3['time'], data3['wet_tubes_pct'], linewidth=2.5, color=color3, 
             label="Big Cluster", alpha=0.9)
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
             label="Small Cluster", alpha=0.9)
    ax3.plot(data3['time'], data3['objects_in_cache_pct'], linewidth=2.5, color=color3, 
             label="Big Cluster", alpha=0.9)
    ax3.set_xlabel('Time (years)', fontsize=11)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=11)
    ax3.set_title('Objects in Cache %', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='best', fontsize=9)
    
    # Plot 4: Expired Tubes
    ax4 = axes[1, 1]
    # Calculate totals and by-time percentages
    total1 = [data1['tubes_expired_by_time'][i] + data1['tubes_expired_by_reads'][i] 
              for i in range(len(data1['time']))]
    total2 = [data2['tubes_expired_by_time'][i] + data2['tubes_expired_by_reads'][i] 
              for i in range(len(data2['time']))]
    total3 = [data3['tubes_expired_by_time'][i] + data3['tubes_expired_by_reads'][i] 
              for i in range(len(data3['time']))]
    
    pct1_total = [(t / data1['initial_tubes']) * 100 for t in total1]
    pct2_total = [(t / data2['initial_tubes']) * 100 for t in total2]
    pct3_total = [(t / data3['initial_tubes']) * 100 for t in total3]
    
    pct1_by_time = [(t / data1['initial_tubes']) * 100 for t in data1['tubes_expired_by_time']]
    pct2_by_time = [(t / data2['initial_tubes']) * 100 for t in data2['tubes_expired_by_time']]
    pct3_by_time = [(t / data3['initial_tubes']) * 100 for t in data3['tubes_expired_by_time']]
    
    # Plot total (solid) and by time (dashed)
    ax4.plot(data1['time'], pct1_total, linewidth=2.5, color=color1, label="SHA (Total)", alpha=0.9)
    ax4.plot(data2['time'], pct2_total, linewidth=2.5, color=color2, label="Small Cluster (Total)", alpha=0.9)
    ax4.plot(data3['time'], pct3_total, linewidth=2.5, color=color3, label="Big Cluster (Total)", alpha=0.9)
    
    ax4.plot(data1['time'], pct1_by_time, linewidth=2, color=color1, linestyle='--', 
             label="SHA (By Time)", alpha=0.7)
    ax4.plot(data2['time'], pct2_by_time, linewidth=2, color=color2, linestyle='--', 
             label="Small Cluster (By Time)", alpha=0.7)
    ax4.plot(data3['time'], pct3_by_time, linewidth=2, color=color3, linestyle='--', 
             label="Big Cluster (By Time)", alpha=0.7)
    
    ax4.set_xlabel('Time (years)', fontsize=11)
    ax4.set_ylabel('Expired Tubes (% of Initial)', fontsize=11)
    ax4.set_title('Expired Tubes %', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best', fontsize=8)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'{config}.png')
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    plt.close()
    
    print(f"  SHA: Tubes={data1['initial_tubes']}, Cache Max={result['sha_cache_max']:.2f}%")
    print(f"  Small Cluster: Tubes={data2['initial_tubes']}, Cache Max={result['small_cache_max']:.2f}%")
    print(f"  Big Cluster: Tubes={data3['initial_tubes']}, Cache Max={result['big_cache_max']:.2f}%")

# Create summary chart
print("\n" + "="*80)
print("CREATING SUMMARY COMPARISON")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(18, 10))
fig.suptitle('Summary: SHA vs Small Cluster vs Big Cluster\nAll Configurations', 
             fontsize=18, fontweight='bold')

configs = [r['config'] for r in summary_results]
x = np.arange(len(configs))
width = 0.25

# Plot 1: Max Cache %
ax1 = axes[0, 0]
sha_cache_max = [r['sha_cache_max'] for r in summary_results]
small_cache_max = [r['small_cache_max'] for r in summary_results]
big_cache_max = [r['big_cache_max'] for r in summary_results]
ax1.bar(x - width, sha_cache_max, width, label='SHA', color='#A23B72', alpha=0.8)
ax1.bar(x, small_cache_max, width, label='Small Cluster', color='#06A77D', alpha=0.8)
ax1.bar(x + width, big_cache_max, width, label='Big Cluster', color='#F18F01', alpha=0.8)
ax1.set_ylabel('Max Cache %', fontsize=12, fontweight='bold')
ax1.set_title('Maximum Cache Percentage', fontsize=13, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Plot 2: Avg Cache %
ax2 = axes[0, 1]
sha_cache_avg = [r['sha_cache_avg'] for r in summary_results]
small_cache_avg = [r['small_cache_avg'] for r in summary_results]
big_cache_avg = [r['big_cache_avg'] for r in summary_results]
ax2.bar(x - width, sha_cache_avg, width, label='SHA', color='#A23B72', alpha=0.8)
ax2.bar(x, small_cache_avg, width, label='Small Cluster', color='#06A77D', alpha=0.8)
ax2.bar(x + width, big_cache_avg, width, label='Big Cluster', color='#F18F01', alpha=0.8)
ax2.set_ylabel('Avg Cache %', fontsize=12, fontweight='bold')
ax2.set_title('Average Cache Percentage', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# Plot 3: Number of Tubes
ax3 = axes[1, 0]
sha_tubes = [r['sha_tubes'] if r['sha_tubes'] is not None else 0 for r in summary_results]
small_tubes = [r['small_tubes'] if r['small_tubes'] is not None else 0 for r in summary_results]
big_tubes = [r['big_tubes'] if r['big_tubes'] is not None else 0 for r in summary_results]
ax3.bar(x - width, sha_tubes, width, label='SHA', color='#A23B72', alpha=0.8)
ax3.bar(x, small_tubes, width, label='Small Cluster', color='#06A77D', alpha=0.8)
ax3.bar(x + width, big_tubes, width, label='Big Cluster', color='#F18F01', alpha=0.8)
ax3.set_ylabel('Number of Tubes', fontsize=12, fontweight='bold')
ax3.set_title('Initial Number of Tubes', fontsize=13, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax3.legend()
ax3.grid(axis='y', alpha=0.3)

# Plot 4: Cache Ratio Comparison
ax4 = axes[1, 1]
small_vs_sha = [r['small_cache_max'] / r['sha_cache_max'] if r['sha_cache_max'] > 0 else 1 
                for r in summary_results]
big_vs_sha = [r['big_cache_max'] / r['sha_cache_max'] if r['sha_cache_max'] > 0 else 1 
              for r in summary_results]
ax4.bar(x - width/2, small_vs_sha, width, label='Small/SHA', color='#06A77D', alpha=0.8)
ax4.bar(x + width/2, big_vs_sha, width, label='Big/SHA', color='#F18F01', alpha=0.8)
ax4.axhline(y=1, color='black', linestyle='--', linewidth=2, label='Equal to SHA')
ax4.set_ylabel('Ratio', fontsize=12, fontweight='bold')
ax4.set_title('Cache Performance Ratio vs SHA\n(>1 means better than SHA)', fontsize=13, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels([c.replace('_', '\n') for c in configs], rotation=45, ha='right', fontsize=8)
ax4.legend()
ax4.grid(axis='y', alpha=0.3)

plt.tight_layout()
summary_file = os.path.join(output_dir, 'SUMMARY_three_way_comparison.png')
plt.savefig(summary_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"\nSummary chart saved to: {summary_file}")
print(f"Individual comparisons saved to: {output_dir}")

# Print summary table
print("\n" + "="*120)
print("SUMMARY TABLE")
print("="*120)
print(f"{'Configuration':<45} {'SHA':<10} {'Small':<10} {'Big':<10} {'SHA Max%':<12} {'Small Max%':<12} {'Big Max%':<12}")
print("-"*120)
for r in summary_results:
    sha_t = r['sha_tubes'] if r['sha_tubes'] is not None else 0
    small_t = r['small_tubes'] if r['small_tubes'] is not None else 0
    big_t = r['big_tubes'] if r['big_tubes'] is not None else 0
    print(f"{r['config']:<45} {sha_t:<10} {small_t:<10} {big_t:<10} "
          f"{r['sha_cache_max']:<12.3f} {r['small_cache_max']:<12.3f} {r['big_cache_max']:<12.3f}")
print("="*120)
