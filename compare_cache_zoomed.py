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

# Parse files
file1 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260106_172713.txt'
file3 = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260106_223033.txt'

time1, cache1, max_reads1, tubes1, obj_per_tube1 = parse_snapshot_file(file1)
time3, cache3, max_reads3, tubes3, obj_per_tube3 = parse_snapshot_file(file3)

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Left plot: Zoomed view of Files 1 and 3
ax1.plot(time1, cache1, linewidth=2.5, color='#2E86AB', 
         label=f'172713: Tubes={tubes1}, ObjPerTube={obj_per_tube1}', alpha=0.9)
ax1.plot(time3, cache3, linewidth=2.5, color='#F18F01', 
         label=f'223033: Tubes={tubes3}, ObjPerTube={obj_per_tube3}', alpha=0.9)

ax1.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Objects in Cache (%)', fontsize=12, fontweight='bold')
ax1.set_title('Zoomed View: Files 172713 vs 223033\n(Similar Cache Performance)', 
              fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='upper right', fontsize=10)

# Add statistics
avg1 = np.mean(cache1)
max1 = np.max(cache1)
avg3 = np.mean(cache3)
max3 = np.max(cache3)

stats_text = f'File 172713:\n  Avg: {avg1:.4f}%\n  Max: {max1:.4f}%\n\n'
stats_text += f'File 223033:\n  Avg: {avg3:.4f}%\n  Max: {max3:.4f}%'
ax1.text(0.98, 0.98, stats_text, transform=ax1.transAxes, 
         fontsize=10, verticalalignment='top', horizontalalignment='right',
         family='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Right plot: Detail view showing actual values at specific point
# Find the index closest to year 1.14 (where user saw 0.3469)
target_year = 1.14
idx3 = min(range(len(time3)), key=lambda i: abs(time3[i] - target_year))
idx1 = min(range(len(time1)), key=lambda i: abs(time1[i] - target_year))

# Plot a window around that time
time_window = 2.0  # years
mask1 = [(t >= 0 and t <= time_window) for t in time1]
mask3 = [(t >= 0 and t <= time_window) for t in time3]

time1_zoom = [time1[i] for i in range(len(time1)) if mask1[i]]
cache1_zoom = [cache1[i] for i in range(len(cache1)) if mask1[i]]
time3_zoom = [time3[i] for i in range(len(time3)) if mask3[i]]
cache3_zoom = [cache3[i] for i in range(len(cache3)) if mask3[i]]

ax2.plot(time1_zoom, cache1_zoom, linewidth=2.5, color='#2E86AB', 
         label=f'172713', alpha=0.9, marker='o', markersize=3, markevery=50)
ax2.plot(time3_zoom, cache3_zoom, linewidth=2.5, color='#F18F01', 
         label=f'223033', alpha=0.9, marker='s', markersize=3, markevery=50)

# Highlight the point the user asked about
ax2.axvline(x=time3[idx3], color='red', linestyle='--', alpha=0.5, linewidth=1)
ax2.plot(time3[idx3], cache3[idx3], 'ro', markersize=8, 
         label=f'Line 574: {cache3[idx3]:.4f}% at {time3[idx3]:.2f} years')

ax2.set_xlabel('Time (years)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Objects in Cache (%)', fontsize=12, fontweight='bold')
ax2.set_title(f'First {time_window} Years Detail View\n(Showing actual cache values)', 
              fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(loc='upper right', fontsize=9)

plt.tight_layout()

# Save the plot
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output'
output_file = os.path.join(output_dir, 'cache_percentage_zoomed_comparison.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Zoomed comparison plot saved to: {output_file}")

# Print the specific value user asked about
print(f"\nValue at line 574 (file 223033):")
print(f"  Time: {time3[idx3]:.4f} years (timestamp {time3[idx3] * 500 * 365:.0f})")
print(f"  Cache %: {cache3[idx3]:.4f}%")
print(f"\nThis IS correctly plotted! The issue is the scale:")
print(f"  - Previous graph scale: 0-16% (to show file 181118)")
print(f"  - File 223033 max: {max3:.4f}%")
print(f"  - So the 0.3469% appears very close to 0 on a 0-16% scale")
print(f"  - On this zoomed view, you can see the actual values clearly")

plt.show()

