"""
Tube Simulation Data Visualizer
Plots lost objects, lost percent, failed reads, and failed percent over time.
"""

import os
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required. Install it with:")
    print("  pip3 install --user --break-system-packages matplotlib")
    exit(1)


def parse_simulation_file(filepath: str) -> dict:
    """
    Parse a simulation output file and extract all metrics.
    
    Returns:
        Dictionary with timestamps and all 4 metrics
    """
    timestamps = []
    lost_objects = []
    lost_percent = []
    failed_reads = []
    failed_percent = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Data starts at line 5 (index 4) after the headers
    for line in lines[4:]:
        line = line.strip()
        if not line:
            continue
        
        values = [v.strip() for v in line.split(',')]
        if len(values) >= 12:
            try:
                timestamps.append(float(values[0]))
                lost_objects.append(float(values[8]))   # m_lost_objects
                lost_percent.append(float(values[9]))   # m_lost_percent
                failed_reads.append(float(values[10]))  # m_failed_reads
                failed_percent.append(float(values[11])) # m_failed_percent
            except ValueError:
                continue
    
    return {
        'timestamps': timestamps,
        'lost_objects': lost_objects,
        'lost_percent': lost_percent,
        'failed_reads': failed_reads,
        'failed_percent': failed_percent
    }


def scale_to_years(timestamps: list[float], max_years: float = 10.0) -> list[float]:
    """Scale timestamps so that max timestamp = max_years."""
    if not timestamps or max(timestamps) == 0:
        return timestamps
    scale_factor = max_years / max(timestamps)
    return [t * scale_factor for t in timestamps]


def plot_all_metrics(filepath: str, output_path: str) -> None:
    """
    Create a 2x2 subplot with all 4 metrics over time.
    """
    data = parse_simulation_file(filepath)
    years = scale_to_years(data['timestamps'], max_years=10.0)
    
    filename = Path(filepath).name
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Simulation Metrics Over Time\n{filename}', fontsize=14, fontweight='bold')
    
    metrics = [
        ('lost_objects', 'Lost Objects', '#e63946'),
        ('lost_percent', 'Lost Percent (%)', '#457b9d'),
        ('failed_reads', 'Failed Reads', '#2a9d8f'),
        ('failed_percent', 'Failed Percent (%)', '#e9c46a')
    ]
    
    for ax, (key, label, color) in zip(axes.flat, metrics):
        values = data[key]
        ax.plot(years, values, linewidth=1.5, color=color, marker='o', markersize=2, markevery=max(1, len(years)//50))
        ax.set_xlabel('Time (Years)', fontsize=10)
        ax.set_ylabel(label, fontsize=10)
        ax.set_title(label, fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 10)
        
        # Add stats
        max_val = max(values) if values else 0
        final_val = values[-1] if values else 0
        ax.text(0.02, 0.98, f'Max: {max_val:,.2f}\nFinal: {final_val:,.2f}', 
                transform=ax.transAxes, verticalalignment='top',
                fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Plot saved to: {output_path}")


def main() -> None:
    """Main entry point - process all files in the input folder."""
    input_folder = Path(__file__).parent / "input"
    output_folder = Path(__file__).parent / "output"
    output_folder.mkdir(exist_ok=True)
    
    if not input_folder.exists():
        print(f"Input folder not found: {input_folder}")
        return
    
    files = sorted(input_folder.glob("*.txt"))
    
    if not files:
        print("No .txt files found in input folder")
        return
    
    print(f"Found {len(files)} files to process\n")
    
    for i, file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing: {file.name}")
        
        data = parse_simulation_file(str(file))
        print(f"  Data points: {len(data['timestamps'])}")
        print(f"  Lost objects range: {min(data['lost_objects']):.0f} - {max(data['lost_objects']):.0f}")
        print(f"  Lost percent range: {min(data['lost_percent']):.2f} - {max(data['lost_percent']):.2f}%")
        print(f"  Failed reads range: {min(data['failed_reads']):.0f} - {max(data['failed_reads']):.0f}")
        print(f"  Failed percent range: {min(data['failed_percent']):.2f} - {max(data['failed_percent']):.2f}%")
        
        output_file = output_folder / f"{file.stem}_graph.png"
        plot_all_metrics(str(file), str(output_file))
        print()


if __name__ == "__main__":
    main()
