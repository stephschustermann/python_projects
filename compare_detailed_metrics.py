import matplotlib.pyplot as plt
import numpy as np
import os

def parse_snapshot_file_detailed(filepath):
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
    
    # Convert time stamps from reads to years
    time_in_years = [t / (500 * 365) for t in time_stamps]
    
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

# Parse both files
file1 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260108_193825.txt'
file2 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260108_193402.txt'

data1 = parse_snapshot_file_detailed(file1)
data2 = parse_snapshot_file_detailed(file2)

# Create a 2x2 subplot figure
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Detailed Comparison: File 193825 vs File 193402\n(Snapshots every 365 reads, 500 reads/day)', 
             fontsize=18, fontweight='bold', y=0.995)

# Color scheme
color1 = '#A23B72'  # Purple for 193825
color2 = '#06A77D'  # Green for 193402

# Plot 1: Lost Objects Percentage
ax1 = axes[0, 0]
ax1.plot(data1['time'], data1['lost_objects_pct'], linewidth=2.5, color=color1, 
         label=f"193825 (Obj/Tube={data1['objects_per_tube']})", alpha=0.9)
ax1.plot(data2['time'], data2['lost_objects_pct'], linewidth=2.5, color=color2, 
         label=f"193402 (Obj/Tube={data2['objects_per_tube']})", alpha=0.9)
ax1.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Lost Objects (%)', fontsize=12, fontweight='bold')
ax1.set_title('Lost Objects Percentage Over Time', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='best', fontsize=10)

# Add statistics
avg1 = np.mean(data1['lost_objects_pct'])
avg2 = np.mean(data2['lost_objects_pct'])
final1 = data1['lost_objects_pct'][-1] if data1['lost_objects_pct'] else 0
final2 = data2['lost_objects_pct'][-1] if data2['lost_objects_pct'] else 0
stats_text = f'193825: Final={final1:.2f}%\n193402: Final={final2:.2f}%'
ax1.text(0.98, 0.02, stats_text, transform=ax1.transAxes, 
         fontsize=10, verticalalignment='bottom', horizontalalignment='right',
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Plot 2: Wet Tubes Percentage
ax2 = axes[0, 1]
ax2.plot(data1['time'], data1['wet_tubes_pct'], linewidth=2.5, color=color1, 
         label=f"193825", alpha=0.9)
ax2.plot(data2['time'], data2['wet_tubes_pct'], linewidth=2.5, color=color2, 
         label=f"193402", alpha=0.9)
ax2.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Wet Tubes (%)', fontsize=12, fontweight='bold')
ax2.set_title('Wet Tubes Percentage Over Time', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(loc='best', fontsize=10)

# Add statistics
final1 = data1['wet_tubes_pct'][-1] if data1['wet_tubes_pct'] else 0
final2 = data2['wet_tubes_pct'][-1] if data2['wet_tubes_pct'] else 0
stats_text = f'193825: Final={final1:.2f}%\n193402: Final={final2:.2f}%'
ax2.text(0.98, 0.98, stats_text, transform=ax2.transAxes, 
         fontsize=10, verticalalignment='top', horizontalalignment='right',
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Plot 3: Objects in Cache Percentage
ax3 = axes[1, 0]
ax3.plot(data1['time'], data1['objects_in_cache_pct'], linewidth=2.5, color=color1, 
         label=f"193825", alpha=0.9)
ax3.plot(data2['time'], data2['objects_in_cache_pct'], linewidth=2.5, color=color2, 
         label=f"193402", alpha=0.9)
ax3.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Objects in Cache (%)', fontsize=12, fontweight='bold')
ax3.set_title('Objects in Cache Percentage Over Time', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.legend(loc='best', fontsize=10)

# Add statistics
max1 = np.max(data1['objects_in_cache_pct'])
max2 = np.max(data2['objects_in_cache_pct'])
avg1 = np.mean(data1['objects_in_cache_pct'])
avg2 = np.mean(data2['objects_in_cache_pct'])
stats_text = f'193825: Max={max1:.2f}%, Avg={avg1:.2f}%\n193402: Max={max2:.2f}%, Avg={avg2:.2f}%'
ax3.text(0.98, 0.98, stats_text, transform=ax3.transAxes, 
         fontsize=10, verticalalignment='top', horizontalalignment='right',
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Plot 4: Expired Tubes (both by time and by reads)
ax4 = axes[1, 1]
# Calculate total expired tubes
total_expired1 = [data1['tubes_expired_by_time'][i] + data1['tubes_expired_by_reads'][i] 
                  for i in range(len(data1['time']))]
total_expired2 = [data2['tubes_expired_by_time'][i] + data2['tubes_expired_by_reads'][i] 
                  for i in range(len(data2['time']))]

# Calculate as percentage of initial tubes
expired_pct1 = [(exp / data1['initial_tubes']) * 100 for exp in total_expired1]
expired_pct2 = [(exp / data2['initial_tubes']) * 100 for exp in total_expired2]

ax4.plot(data1['time'], expired_pct1, linewidth=2.5, color=color1, 
         label=f"193825 (Total Expired)", alpha=0.9)
ax4.plot(data2['time'], expired_pct2, linewidth=2.5, color=color2, 
         label=f"193402 (Total Expired)", alpha=0.9)

# Also plot expired by time separately (with dashed lines)
expired_by_time_pct1 = [(exp / data1['initial_tubes']) * 100 for exp in data1['tubes_expired_by_time']]
expired_by_time_pct2 = [(exp / data2['initial_tubes']) * 100 for exp in data2['tubes_expired_by_time']]

ax4.plot(data1['time'], expired_by_time_pct1, linewidth=1.5, color=color1, 
         linestyle='--', label=f"193825 (Expired by Time)", alpha=0.6)
ax4.plot(data2['time'], expired_by_time_pct2, linewidth=1.5, color=color2, 
         linestyle='--', label=f"193402 (Expired by Time)", alpha=0.6)

ax4.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Expired Tubes (% of Initial)', fontsize=12, fontweight='bold')
ax4.set_title('Expired Tubes Percentage Over Time', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.legend(loc='best', fontsize=9)

# Add statistics
final_total1 = expired_pct1[-1] if expired_pct1 else 0
final_total2 = expired_pct2[-1] if expired_pct2 else 0
final_time1 = expired_by_time_pct1[-1] if expired_by_time_pct1 else 0
final_time2 = expired_by_time_pct2[-1] if expired_by_time_pct2 else 0
stats_text = f'193825: Total={final_total1:.1f}%, ByTime={final_time1:.1f}%\n'
stats_text += f'193402: Total={final_total2:.1f}%, ByTime={final_time2:.1f}%'
ax4.text(0.98, 0.02, stats_text, transform=ax4.transAxes, 
         fontsize=10, verticalalignment='bottom', horizontalalignment='right',
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()

# Save the plot
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output'
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, 'detailed_comparison_193825_vs_193402.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Detailed comparison plot saved to: {output_file}")

# Print detailed statistics
print(f"\n{'='*80}")
print(f"DETAILED COMPARISON: FILE 193825 vs FILE 193402")
print(f"{'='*80}")

print(f"\nFile Parameters:")
print(f"  193825: {data1['initial_tubes']} tubes, {data1['max_reads']} max reads, {data1['objects_per_tube']} obj/tube")
print(f"  193402: {data2['initial_tubes']} tubes, {data2['max_reads']} max reads, {data2['objects_per_tube']} obj/tube")

print(f"\n1. LOST OBJECTS PERCENTAGE:")
print(f"  193825: Final = {data1['lost_objects_pct'][-1]:.4f}%")
print(f"  193402: Final = {data2['lost_objects_pct'][-1]:.4f}%")
print(f"  Difference: {abs(data1['lost_objects_pct'][-1] - data2['lost_objects_pct'][-1]):.4f}%")

print(f"\n2. WET TUBES PERCENTAGE:")
print(f"  193825: Final = {data1['wet_tubes_pct'][-1]:.4f}%")
print(f"  193402: Final = {data2['wet_tubes_pct'][-1]:.4f}%")
print(f"  Difference: {abs(data1['wet_tubes_pct'][-1] - data2['wet_tubes_pct'][-1]):.4f}%")

print(f"\n3. OBJECTS IN CACHE PERCENTAGE:")
print(f"  193825: Max = {np.max(data1['objects_in_cache_pct']):.4f}%, Avg = {np.mean(data1['objects_in_cache_pct']):.4f}%, Final = {data1['objects_in_cache_pct'][-1]:.4f}%")
print(f"  193402: Max = {np.max(data2['objects_in_cache_pct']):.4f}%, Avg = {np.mean(data2['objects_in_cache_pct']):.4f}%, Final = {data2['objects_in_cache_pct'][-1]:.4f}%")
print(f"  Max Difference: {abs(np.max(data1['objects_in_cache_pct']) - np.max(data2['objects_in_cache_pct'])):.4f}%")

print(f"\n4. EXPIRED TUBES:")
final_expired1 = data1['tubes_expired_by_time'][-1] + data1['tubes_expired_by_reads'][-1]
final_expired2 = data2['tubes_expired_by_time'][-1] + data2['tubes_expired_by_reads'][-1]
print(f"  193825: Total = {final_expired1:.0f} ({(final_expired1/data1['initial_tubes']*100):.2f}% of initial)")
print(f"          By Time = {data1['tubes_expired_by_time'][-1]:.0f}, By Reads = {data1['tubes_expired_by_reads'][-1]:.0f}")
print(f"  193402: Total = {final_expired2:.0f} ({(final_expired2/data2['initial_tubes']*100):.2f}% of initial)")
print(f"          By Time = {data2['tubes_expired_by_time'][-1]:.0f}, By Reads = {data2['tubes_expired_by_reads'][-1]:.0f}")

print(f"\n{'='*80}")
print(f"KEY INSIGHT:")
print(f"{'='*80}")
print(f"Both files have IDENTICAL tube counts ({data1['initial_tubes']} tubes), but DIFFERENT objects per tube:")
print(f"  File 193825: {data1['objects_per_tube']} objects/tube")
print(f"  File 193402: {data2['objects_per_tube']} objects/tube")
print(f"This comparison shows how the objects-per-tube ratio affects cache performance,")
print(f"wet tube utilization, and overall system behavior.")

plt.show()

