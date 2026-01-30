#!/usr/bin/env python3
"""
Compare 3 scenarios for EACH policy:
1. Baseline (new_snaps)
2. With Replenishment (new_snaps_replanishment)
3. With Replenishment + Tube Expiration (new_snaps_tube_exp)

For each policy, create a comparison showing all 3 scenarios.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime
from collections import defaultdict

# Scenario folder mappings for each policy
POLICIES = ['clustered_random', 'sha', 'triplets_copysets', 'tube_replication']

POLICY_DISPLAY_NAMES = {
    'clustered_random': 'Clustered Random',
    'sha': 'SHA',
    'triplets_copysets': 'Copysets',
    'tube_replication': 'Tube Replication'
}

def get_scenario_folders(policy):
    """Get the three scenario folders for a given policy."""
    
    # Handle special case for clustered_random in baseline
    if policy == 'clustered_random':
        baseline_folder = 'input/snaps/new_snaps_clustered_random_small'
    else:
        baseline_folder = f'input/snaps/new_snaps_{policy}'
    
    return {
        'Baseline': baseline_folder,
        'Replenishment': f'input/snaps/new_snaps_replanishment_{policy}',
        'Repl + AlmostTerminated': f'input/snaps/new_snaps_tube_exp_{policy}'
    }

# Colors for each scenario
SCENARIO_COLORS = {
    'Baseline': '#e74c3c',              # red
    'Replenishment': '#3498db',         # blue
    'Repl + AlmostTerminated': '#2ecc71'      # green
}

def parse_snaps_file(filepath):
    """Parse a snaps file and extract key metrics."""
    
    data = {
        'timestamp': [],
        'objects_lost_since_snap': [],
        'total_objects_in_system': [],
        'total_objects_in_cache': [],
        'tubes_wetted_percent': [],
        'tubes_expired_by_reads_percent': [],
        'tubes_expired_by_time_percent': []
    }
    
    try:
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
                elif col == 'tubes_expired_by_reads_percent':
                    col_indices['expired_reads'] = i
                elif col == 'tubes_expired_by_time_percent':
                    col_indices['expired_time'] = i
            
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
                    data['tubes_expired_by_reads_percent'].append(float(parts[col_indices['expired_reads']]))
                    data['tubes_expired_by_time_percent'].append(float(parts[col_indices['expired_time']]))
                except (ValueError, IndexError, KeyError):
                    continue
    
    except FileNotFoundError:
        return None
    
    return data

def calculate_metrics(data, total_objects=1000000):
    """Calculate derived metrics."""
    
    if not data or len(data['timestamp']) == 0:
        return None
    
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
    
    # Calculate total expired (by reads + by time)
    total_expired_percent = [
        reads + time 
        for reads, time in zip(data['tubes_expired_by_reads_percent'], 
                               data['tubes_expired_by_time_percent'])
    ]
    
    return {
        'lost_objects_percent': lost_objects_percent,
        'objects_in_cache_percent': objects_in_cache_percent,
        'total_expired_percent': total_expired_percent
    }

def extract_param_pattern(filename):
    """Extract parameter pattern from filename (without timestamp)."""
    parts = filename.replace('.txt', '').split('_')
    
    # Find where the timestamp starts
    param_parts = []
    for i, part in enumerate(parts):
        if len(part) == 8 and part.isdigit():
            break
        param_parts.append(part)
    
    return '_'.join(param_parts)

def find_matching_files_for_policy(policy):
    """Find files with matching parameter patterns across all 3 scenarios for a policy."""
    
    scenario_folders = get_scenario_folders(policy)
    file_groups = defaultdict(dict)
    
    for scenario_name, folder_path in scenario_folders.items():
        if not os.path.exists(folder_path):
            print(f"  Warning: Folder not found: {folder_path}")
            continue
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        
        for filename in files:
            param_pattern = extract_param_pattern(filename)
            file_groups[param_pattern][scenario_name] = os.path.join(folder_path, filename)
    
    # Filter to only files present in all 3 scenarios
    complete_groups = {pattern: scenarios for pattern, scenarios in file_groups.items() 
                       if len(scenarios) == 3}
    
    return complete_groups

def compare_scenarios_for_policy(policy, file_groups, output_dir='output/scenario_comparisons'):
    """Create comparison visualizations for a specific policy across scenarios."""
    
    policy_output_dir = os.path.join(output_dir, policy)
    os.makedirs(policy_output_dir, exist_ok=True)
    
    policy_display = POLICY_DISPLAY_NAMES[policy]
    
    print(f"\n{policy_display}: Found {len(file_groups)} matching parameter patterns")
    
    for param_pattern, scenario_files in sorted(file_groups.items()):
        print(f"  Processing: {param_pattern}")
        
        # Parse all scenario files
        scenario_data = {}
        scenario_metrics = {}
        
        for scenario_name, filepath in scenario_files.items():
            data = parse_snaps_file(filepath)
            if data:
                metrics = calculate_metrics(data)
                if metrics:
                    scenario_data[scenario_name] = data
                    scenario_metrics[scenario_name] = metrics
        
        if len(scenario_data) < 3:
            print(f"    Skipping - not all scenarios have valid data")
            continue
        
        # Create comparison plot (wider to accommodate table)
        fig, axes = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle(f'Scenario Comparison: {policy_display}\n{param_pattern}', 
                     fontsize=16, fontweight='bold')
        
        # Plot 1: Lost Objects Percentage
        ax1 = axes[0, 0]
        
        # Collect final values for table
        final_values = []
        
        for scenario_name in ['Baseline', 'Replenishment', 'Repl + AlmostTerminated']:
            if scenario_name in scenario_metrics:
                data = scenario_data[scenario_name]
                metrics = scenario_metrics[scenario_name]
                ax1.plot(data['timestamp'], metrics['lost_objects_percent'], 
                        linewidth=2.5, label=scenario_name, color=SCENARIO_COLORS[scenario_name])
                
                # Collect final value
                final_val = metrics['lost_objects_percent'][-1]
                final_values.append([scenario_name, f'{final_val:.2f}%'])
        
        ax1.set_xlabel('Time (years)', fontsize=12)
        ax1.set_ylabel('Lost Objects (%)', fontsize=12)
        ax1.set_title('Lost Objects Over Time', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 10)
        
        # Add table with final values
        if final_values:
            table_data = [['Scenario', 'Final Loss']] + final_values
            table = ax1.table(cellText=table_data, 
                            cellLoc='left',
                            loc='right',
                            bbox=[1.02, 0.7, 0.35, 0.25],
                            cellColours=[['lightgray', 'lightgray']] + 
                                       [[SCENARIO_COLORS[row[0]], 'white'] for row in final_values])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
        
        # Plot 2: Wet Tubes Percentage
        ax2 = axes[0, 1]
        for scenario_name in ['Baseline', 'Replenishment', 'Repl + AlmostTerminated']:
            if scenario_name in scenario_data:
                data = scenario_data[scenario_name]
                ax2.plot(data['timestamp'], data['tubes_wetted_percent'], 
                        linewidth=2.5, label=scenario_name, color=SCENARIO_COLORS[scenario_name])
        
        ax2.set_xlabel('Time (years)', fontsize=12)
        ax2.set_ylabel('Wet Tubes (%)', fontsize=12)
        ax2.set_title('Wet Tubes Over Time', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 10)
        
        # Plot 3: Objects in Cache Percentage
        ax3 = axes[1, 0]
        for scenario_name in ['Baseline', 'Replenishment', 'Repl + AlmostTerminated']:
            if scenario_name in scenario_metrics:
                data = scenario_data[scenario_name]
                metrics = scenario_metrics[scenario_name]
                ax3.plot(data['timestamp'], metrics['objects_in_cache_percent'], 
                        linewidth=2.5, label=scenario_name, color=SCENARIO_COLORS[scenario_name])
        
        ax3.set_xlabel('Time (years)', fontsize=12)
        ax3.set_ylabel('Objects in Cache (%)', fontsize=12)
        ax3.set_title('Objects in Cache Over Time', fontsize=14, fontweight='bold')
        ax3.legend(loc='best', fontsize=11)
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, 10)
        
        # Plot 4: Expired Tubes Percentage
        ax4 = axes[1, 1]
        
        # Plot expired by time (dashed) and total expired (solid) for each scenario
        for scenario_name in ['Baseline', 'Replenishment', 'Repl + AlmostTerminated']:
            if scenario_name in scenario_data and scenario_name in scenario_metrics:
                data = scenario_data[scenario_name]
                metrics = scenario_metrics[scenario_name]
                
                # Expired by time (dashed)
                ax4.plot(data['timestamp'], data['tubes_expired_by_time_percent'], 
                        linewidth=1.5, color=SCENARIO_COLORS[scenario_name],
                        linestyle='--', alpha=0.7)
                
                # Total expired (solid)
                ax4.plot(data['timestamp'], metrics['total_expired_percent'], 
                        linewidth=2.5, label=scenario_name, color=SCENARIO_COLORS[scenario_name])
        
        ax4.set_xlabel('Time (years)', fontsize=12)
        ax4.set_ylabel('Expired Tubes (%)', fontsize=12)
        ax4.set_title('Expired Tubes Over Time\n(Dashed: By Time, Solid: Total)', 
                     fontsize=14, fontweight='bold')
        ax4.legend(loc='best', fontsize=11)
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, 10)
        
        plt.tight_layout(rect=[0, 0, 0.85, 1])  # Leave space on right for table
        
        # Save the figure
        output_filename = f'{policy}_{param_pattern}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        output_path = os.path.join(policy_output_dir, output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Saved: {output_path}")
        
        # Print summary
        print(f"    Final Lost Objects:")
        for scenario_name in ['Baseline', 'Replenishment', 'Repl + AlmostTerminated']:
            if scenario_name in scenario_metrics:
                final_loss = scenario_metrics[scenario_name]['lost_objects_percent'][-1]
                print(f"      {scenario_name:20s}: {final_loss:6.2f}%")

if __name__ == '__main__':
    print("="*80)
    print("SCENARIO COMPARISON ANALYSIS PER POLICY")
    print("="*80)
    print("\nScenarios:")
    print("  1. Baseline - standard operation")
    print("  2. Replenishment - with cache replenishment")
    print("  3. Repl + AlmostTerminated - replenishment + tube expiration at 20 reads")
    print("="*80)
    
    total_comparisons = 0
    
    for policy in POLICIES:
        print(f"\n{'='*80}")
        print(f"Processing Policy: {POLICY_DISPLAY_NAMES[policy]}")
        print('='*80)
        
        # Find matching files for this policy
        file_groups = find_matching_files_for_policy(policy)
        
        if not file_groups:
            print(f"  No matching files found across all 3 scenarios for {policy}!")
            continue
        
        # Create comparisons for this policy
        compare_scenarios_for_policy(policy, file_groups)
        total_comparisons += len(file_groups)
    
    print("\n" + "="*80)
    print(f"Comparison complete! Generated {total_comparisons} total comparisons")
    print(f"Check output/scenario_comparisons/ folder (organized by policy)")
    print("="*80)
