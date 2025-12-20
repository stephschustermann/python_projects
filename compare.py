"""
Comparison Script: Copysets vs Random
Compares lost objects percentage over 10 years between matching file pairs.
"""

import re
from pathlib import Path
import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required. Install it with:")
    print("  pip3 install --user --break-system-packages matplotlib")
    exit(1)


def parse_simulation_file(filepath: str) -> dict:
    """Parse a simulation output file and extract metrics."""
    timestamps = []
    lost_percent = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines[4:]:
        line = line.strip()
        if not line:
            continue
        
        values = [v.strip() for v in line.split(',')]
        if len(values) >= 12:
            try:
                timestamps.append(float(values[0]))
                lost_percent.append(float(values[9]))
            except ValueError:
                continue
    
    return {'timestamps': timestamps, 'lost_percent': lost_percent}


def scale_to_years(timestamps: list[float], max_years: float = 10.0) -> list[float]:
    """Scale timestamps so that max timestamp = max_years."""
    if not timestamps or max(timestamps) == 0:
        return timestamps
    scale_factor = max_years / max(timestamps)
    return [t * scale_factor for t in timestamps]


def find_key_points(years: list, values: list) -> list[tuple]:
    """Find important points in the curve."""
    key_points = []
    values_arr = np.array(values)
    years_arr = np.array(years)
    
    # First non-zero point
    non_zero_idx = np.where(values_arr > 0)[0]
    if len(non_zero_idx) > 0:
        first_idx = non_zero_idx[0]
        key_points.append((years_arr[first_idx], values_arr[first_idx], 'First loss'))
    
    # Maximum point
    if max(values) > 0:
        max_idx = np.argmax(values_arr)
        key_points.append((years_arr[max_idx], values_arr[max_idx], 'Max'))
    
    # Points where big jumps occur
    if len(values) > 10:
        diff = np.diff(values_arr)
        avg_change = np.mean(np.abs(diff[diff != 0])) if np.any(diff != 0) else 0
        if avg_change > 0:
            jump_threshold = avg_change * 3
            jumps = np.where(diff > jump_threshold)[0]
            
            if len(jumps) > 0:
                jump_magnitudes = diff[jumps]
                top_jumps = jumps[np.argsort(jump_magnitudes)[-3:]]
                for idx in top_jumps:
                    if idx + 1 < len(years_arr):
                        key_points.append((years_arr[idx + 1], values_arr[idx + 1], 'Jump'))
    
    # Final value
    if values[-1] > 0:
        key_points.append((years_arr[-1], values_arr[-1], 'Final'))
    
    return key_points


def plot_comparison(copyset_file: str, random_file: str, output_path: str, title_suffix: str) -> None:
    """Create a comparison plot of lost percentage for copysets vs random."""
    
    copyset_data = parse_simulation_file(copyset_file)
    random_data = parse_simulation_file(random_file)
    
    copyset_years = scale_to_years(copyset_data['timestamps'])
    random_years = scale_to_years(random_data['timestamps'])
    
    copyset_lost = copyset_data['lost_percent']
    random_lost = random_data['lost_percent']
    
    plt.figure(figsize=(14, 8))
    
    # Plot both lines
    plt.plot(copyset_years, copyset_lost, linewidth=2.5, color='black', 
             label='Copysets', marker='o', markersize=3, markevery=max(1, len(copyset_years)//30))
    plt.plot(random_years, random_lost, linewidth=2.5, color='#2563eb',
             label='Random', marker='s', markersize=3, markevery=max(1, len(random_years)//30))
    
    # Annotate key points for copysets
    copyset_key_points = find_key_points(copyset_years, copyset_lost)
    for x, y, label in copyset_key_points:
        if y > 0:
            plt.annotate(f'{label}\n({x:.1f}y, {y:.1f}%)', 
                        xy=(x, y), xytext=(x + 0.3, y + 5),
                        fontsize=8, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', lw=0.8),
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', alpha=0.8))
    
    # Annotate key points for random
    random_key_points = find_key_points(random_years, random_lost)
    for x, y, label in random_key_points:
        if y > 0:
            plt.annotate(f'{label}\n({x:.1f}y, {y:.1f}%)', 
                        xy=(x, y), xytext=(x - 0.5, y - 8),
                        fontsize=8, color='#2563eb',
                        arrowprops=dict(arrowstyle='->', color='#2563eb', lw=0.8),
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2563eb', alpha=0.8))
    
    plt.xlabel('Time (Years)', fontsize=12)
    plt.ylabel('Lost Objects (%)', fontsize=12)
    plt.title(f'Lost Objects Percentage: Copysets vs Random\n({title_suffix})', 
              fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 10)
    plt.ylim(0, 105)
    plt.yticks(range(0, 105, 5))  # Grid lines every 5%
    
    # Stats box
    stats_text = (
        f"Copysets: Final={copyset_lost[-1]:.2f}%, Max={max(copyset_lost):.2f}%\n"
        f"Random:   Final={random_lost[-1]:.2f}%, Max={max(random_lost):.2f}%"
    )
    plt.text(0.98, 0.02, stats_text, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='gray', alpha=0.9),
             family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"    Saved: {Path(output_path).name}")


def find_matching_pairs(input_folder: Path) -> list[tuple]:
    """
    Find all matching copyset/random file pairs.
    Returns list of (copyset_file, random_file, suffix) tuples.
    """
    pairs = []
    
    # Pattern 1: copyset_* vs random_* (no _2)
    copyset_files = list(input_folder.glob("copyset_*.txt"))
    for copyset_file in copyset_files:
        # Extract suffix after "copyset_"
        suffix = copyset_file.name.replace("copyset_", "")
        random_file = input_folder / f"random_{suffix}"
        if random_file.exists():
            pairs.append((copyset_file, random_file, suffix.replace(".txt", ""), "copyset"))
    
    # Pattern 2: copysets_2_* vs random_2_*
    copysets2_files = list(input_folder.glob("copysets_2_*.txt"))
    for copyset_file in copysets2_files:
        # Extract suffix after "copysets_2_"
        suffix = copyset_file.name.replace("copysets_2_", "")
        random_file = input_folder / f"random_2_{suffix}"
        if random_file.exists():
            pairs.append((copyset_file, random_file, suffix.replace(".txt", ""), "copysets_2"))
    
    return pairs


def main() -> None:
    """Main entry point - process all matching pairs."""
    input_folder = Path(__file__).parent / "input"
    output_folder = Path(__file__).parent / "output"
    output_folder.mkdir(exist_ok=True)
    
    pairs = find_matching_pairs(input_folder)
    
    if not pairs:
        print("No matching file pairs found!")
        return
    
    print(f"Found {len(pairs)} matching pairs to compare\n")
    
    # Group by type
    copyset_pairs = [(c, r, s) for c, r, s, t in pairs if t == "copyset"]
    copysets2_pairs = [(c, r, s) for c, r, s, t in pairs if t == "copysets_2"]
    
    # Process copyset vs random pairs
    if copyset_pairs:
        print(f"=== Copyset vs Random ({len(copyset_pairs)} pairs) ===")
        for copyset_file, random_file, suffix in sorted(copyset_pairs, key=lambda x: x[2]):
            print(f"  {suffix}")
            output_file = output_folder / f"comparison_copyset_vs_random_{suffix}.png"
            plot_comparison(str(copyset_file), str(random_file), str(output_file), suffix)
        print()
    
    # Process copysets_2 vs random_2 pairs
    if copysets2_pairs:
        print(f"=== Copysets_2 vs Random_2 ({len(copysets2_pairs)} pairs) ===")
        for copyset_file, random_file, suffix in sorted(copysets2_pairs, key=lambda x: x[2]):
            print(f"  {suffix}")
            output_file = output_folder / f"comparison_copysets2_vs_random2_{suffix}.png"
            plot_comparison(str(copyset_file), str(random_file), str(output_file), suffix)
        print()
    
    print(f"Done! Generated {len(pairs)} comparison graphs in output/")


if __name__ == "__main__":
    main()
