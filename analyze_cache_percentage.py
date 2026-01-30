import matplotlib.pyplot as plt
import numpy as np
import os

# Read the snapshot file
input_file = '/Users/stephanie/Documents/thesis/python_projects/input/snaps/snaps_output_2_20260106_172713.txt'

# Lists to store data
time_stamps = []
cache_percentages = []

# Read the file
with open(input_file, 'r') as f:
    lines = f.readlines()
    
    # Skip header lines (first 3 lines)
    for i, line in enumerate(lines[3:], start=3):
        parts = line.strip().split(', ')
        if len(parts) >= 17:  # Make sure we have enough columns
            try:
                time_stamp = float(parts[0])
                cache_pct = float(parts[16])  # objects_in_cache_pct column
                
                time_stamps.append(time_stamp)
                cache_percentages.append(cache_pct)
            except (ValueError, IndexError):
                # Skip lines with invalid data
                continue

# Convert time stamps from reads to years
# Snapshots every 365 reads, 500 reads per day
# years = time_stamp / (500 reads/day * 365 days/year)
time_in_years = [t / (500 * 365) for t in time_stamps]

# Create the plot
plt.figure(figsize=(14, 8))
plt.plot(time_in_years, cache_percentages, linewidth=2, color='#2E86AB')
plt.xlabel('Time (years)', fontsize=14, fontweight='bold')
plt.ylabel('Objects in Cache (%)', fontsize=14, fontweight='bold')
plt.title('Percentage of Objects in Cache Over Time\n(Snapshots every 365 reads, 500 reads/day)', 
          fontsize=16, fontweight='bold', pad=20)
plt.grid(True, alpha=0.3, linestyle='--')
plt.tight_layout()

# Add some statistics to the plot
avg_cache = np.mean(cache_percentages)
max_cache = np.max(cache_percentages)
final_cache = cache_percentages[-1] if cache_percentages else 0

stats_text = f'Average: {avg_cache:.2f}%\nMax: {max_cache:.2f}%\nFinal: {final_cache:.2f}%'
plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
         fontsize=12, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Save the plot
output_dir = '/Users/stephanie/Documents/thesis/python_projects/output'
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, 'cache_percentage_over_time_20260106_172713.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Plot saved to: {output_file}")

# Print summary statistics
print(f"\nSummary Statistics:")
print(f"Total snapshots: {len(time_stamps)}")
print(f"Time range: {time_in_years[0]:.2f} to {time_in_years[-1]:.2f} years")
print(f"Average cache percentage: {avg_cache:.2f}%")
print(f"Maximum cache percentage: {max_cache:.2f}%")
print(f"Minimum cache percentage: {np.min(cache_percentages):.4f}%")
print(f"Final cache percentage: {final_cache:.2f}%")

plt.show()

