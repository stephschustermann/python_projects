#!/usr/bin/env python3
"""
Enhanced analysis including tube counts to understand the relationship
between wet tubes, objects, and loss.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime

def parse_snaps_file_with_tubes(filepath):
    """Parse the snaps output file including tube information."""
    
    print(f"Reading file: {filepath}")
    
    data = {
        'timestamp': [],
        'objects_lost_since_snap': [],
        'total_objects_in_system': [],
        'total_objects_in_cache': [],
        'tubes_wetted_percent': [],
        'tubes_expired_by_reads': [],
        'tubes_expired_by_time': [],
        'tubes_destroyed': [],
        'tubes_created': [],
        'available_tubes': []
    }
    
    with open(filepath, 'r') as f:
        header = f.readline().strip()
        columns = [col.strip() for col in header.split(',')]
        
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
            elif col == 'tubes_expired_by_reads_since_last_snap':
                col_indices['expired_reads'] = i
            elif col == 'tubes_expired_by_time_since_last_snap':
                col_indices['expired_time'] = i
            elif col == 'tubes_destroyed_since_last_snap':
                col_indices['tubes_destroyed'] = i
            elif col == 'tubes_created_from_cache_since_last_snap':
                col_indices['tubes_created'] = i
            elif col == 'available tubes in the system':
                col_indices['available_tubes'] = i
        
        # Read data rows
        for line in f:
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
                data['tubes_expired_by_reads'].append(float(parts[col_indices['expired_reads']]))
                data['tubes_expired_by_time'].append(float(parts[col_indices['expired_time']]))
                data['tubes_destroyed'].append(float(parts[col_indices['tubes_destroyed']]))
                data['tubes_created'].append(float(parts[col_indices['tubes_created']]))
                data['available_tubes'].append(float(parts[col_indices['available_tubes']]))
            except (ValueError, IndexError):
                continue
    
    print(f"Total rows parsed: {len(data['timestamp'])}")
    return data

def analyze_with_explanation(input_file, total_objects=1000000):
    """Analyze and explain the relationship between tubes and objects."""
    
    data = parse_snaps_file_with_tubes(input_file)
    
    # Calculate cumulative values
    cumulative_lost = []
    cumulative_tubes_destroyed = []
    cumulative_tubes_created = []
    
    total_lost = 0
    total_destroyed = 0
    total_created = 0
    
    for i in range(len(data['timestamp'])):
        total_lost += data['objects_lost_since_snap'][i]
        total_destroyed += data['tubes_destroyed'][i]
        total_created += data['tubes_created'][i]
        cumulative_lost.append(total_lost)
        cumulative_tubes_destroyed.append(total_destroyed)
        cumulative_tubes_created.append(total_created)
    
    # Calculate objects in tubes (not in cache)
    objects_in_tubes = [
        data['total_objects_in_system'][i] - data['total_objects_in_cache'][i]
        for i in range(len(data['timestamp']))
    ]
    
    # Create visualization
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    filename = os.path.basename(input_file)
    fig.suptitle(f'Understanding Wet Tubes vs Lost Objects\n{filename}', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Objects distribution
    ax1 = axes[0, 0]
    ax1.plot(data['timestamp'], data['total_objects_in_cache'], 
             label='In Cache', linewidth=2, color='#2ca02c')
    ax1.plot(data['timestamp'], objects_in_tubes, 
             label='In Tubes', linewidth=2, color='#1f77b4')
    ax1.plot(data['timestamp'], cumulative_lost, 
             label='Lost', linewidth=2, color='#d62728')
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Number of Objects', fontsize=12)
    ax1.set_title('Where Are The Objects?', fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Tube counts
    ax2 = axes[0, 1]
    ax2.plot(data['timestamp'], cumulative_tubes_created, 
             label='Tubes Created', linewidth=2, color='#2ca02c')
    ax2.plot(data['timestamp'], cumulative_tubes_destroyed, 
             label='Tubes Destroyed', linewidth=2, color='#d62728')
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Cumulative Tube Count', fontsize=12)
    ax2.set_title('Tube Creation vs Destruction', fontsize=14, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Wet tubes percentage
    ax3 = axes[1, 0]
    ax3.plot(data['timestamp'], data['tubes_wetted_percent'], 
             linewidth=2, color='#1f77b4')
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Wet Tubes (%)', fontsize=12)
    ax3.set_title('Wet Tubes (% of EXISTING tubes)', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=100, color='red', linestyle='--', alpha=0.5)
    
    # Plot 4: Cumulative loss percentage
    ax4 = axes[1, 1]
    lost_pct = [(lost / total_objects) * 100 for lost in cumulative_lost]
    ax4.plot(data['timestamp'], lost_pct, linewidth=2, color='#d62728')
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Lost Objects (%)', fontsize=12)
    ax4.set_title('Cumulative Object Loss', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Tubes destroyed vs objects lost
    ax5 = axes[2, 0]
    ax5.plot(data['timestamp'], cumulative_tubes_destroyed, 
             label='Tubes Destroyed', linewidth=2, color='#ff7f0e')
    ax5_twin = ax5.twinx()
    ax5_twin.plot(data['timestamp'], cumulative_lost, 
                  label='Objects Lost', linewidth=2, color='#d62728')
    ax5.set_xlabel('Time (years)', fontsize=12)
    ax5.set_ylabel('Tubes Destroyed', fontsize=12, color='#ff7f0e')
    ax5_twin.set_ylabel('Objects Lost', fontsize=12, color='#d62728')
    ax5.set_title('Tube Destruction Causes Object Loss', fontsize=14, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Objects per tube ratio
    ax6 = axes[2, 1]
    # Calculate ratio where tubes exist
    objects_per_tube = []
    time_for_ratio = []
    for i in range(len(data['timestamp'])):
        if objects_in_tubes[i] > 0 and cumulative_tubes_created[i] > cumulative_tubes_destroyed[i]:
            existing_tubes = cumulative_tubes_created[i] - cumulative_tubes_destroyed[i]
            ratio = objects_in_tubes[i] / existing_tubes
            objects_per_tube.append(ratio)
            time_for_ratio.append(data['timestamp'][i])
    
    if objects_per_tube:
        ax6.plot(time_for_ratio, objects_per_tube, linewidth=2, color='#9467bd')
        ax6.set_xlabel('Time (years)', fontsize=12)
        ax6.set_ylabel('Objects per Tube', fontsize=12)
        ax6.set_title('Average Objects Stored per Tube', fontsize=14, fontweight='bold')
        ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_dir = 'output/snaps_format2_analysis'
    os.makedirs(output_dir, exist_ok=True)
    file_timestamp = filename.replace('snaps_output_2_', '').replace('.txt', '')
    output_filename = f'tubes_explanation_{file_timestamp}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")
    
    # Generate explanation
    print("\n" + "="*80)
    print("EXPLANATION: WHY 100% WET TUBES BUT NOT 100% LOST OBJECTS")
    print("="*80)
    
    print(f"\n📊 Final State:")
    print(f"   - Objects lost: {cumulative_lost[-1]:,.0f} ({(cumulative_lost[-1]/total_objects)*100:.2f}%)")
    print(f"   - Objects remaining: {data['total_objects_in_system'][-1]:,.0f}")
    print(f"   - Objects in cache: {data['total_objects_in_cache'][-1]:,.0f}")
    print(f"   - Objects in tubes: {objects_in_tubes[-1]:,.0f}")
    print(f"   - Wet tubes: {data['tubes_wetted_percent'][-1]:.2f}%")
    
    print(f"\n📦 Tube Activity:")
    print(f"   - Total tubes created: {cumulative_tubes_created[-1]:,.0f}")
    print(f"   - Total tubes destroyed: {cumulative_tubes_destroyed[-1]:,.0f}")
    print(f"   - Tubes still existing: {cumulative_tubes_created[-1] - cumulative_tubes_destroyed[-1]:,.0f}")
    
    if objects_in_tubes[-1] > 0:
        existing_tubes = cumulative_tubes_created[-1] - cumulative_tubes_destroyed[-1]
        if existing_tubes > 0:
            avg_objects = objects_in_tubes[-1] / existing_tubes
            print(f"   - Avg objects per remaining tube: {avg_objects:.2f}")
    
    print(f"\n💡 KEY INSIGHT:")
    print(f"   'Wet tubes = 100%' means 100% of EXISTING tubes are wet.")
    print(f"   It does NOT mean all tubes that were ever created still exist!")
    print(f"   ")
    print(f"   - When tubes are destroyed, objects in them are LOST")
    print(f"   - The {(cumulative_lost[-1]/total_objects)*100:.1f}% lost objects were in destroyed tubes")
    print(f"   - The remaining {100-(cumulative_lost[-1]/total_objects)*100:.1f}% are in tubes that still exist")
    print(f"   - ALL of those remaining tubes happen to be wet (100% wet tubes)")
    
    print("\n" + "="*80)
    
    return data

if __name__ == '__main__':
    input_file = 'input/snaps/snaps_output_2_20260113_125230.txt'
    analyze_with_explanation(input_file, total_objects=1000000)
