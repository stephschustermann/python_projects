"""
Comparison Script: 6-way comparison
Copysets_2 (black) | Copysets_224 (green) | Copysets_248 (red) | Copysets_296 (orange) | Copysets_2384 (yellow) | Random_2 (blue)
All six on one graph for each configuration.
"""

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


def find_key_points(years: list, values: list, max_points: int = 2) -> list[tuple]:
    """Find important points in the curve (limited to avoid clutter)."""
    key_points = []
    values_arr = np.array(values)
    years_arr = np.array(years)
    
    # First non-zero point
    non_zero_idx = np.where(values_arr > 0)[0]
    if len(non_zero_idx) > 0:
        first_idx = non_zero_idx[0]
        key_points.append((years_arr[first_idx], values_arr[first_idx], 'Start'))
    
    # Final value
    if values[-1] > 0:
        key_points.append((years_arr[-1], values_arr[-1], 'Final'))
    
    return key_points[:max_points]


def plot_six_comparison(copysets2_file: str, copysets224_file: str, 
                        copysets248_file: str, copysets296_file: str,
                        copysets2384_file: str, random2_file: str,
                        output_path: str, title_suffix: str) -> None:
    """Create a 6-way comparison plot."""
    
    # Parse all six files
    data_2 = parse_simulation_file(copysets2_file)
    data_224 = parse_simulation_file(copysets224_file)
    data_248 = parse_simulation_file(copysets248_file)
    data_296 = parse_simulation_file(copysets296_file)
    data_2384 = parse_simulation_file(copysets2384_file)
    data_r2 = parse_simulation_file(random2_file)
    
    years_2 = scale_to_years(data_2['timestamps'])
    years_224 = scale_to_years(data_224['timestamps'])
    years_248 = scale_to_years(data_248['timestamps'])
    years_296 = scale_to_years(data_296['timestamps'])
    years_2384 = scale_to_years(data_2384['timestamps'])
    years_r2 = scale_to_years(data_r2['timestamps'])
    
    lost_2 = data_2['lost_percent']
    lost_224 = data_224['lost_percent']
    lost_248 = data_248['lost_percent']
    lost_296 = data_296['lost_percent']
    lost_2384 = data_2384['lost_percent']
    lost_r2 = data_r2['lost_percent']
    
    plt.figure(figsize=(15, 9))
    
    # Plot all six lines
    plt.plot(years_2, lost_2, linewidth=2.5, color='black', 
             label='Copysets_2', marker='o', markersize=3, markevery=max(1, len(years_2)//30))
    plt.plot(years_224, lost_224, linewidth=2.5, color='#16a34a',
             label='Copysets_224', marker='s', markersize=3, markevery=max(1, len(years_224)//30))
    plt.plot(years_248, lost_248, linewidth=2.5, color='#dc2626',
             label='Copysets_248', marker='D', markersize=3, markevery=max(1, len(years_248)//30))
    plt.plot(years_296, lost_296, linewidth=2.5, color='#f97316',
             label='Copysets_296', marker='v', markersize=3, markevery=max(1, len(years_296)//30))
    plt.plot(years_2384, lost_2384, linewidth=2.5, color='#eab308',
             label='Copysets_2384', marker='p', markersize=3, markevery=max(1, len(years_2384)//30))
    plt.plot(years_r2, lost_r2, linewidth=2.5, color='#2563eb',
             label='Random_2', marker='^', markersize=3, markevery=max(1, len(years_r2)//30))
    
    # Annotate key points for each (limited to avoid clutter)
    offset_y = [12, -4, -8, -12, -16, 16]
    colors = ['black', '#16a34a', '#dc2626', '#f97316', '#eab308', '#2563eb']
    data_sets = [(years_2, lost_2), (years_224, lost_224), (years_248, lost_248), 
                 (years_296, lost_296), (years_2384, lost_2384), (years_r2, lost_r2)]
    labels = ['Copysets_2', 'Copysets_224', 'Copysets_248', 'Copysets_296', 'Copysets_2384', 'Random_2']
    
    for i, ((years, lost), color, label) in enumerate(zip(data_sets, colors, labels)):
        key_points = find_key_points(years, lost)
        for x, y, pt_label in key_points:
            if y > 0:
                plt.annotate(f'{label}\n{pt_label}: {y:.1f}%', 
                            xy=(x, y), xytext=(x + 0.15, y + offset_y[i]),
                            fontsize=6, color=color,
                            arrowprops=dict(arrowstyle='->', color=color, lw=0.5),
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.85))
    
    plt.xlabel('Time (Years)', fontsize=12)
    plt.ylabel('Lost Objects (%)', fontsize=12)
    plt.title(f'Lost Objects Percentage: 6-Way Comparison\n({title_suffix})', 
              fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 10)
    plt.ylim(0, 105)
    plt.yticks(range(0, 105, 5))
    
    # Stats box
    stats_text = (
        f"Copysets_2:    Final={lost_2[-1]:6.2f}%, Max={max(lost_2):6.2f}%\n"
        f"Copysets_224:  Final={lost_224[-1]:6.2f}%, Max={max(lost_224):6.2f}%\n"
        f"Copysets_248:  Final={lost_248[-1]:6.2f}%, Max={max(lost_248):6.2f}%\n"
        f"Copysets_296:  Final={lost_296[-1]:6.2f}%, Max={max(lost_296):6.2f}%\n"
        f"Copysets_2384: Final={lost_2384[-1]:6.2f}%, Max={max(lost_2384):6.2f}%\n"
        f"Random_2:      Final={lost_r2[-1]:6.2f}%, Max={max(lost_r2):6.2f}%"
    )
    plt.text(0.98, 0.02, stats_text, transform=plt.gca().transAxes, 
             fontsize=8, verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='gray', alpha=0.9),
             family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Saved: {Path(output_path).name}")


def find_six_sets(input_folder: Path) -> list[tuple]:
    """
    Find all sets of six files with same endings.
    """
    six_sets = []
    
    copysets2_files = list(input_folder.glob("copysets_2_*.txt"))
    for file2 in copysets2_files:
        suffix = file2.name.replace("copysets_2_", "")
        file224 = input_folder / f"copysets_224_{suffix}"
        file248 = input_folder / f"copysets_248_{suffix}"
        file296 = input_folder / f"copysets_296_{suffix}"
        file2384 = input_folder / f"copysets_2384_{suffix}"
        file_r2 = input_folder / f"random_2_{suffix}"
        
        if all(f.exists() for f in [file224, file248, file296, file2384, file_r2]):
            six_sets.append((file2, file224, file248, file296, file2384, file_r2, suffix.replace(".txt", "")))
    
    return six_sets


def main() -> None:
    """Main entry point - process all six sets."""
    input_folder = Path(__file__).parent / "input"
    output_folder = Path(__file__).parent / "output"
    output_folder.mkdir(exist_ok=True)
    
    six_sets = find_six_sets(input_folder)
    
    if not six_sets:
        print("No matching six sets found!")
        return
    
    print(f"Found {len(six_sets)} six sets to compare\n")
    print("=== Copysets_2 (black) | Copysets_224 (green) | Copysets_248 (red) | Copysets_296 (orange) | Copysets_2384 (yellow) | Random_2 (blue) ===\n")
    
    for file2, file224, file248, file296, file2384, file_r2, suffix in sorted(six_sets, key=lambda x: x[6]):
        print(f"  {suffix}")
        output_file = output_folder / f"comparison_6way_{suffix}.png"
        plot_six_comparison(
            str(file2), str(file224), str(file248), str(file296), str(file2384), str(file_r2),
            str(output_file), suffix
        )
    
    print(f"\nDone! Generated {len(six_sets)} 6-way comparison graphs in output/")


if __name__ == "__main__":
    main()
