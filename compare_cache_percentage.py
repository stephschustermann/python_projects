import matplotlib.pyplot as plt
import numpy as np
import os

def parse_snapshot_file(filepath):
    """Parse a snapshot file and extract cache percentages over time."""
    time_stamps = []
    cache_percentages = []
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
                    cache_pct = float(parts[16])  # objects_in_cache_pct column
                    
                    time_stamps.append(time_stamp)
                    cache_percentages.append(cache_pct)
                except (ValueError, IndexError):
                    continue
    
    # Convert time stamps from reads to years
    # Snapshots every 365 reads, 500 reads per day
    time_in_years = [t / (500 * 365) for t in time_stamps]
    
    return time_in_years, cache_percentages, max_reads, initial_tubes, objects_per_tube

# Parse all four files
file1 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260106_172713.txt'
file2 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260106_181118.txt'
file3 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260106_223033.txt'
file4 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260107_171654.txt'

time1, cache1, max_reads1, tubes1, obj_per_tube1 = parse_snapshot_file(file1)
time2, cache2, max_reads2, tubes2, obj_per_tube2 = parse_snapshot_file(file2)
time3, cache3, max_reads3, tubes3, obj_per_tube3 = parse_snapshot_file(file3)
time4, cache4, max_reads4, tubes4, obj_per_tube4 = parse_snapshot_file(file4)

# Create the comparison plot
plt.figure(figsize=(14, 8))

# Plot all four datasets with different colors and styles
plt.plot(time1, cache1, linewidth=2.5, color='#2E86AB', 
         label=f'172713: Tubes={tubes1}, MaxReads={max_reads1}, ObjPerTube={obj_per_tube1}', alpha=0.9)
plt.plot(time2, cache2, linewidth=2.5, color='#A23B72', 
         label=f'181118: Tubes={tubes2}, MaxReads={max_reads2}, ObjPerTube={obj_per_tube2}', alpha=0.9)
plt.plot(time3, cache3, linewidth=2.5, color='#F18F01', 
         label=f'223033: Tubes={tubes3}, MaxReads={max_reads3}, ObjPerTube={obj_per_tube3}', alpha=0.9)
plt.plot(time4, cache4, linewidth=2.5, color='#06A77D', 
         label=f'171654: Tubes={tubes4}, MaxReads={max_reads4}, ObjPerTube={obj_per_tube4}', alpha=0.9)

plt.xlabel('Time (years)', fontsize=14, fontweight='bold')
plt.ylabel('Objects in Cache (%)', fontsize=14, fontweight='bold')
plt.title('Comparison: Percentage of Objects in Cache Over Time (4 Files)\n(Snapshots every 365 reads, 500 reads/day)', 
          fontsize=16, fontweight='bold', pad=20)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper right', fontsize=12, framealpha=0.9)

# Add statistics for all four files
avg_cache1 = np.mean(cache1)
max_cache1 = np.max(cache1)
final_cache1 = cache1[-1] if cache1 else 0

avg_cache2 = np.mean(cache2)
max_cache2 = np.max(cache2)
final_cache2 = cache2[-1] if cache2 else 0

avg_cache3 = np.mean(cache3)
max_cache3 = np.max(cache3)
final_cache3 = cache3[-1] if cache3 else 0

avg_cache4 = np.mean(cache4)
max_cache4 = np.max(cache4)
final_cache4 = cache4[-1] if cache4 else 0

stats_text = f'172713 (T:{tubes1}, R:{max_reads1}, O:{obj_per_tube1}):\n'
stats_text += f'  Avg:{avg_cache1:.2f}% Max:{max_cache1:.2f}%\n\n'
stats_text += f'181118 (T:{tubes2}, R:{max_reads2}, O:{obj_per_tube2}):\n'
stats_text += f'  Avg:{avg_cache2:.2f}% Max:{max_cache2:.2f}%\n\n'
stats_text += f'223033 (T:{tubes3}, R:{max_reads3}, O:{obj_per_tube3}):\n'
stats_text += f'  Avg:{avg_cache3:.2f}% Max:{max_cache3:.2f}%\n\n'
stats_text += f'171654 (T:{tubes4}, R:{max_reads4}, O:{obj_per_tube4}):\n'
stats_text += f'  Avg:{avg_cache4:.2f}% Max:{max_cache4:.2f}%'

plt.text(0.02, 0.82, stats_text, transform=plt.gca().transAxes, 
         fontsize=9, verticalalignment='top', family='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()

# Save the plot
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output'
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, 'cache_percentage_comparison_4files.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Comparison plot saved to: {output_file}")

# Print detailed comparison
print(f"\n{'='*80}")
print(f"COMPARISON SUMMARY: FOUR FILES")
print(f"{'='*80}")

print(f"\nFile 1: snaps_output_2_20260106_172713.txt")
print(f"  Initial Number of Tubes: {tubes1}")
print(f"  Maximum Reads per Tube: {max_reads1}")
print(f"  Objects per Tube: {obj_per_tube1}")
print(f"  Total snapshots: {len(time1)}")
print(f"  Time range: {time1[0]:.2f} to {time1[-1]:.2f} years")
print(f"  Average cache %: {avg_cache1:.4f}%")
print(f"  Maximum cache %: {max_cache1:.4f}%")
print(f"  Minimum cache %: {np.min(cache1):.4f}%")
print(f"  Final cache %: {final_cache1:.4f}%")

print(f"\nFile 2: snaps_output_2_20260106_181118.txt")
print(f"  Initial Number of Tubes: {tubes2}")
print(f"  Maximum Reads per Tube: {max_reads2}")
print(f"  Objects per Tube: {obj_per_tube2}")
print(f"  Total snapshots: {len(time2)}")
print(f"  Time range: {time2[0]:.2f} to {time2[-1]:.2f} years")
print(f"  Average cache %: {avg_cache2:.4f}%")
print(f"  Maximum cache %: {max_cache2:.4f}%")
print(f"  Minimum cache %: {np.min(cache2):.4f}%")
print(f"  Final cache %: {final_cache2:.4f}%")

print(f"\nFile 3: snaps_output_2_20260106_223033.txt")
print(f"  Initial Number of Tubes: {tubes3}")
print(f"  Maximum Reads per Tube: {max_reads3}")
print(f"  Objects per Tube: {obj_per_tube3}")
print(f"  Total snapshots: {len(time3)}")
print(f"  Time range: {time3[0]:.2f} to {time3[-1]:.2f} years")
print(f"  Average cache %: {avg_cache3:.4f}%")
print(f"  Maximum cache %: {max_cache3:.4f}%")
print(f"  Minimum cache %: {np.min(cache3):.4f}%")
print(f"  Final cache %: {final_cache3:.4f}%")

print(f"\nFile 4: snaps_output_2_20260107_171654.txt")
print(f"  Initial Number of Tubes: {tubes4}")
print(f"  Maximum Reads per Tube: {max_reads4}")
print(f"  Objects per Tube: {obj_per_tube4}")
print(f"  Total snapshots: {len(time4)}")
print(f"  Time range: {time4[0]:.2f} to {time4[-1]:.2f} years")
print(f"  Average cache %: {avg_cache4:.4f}%")
print(f"  Maximum cache %: {max_cache4:.4f}%")
print(f"  Minimum cache %: {np.min(cache4):.4f}%")
print(f"  Final cache %: {final_cache4:.4f}%")

print(f"\n{'='*80}")
print(f"KEY DIFFERENCES:")
print(f"{'='*80}")

# Find file with highest peak
max_peaks = [max_cache1, max_cache2, max_cache3, max_cache4]
file_names = ['172713', '181118', '223033', '171654']
max_idx = max_peaks.index(max(max_peaks))
print(f"Highest peak cache: File {file_names[max_idx]} with {max_peaks[max_idx]:.4f}%")

# Find file with highest average
avg_caches = [avg_cache1, avg_cache2, avg_cache3, avg_cache4]
avg_idx = avg_caches.index(max(avg_caches))
print(f"Highest average cache: File {file_names[avg_idx]} with {avg_caches[avg_idx]:.4f}%")

print(f"\nKey parameter differences:")
print(f"  File 172713: {tubes1} tubes, {max_reads1} max reads, {obj_per_tube1} obj/tube")
print(f"  File 181118: {tubes2} tubes, {max_reads2} max reads, {obj_per_tube2} obj/tube")
print(f"  File 223033: {tubes3} tubes, {max_reads3} max reads, {obj_per_tube3} obj/tube")
print(f"  File 171654: {tubes4} tubes, {max_reads4} max reads, {obj_per_tube4} obj/tube")

print(f"\nNOTE: Files 172713 and 171654 have IDENTICAL parameters.")
print(f"      Comparing their cache performance shows simulation variability.")

plt.show()

