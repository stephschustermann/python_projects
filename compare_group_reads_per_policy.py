#!/usr/bin/env python3
"""
Compare different group reads values per policy.
Creates one set of graphs per policy, with each line representing a different group_read value.
"""

import os
import re
import matplotlib
matplotlib.use('Agg')  # Prevent GUI issues
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict

def parse_file(filepath):
    """Parse a snapshot file and extract metrics over time."""
    timestamps = []
    lost_objects_pct = []
    wet_tubes_pct = []
    cache_pct = []
    expired_total_pct = []
    expired_by_time_pct = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find the data start (header is on line 0, data starts on line 1)
    data_start = 1
    
    # Parse data with accumulation
    total_objects = 1000000
    cumulative_lost = 0
    cumulative_expired_reads = 0
    cumulative_expired_time = 0
    
    for line in lines[data_start:]:
        line = line.strip()
        if not line or line.startswith('==='):
            continue
        
        parts = line.split(',')
        if len(parts) < 27:
            continue
        
        try:
            # Column mapping for new format:
            # 0: timestamp
            # 13: tubes_wetted_percent  
            # 22: objects_lost_since_last_snap
            # 25: total objects in cache
            # 14: tubes_expired_by_reads_since_last_snap
            # 17: tubes_expired_by_time_since_last_snap
            
            timestamp = float(parts[0])
            wet_tubes_percent = float(parts[13])
            objects_lost_increment = int(parts[22])
            cache_objects = int(parts[25])
            expired_reads_increment = int(parts[14])
            expired_time_increment = int(parts[17])
            
            # Accumulate incremental values
            cumulative_lost += objects_lost_increment
            cumulative_expired_reads += expired_reads_increment
            cumulative_expired_time += expired_time_increment
            
            # Store values
            timestamps.append(timestamp)  # Already in years
            lost_objects_pct.append((cumulative_lost / total_objects) * 100)
            wet_tubes_pct.append(wet_tubes_percent)  # Already a percentage
            cache_pct.append((cache_objects / total_objects) * 100)
            
            total_expired = cumulative_expired_reads + cumulative_expired_time
            expired_total_pct.append(total_expired)
            expired_by_time_pct.append(cumulative_expired_time)
            
        except (ValueError, IndexError) as e:
            continue
    
    return {
        'timestamps': timestamps,
        'lost_objects_pct': lost_objects_pct,
        'wet_tubes_pct': wet_tubes_pct,
        'cache_pct': cache_pct,
        'expired_total_pct': expired_total_pct,
        'expired_by_time_pct': expired_by_time_pct
    }

def extract_param_pattern(filename):
    """Extract parameter pattern from filename (e.g., maxReads_100_accessRate_100_dist_Uniform)."""
    # Remove timestamp and extension
    pattern = re.sub(r'_\d{8}_\d{6}\.txt$', '', filename)
    return pattern

def plot_group_reads_comparison(all_data, policy_display, param_pattern, output_dir, final_values):
    """Create a 4-panel comparison plot for different group reads values."""
    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3, width_ratios=[2, 2, 1])
    
    colors = {
        '1': '#e74c3c',    # Red
        '5': '#3498db',    # Blue
        '10': '#2ecc71',   # Green
        '20': '#9b59b6'    # Purple
    }
    
    group_read_names = {
        '1': 'Group Read = 1',
        '5': 'Group Read = 5',
        '10': 'Group Read = 10',
        '20': 'Group Read = 20'
    }
    
    # Sort group_read values for consistent ordering
    sorted_group_reads = sorted(all_data.keys(), key=lambda x: int(x))
    
    # Plot 1: Lost Objects
    ax1 = fig.add_subplot(gs[0, 0])
    for group_read in sorted_group_reads:
        data = all_data[group_read]
        ax1.plot(data['timestamps'], data['lost_objects_pct'], 
                label=group_read_names[group_read], linewidth=2, color=colors[group_read])
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', fontsize=12)
    ax1.set_title('Lost Objects Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_xlim(0, 10)
    
    # Plot 2: Wet Tubes
    ax2 = fig.add_subplot(gs[0, 1])
    for group_read in sorted_group_reads:
        data = all_data[group_read]
        ax2.plot(data['timestamps'], data['wet_tubes_pct'], 
                label=group_read_names[group_read], linewidth=2, color=colors[group_read])
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Wet Tubes (%)', fontsize=12)
    ax2.set_title('Wet Tubes Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_xlim(0, 10)
    
    # Plot 3: Objects in Cache
    ax3 = fig.add_subplot(gs[1, 0])
    for group_read in sorted_group_reads:
        data = all_data[group_read]
        ax3.plot(data['timestamps'], data['cache_pct'], 
                label=group_read_names[group_read], linewidth=2, color=colors[group_read])
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Objects in Cache (%)', fontsize=12)
    ax3.set_title('Objects in Cache Over Time', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=10)
    ax3.set_xlim(0, 10)
    
    # Plot 4: Expired Tubes
    ax4 = fig.add_subplot(gs[1, 1])
    for group_read in sorted_group_reads:
        data = all_data[group_read]
        # Dashed line for expired by time
        ax4.plot(data['timestamps'], data['expired_by_time_pct'], 
                linestyle='--', linewidth=1.5, color=colors[group_read], alpha=0.7)
        # Solid line for total expired
        ax4.plot(data['timestamps'], data['expired_total_pct'], 
                label=group_read_names[group_read], linewidth=2, color=colors[group_read])
    ax4.set_xlabel('Time (years)', fontsize=12)
    ax4.set_ylabel('Expired Tubes (%)', fontsize=12)
    ax4.set_title('Expired Tubes Over Time\n(Dashed: By Time, Solid: Total)', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=10)
    ax4.set_xlim(0, 10)
    
    # Add table for final values
    ax_table = fig.add_subplot(gs[:, 2])
    ax_table.axis('off')
    
    table_data = []
    cell_colors = []
    for group_read in sorted_group_reads:
        final_lost = final_values[group_read]
        table_data.append([group_read_names[group_read], f'{final_lost:.2f}%'])
        cell_colors.append([colors[group_read], colors[group_read]])
    
    table = ax_table.table(cellText=table_data,
                          colLabels=['Group Read', 'Final Lost Objects'],
                          cellColours=cell_colors,
                          loc='center',
                          cellLoc='left',
                          colWidths=[0.6, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)
    
    # Style the header
    for i in range(2):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Main title
    fig.suptitle(f'Group Reads Comparison: {policy_display}\n{param_pattern.replace("_", " ")}',
                fontsize=16, fontweight='bold', y=0.98)
    
    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{policy_display.lower().replace(" ", "_")}_{param_pattern}_{timestamp}.png'
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def main():
    print("=" * 80)
    print("GROUP READS COMPARISON ANALYSIS PER POLICY")
    print("=" * 80)
    print()
    
    # Base directory
    base_dir = 'input/snaps/new_snaps_group_reads'
    
    # Group read values
    group_read_values = ['1', '5', '10', '20']
    
    # Policy information
    policies = {
        'clustered_random': 'Clustered Random',
        'sha': 'SHA',
        'copysets': 'Copysets',
        'tube_replication': 'Tube Replication'
    }
    
    # Create output directory
    output_base = 'output/group_reads_comparisons'
    os.makedirs(output_base, exist_ok=True)
    
    # Process each policy
    for policy_folder, policy_display in policies.items():
        print("=" * 80)
        print(f"Processing Policy: {policy_display}")
        print("=" * 80)
        print()
        
        # Create policy-specific output directory
        policy_output_dir = os.path.join(output_base, policy_folder)
        os.makedirs(policy_output_dir, exist_ok=True)
        
        # Collect all files for this policy across all group_read values
        files_by_pattern = defaultdict(dict)  # pattern -> {group_read: filepath}
        
        for group_read in group_read_values:
            policy_dir = os.path.join(base_dir, f'{group_read}_group_read', policy_folder)
            
            if not os.path.exists(policy_dir):
                print(f"Warning: Folder not found: {policy_dir}")
                continue
            
            # Get all files in this policy folder
            files = [f for f in os.listdir(policy_dir) if f.endswith('.txt')]
            
            for filename in files:
                param_pattern = extract_param_pattern(filename)
                filepath = os.path.join(policy_dir, filename)
                files_by_pattern[param_pattern][group_read] = filepath
        
        # Filter to only patterns that have all group_read values
        complete_patterns = {
            pattern: files for pattern, files in files_by_pattern.items()
            if len(files) == len(group_read_values)
        }
        
        if not complete_patterns:
            print(f"Warning: No complete patterns found for {policy_display}")
            print()
            continue
        
        print(f"{policy_display}: Found {len(complete_patterns)} matching parameter patterns")
        
        # Process each parameter pattern
        for param_pattern in sorted(complete_patterns.keys()):
            print(f"  Processing: {param_pattern}")
            
            # Parse all files for this pattern
            all_data = {}
            final_values = {}
            
            for group_read in group_read_values:
                filepath = complete_patterns[param_pattern][group_read]
                try:
                    data = parse_file(filepath)
                    if data['timestamps']:
                        all_data[group_read] = data
                        final_values[group_read] = data['lost_objects_pct'][-1]
                except Exception as e:
                    print(f"    Error parsing {filepath}: {e}")
            
            if len(all_data) == len(group_read_values):
                output_path = plot_group_reads_comparison(
                    all_data, policy_display, param_pattern, policy_output_dir, final_values
                )
                print(f"    Saved: {output_path}")
                print(f"    Final Lost Objects:")
                for group_read in sorted(all_data.keys(), key=lambda x: int(x)):
                    print(f"      Group Read {group_read:>2}: {final_values[group_read]:6.2f}%")
            else:
                print(f"    Skipping {param_pattern} - incomplete data")
            
        print()
    
    print("=" * 80)
    print(f"Comparison complete! Check {output_base}/ folder (organized by policy)")
    print("=" * 80)

if __name__ == '__main__':
    main()
