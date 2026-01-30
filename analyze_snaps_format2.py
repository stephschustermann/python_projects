#!/usr/bin/env python3
"""
Analyze snaps_output_2 format to extract:
1. Percentage of lost objects over time
2. Wet tube percentage over time
3. Objects in cache percentage over time
4. Expired tubes percentage over time
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os
from datetime import datetime

def parse_snaps_file(filepath):
    """
    Parse the snaps output file and extract relevant metrics.
    
    Returns dictionaries of lists containing the data.
    """
    
    print(f"Reading file: {filepath}")
    
    # Data storage
    data = {
        'timestamp': [],
        'objects_lost_since_snap': [],
        'total_objects_in_system': [],
        'total_objects_in_cache': [],
        'tubes_wetted_percent': [],
        'tubes_expired_by_reads_percent': [],
        'tubes_expired_by_time_percent': []
    }
    
    with open(filepath, 'r') as f:
        # Read header
        header = f.readline().strip()
        columns = [col.strip() for col in header.split(',')]
        
        print(f"Columns found: {len(columns)}")
        print(f"First few columns: {columns[:5]}")
        
        # Find column indices
        col_indices = {}
        for i, col in enumerate(columns):
            if col == 'timestamp':
                col_indices['timestamp'] = i
            elif col == 'objects_lost_since_last_snap':
                col_indices['objects_lost'] = i
            elif col == 'total objects in the system':
                col_indices['total_objects'] = i
            elif col == 'total objects in cache':
                col_indices['objects_in_cache'] = i
            elif col == 'tubes_wetted_percent':
                col_indices['tubes_wetted'] = i
            elif col == 'tubes_expired_by_reads_percent':
                col_indices['expired_reads'] = i
            elif col == 'tubes_expired_by_time_percent':
                col_indices['expired_time'] = i
        
        print(f"Column indices: {col_indices}")
        
        # Read data rows
        for line_num, line in enumerate(f, start=2):
            line = line.strip()
            if not line:
                continue
                
            parts = [p.strip() for p in line.split(',')]
            
            try:
                data['timestamp'].append(float(parts[col_indices['timestamp']]))
                data['objects_lost_since_snap'].append(float(parts[col_indices['objects_lost']]))
                data['total_objects_in_system'].append(float(parts[col_indices['total_objects']]))
                data['total_objects_in_cache'].append(float(parts[col_indices['objects_in_cache']]))
                data['tubes_wetted_percent'].append(float(parts[col_indices['tubes_wetted']]))
                data['tubes_expired_by_reads_percent'].append(float(parts[col_indices['expired_reads']]))
                data['tubes_expired_by_time_percent'].append(float(parts[col_indices['expired_time']]))
            except (ValueError, IndexError) as e:
                print(f"Warning: Skipping line {line_num} due to parsing error: {e}")
                continue
    
    print(f"Total rows parsed: {len(data['timestamp'])}")
    return data

def calculate_metrics(data, total_objects):
    """
    Calculate derived metrics from the parsed data.
    """
    
    # Calculate cumulative lost objects
    cumulative_lost = []
    total = 0
    for lost in data['objects_lost_since_snap']:
        total += lost
        cumulative_lost.append(total)
    
    # Calculate percentages
    lost_objects_percent = [(lost / total_objects) * 100 for lost in cumulative_lost]
    objects_in_cache_percent = [(cache / total_objects) * 100 
                                 for cache in data['total_objects_in_cache']]
    
    # Total expired tubes percentage
    total_expired_tubes_percent = [
        reads + time 
        for reads, time in zip(data['tubes_expired_by_reads_percent'], 
                               data['tubes_expired_by_time_percent'])
    ]
    
    return {
        'cumulative_lost': cumulative_lost,
        'lost_objects_percent': lost_objects_percent,
        'objects_in_cache_percent': objects_in_cache_percent,
        'total_expired_tubes_percent': total_expired_tubes_percent
    }

def analyze_snaps_format2(input_file, total_objects=1000000, total_time_years=10):
    """
    Analyze snaps output format 2
    
    Parameters:
    -----------
    input_file : str
        Path to snaps output file
    total_objects : int
        Total number of objects in the system (default: 1,000,000)
    total_time_years : int
        Total simulation time in years (default: 10)
    """
    
    # Parse the file
    data = parse_snaps_file(input_file)
    
    # Calculate metrics
    metrics = calculate_metrics(data, total_objects)
    
    # Create output directory
    output_dir = 'output/snaps_format2_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Get timestamp from filename
    filename = os.path.basename(input_file)
    file_timestamp = filename.replace('snaps_output_2_', '').replace('.txt', '')
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Snaps Analysis Over {total_time_years} Years\n{filename}', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Lost Objects Percentage
    ax1 = axes[0, 0]
    ax1.plot(data['timestamp'], metrics['lost_objects_percent'], linewidth=2, color='#d62728')
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', fontsize=12)
    ax1.set_title('Lost Objects Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, total_time_years)
    
    # Add final value annotation
    final_lost_pct = metrics['lost_objects_percent'][-1]
    ax1.text(0.98, 0.95, f'Final: {final_lost_pct:.4f}%', 
             transform=ax1.transAxes, ha='right', va='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Plot 2: Wet Tubes Percentage
    ax2 = axes[0, 1]
    ax2.plot(data['timestamp'], data['tubes_wetted_percent'], linewidth=2, color='#1f77b4')
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=12)
    ax2.set_title('Wet Tubes Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, total_time_years)
    
    # Add statistics
    avg_wet = sum(data['tubes_wetted_percent']) / len(data['tubes_wetted_percent'])
    max_wet = max(data['tubes_wetted_percent'])
    ax2.text(0.98, 0.95, f'Avg: {avg_wet:.2f}%\nMax: {max_wet:.2f}%', 
             transform=ax2.transAxes, ha='right', va='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Plot 3: Objects in Cache Percentage
    ax3 = axes[1, 0]
    ax3.plot(data['timestamp'], metrics['objects_in_cache_percent'], linewidth=2, color='#2ca02c')
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=12)
    ax3.set_title('Objects in Cache Over Time', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, total_time_years)
    
    # Add statistics
    avg_cache = sum(metrics['objects_in_cache_percent']) / len(metrics['objects_in_cache_percent'])
    final_cache = metrics['objects_in_cache_percent'][-1]
    ax3.text(0.98, 0.95, f'Avg: {avg_cache:.2f}%\nFinal: {final_cache:.2f}%', 
             transform=ax3.transAxes, ha='right', va='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Plot 4: Expired Tubes Percentage
    ax4 = axes[1, 1]
    ax4.plot(data['timestamp'], data['tubes_expired_by_time_percent'], linewidth=2, 
             label='Expired by Time', color='#9467bd', linestyle='--')
    ax4.plot(data['timestamp'], metrics['total_expired_tubes_percent'], linewidth=2.5, 
             label='Total Expired', color='#8c564b')
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Expired Tubes (%)', fontsize=12)
    ax4.set_title('Expired Tubes Over Time', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='best', fontsize=10)
    ax4.set_xlim(0, total_time_years)
    
    # Add statistics
    avg_expired = sum(metrics['total_expired_tubes_percent']) / len(metrics['total_expired_tubes_percent'])
    max_expired = max(metrics['total_expired_tubes_percent'])
    ax4.text(0.98, 0.95, f'Avg Total: {avg_expired:.2f}%\nMax Total: {max_expired:.2f}%', 
             transform=ax4.transAxes, ha='right', va='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save the figure
    output_filename = f'snaps_analysis_{file_timestamp}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    
    # Generate summary statistics
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    avg_loss = sum(data['objects_lost_since_snap']) / len(data['objects_lost_since_snap'])
    min_wet = min(data['tubes_wetted_percent'])
    max_cache = max(metrics['objects_in_cache_percent'])
    avg_expired_reads = sum(data['tubes_expired_by_reads_percent']) / len(data['tubes_expired_by_reads_percent'])
    avg_expired_time = sum(data['tubes_expired_by_time_percent']) / len(data['tubes_expired_by_time_percent'])
    
    print(f"\n1. LOST OBJECTS:")
    print(f"   - Total lost objects: {metrics['cumulative_lost'][-1]:,.0f}")
    print(f"   - Percentage of total: {metrics['lost_objects_percent'][-1]:.6f}%")
    print(f"   - Average loss rate: {avg_loss:.2f} objects/snapshot")
    
    print(f"\n2. WET TUBES:")
    print(f"   - Average percentage: {avg_wet:.4f}%")
    print(f"   - Maximum percentage: {max_wet:.4f}%")
    print(f"   - Minimum percentage: {min_wet:.4f}%")
    
    print(f"\n3. OBJECTS IN CACHE:")
    print(f"   - Initial percentage: {metrics['objects_in_cache_percent'][0]:.4f}%")
    print(f"   - Final percentage: {final_cache:.4f}%")
    print(f"   - Average percentage: {avg_cache:.4f}%")
    print(f"   - Maximum percentage: {max_cache:.4f}%")
    
    print(f"\n4. EXPIRED TUBES:")
    print(f"   - Average expired by reads: {avg_expired_reads:.4f}%")
    print(f"   - Average expired by time: {avg_expired_time:.4f}%")
    print(f"   - Average total expired: {avg_expired:.4f}%")
    print(f"   - Maximum total expired: {max_expired:.4f}%")
    
    print("\n" + "="*70)
    
    # Save summary to CSV
    csv_filename = f'snaps_summary_{file_timestamp}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    csv_path = os.path.join(output_dir, csv_filename)
    
    with open(csv_path, 'w') as f:
        # Write header
        f.write('timestamp,lost_objects_percent,cumulative_lost_objects,wet_tubes_percent,')
        f.write('objects_in_cache_percent,expired_tubes_by_reads_percent,')
        f.write('expired_tubes_by_time_percent,total_expired_tubes_percent\n')
        
        # Write data rows
        for i in range(len(data['timestamp'])):
            f.write(f"{data['timestamp'][i]},")
            f.write(f"{metrics['lost_objects_percent'][i]},")
            f.write(f"{metrics['cumulative_lost'][i]},")
            f.write(f"{data['tubes_wetted_percent'][i]},")
            f.write(f"{metrics['objects_in_cache_percent'][i]},")
            f.write(f"{data['tubes_expired_by_reads_percent'][i]},")
            f.write(f"{data['tubes_expired_by_time_percent'][i]},")
            f.write(f"{metrics['total_expired_tubes_percent'][i]}\n")
    
    print(f"Summary data saved to: {csv_path}")
    
    return data, metrics


if __name__ == '__main__':
    # Specify the input file
    input_file = 'input/snaps/snaps_output_2_20260113_180933.txt'
    
    # Run the analysis
    data, metrics = analyze_snaps_format2(
        input_file=input_file,
        total_objects=1000000,
        total_time_years=10
    )
