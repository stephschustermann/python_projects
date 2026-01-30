#!/usr/bin/env python3
"""
Compare Group Read 20 Original vs Refactored
To verify refactoring didn't break anything
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import re

def parse_new_snapshot_file(filepath):
    """Parse the new snapshot file format and return metrics over time."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        return None
    
    # Initialize data structures
    data = {
        'time': [],
        'lost_objects_percent': [],
        'wet_tubes_percent': [],
        'objects_in_cache_percent': [],
        'tubes_expired_by_time_percent': [],
        'tubes_expired_by_reads_percent': [],
        'total_expired_percent': []
    }
    
    cumulative_lost_objects = 0
    TOTAL_OBJECTS = 1_000_000  # As specified
    
    for line in lines[1:]:
        parts = line.strip().split(',')
        if len(parts) < 25:
            continue
        
        try:
            # Extract metrics
            time_years = float(parts[0])
            wet_tubes_percent = float(parts[1])
            objects_in_cache_percent = float(parts[2])
            tubes_expired_by_time_percent = float(parts[3])
            tubes_expired_by_reads_percent = float(parts[4])
            total_expired_percent = float(parts[5])
            objects_lost_since_last_snap = float(parts[22])
            
            # Calculate cumulative lost objects
            cumulative_lost_objects += objects_lost_since_last_snap
            lost_objects_percent = (cumulative_lost_objects / TOTAL_OBJECTS) * 100
            
            # Store data
            data['time'].append(time_years)
            data['lost_objects_percent'].append(lost_objects_percent)
            data['wet_tubes_percent'].append(wet_tubes_percent)
            data['objects_in_cache_percent'].append(objects_in_cache_percent)
            data['tubes_expired_by_time_percent'].append(tubes_expired_by_time_percent)
            data['tubes_expired_by_reads_percent'].append(tubes_expired_by_reads_percent)
            data['total_expired_percent'].append(total_expired_percent)
            
        except (ValueError, IndexError) as e:
            continue
    
    if len(data['time']) == 0:
        return None
    
    return data

def parse_filename(filename):
    """Extract parameters from filename (excluding timestamp)."""
    pattern = r'maxReads_(\d+)_accessRate_(\d+)_dist_(\w+)_'
    match = re.search(pattern, filename)
    if match:
        return {
            'maxReads': match.group(1),
            'accessRate': match.group(2),
            'dist': match.group(3)
        }
    return None

def compare_versions_for_policy(policy_name, policy_folder, original_folder, refactored_folder, output_dir):
    """Compare original vs refactored for a single policy."""
    print(f"\n{'='*80}")
    print(f"Processing Policy: {policy_name}")
    print(f"{'='*80}")
    
    original_path = os.path.join(original_folder, policy_folder)
    refactored_path = os.path.join(refactored_folder, policy_folder)
    
    if not os.path.exists(original_path) or not os.path.exists(refactored_path):
        print(f"  ⚠️  Warning: Missing folders for {policy_name}")
        return
    
    # Get files from both versions
    original_files = {}
    refactored_files = {}
    
    for filename in os.listdir(original_path):
        if filename.endswith('.txt'):
            params = parse_filename(filename)
            if params:
                key = f"maxReads_{params['maxReads']}_accessRate_{params['accessRate']}_dist_{params['dist']}"
                original_files[key] = os.path.join(original_path, filename)
    
    for filename in os.listdir(refactored_path):
        if filename.endswith('.txt'):
            params = parse_filename(filename)
            if params:
                key = f"maxReads_{params['maxReads']}_accessRate_{params['accessRate']}_dist_{params['dist']}"
                refactored_files[key] = os.path.join(refactored_path, filename)
    
    print(f"  Original files: {list(original_files.keys())}")
    print(f"  Refactored files: {list(refactored_files.keys())}")
    
    # Find common patterns
    common_keys = set(original_files.keys()) & set(refactored_files.keys())
    
    print(f"\n{policy_name}: Found {len(common_keys)} matching parameter patterns")
    
    if len(common_keys) == 0:
        print(f"  ⚠️  Warning: No matching files found!")
        return
    
    # Create output directory for this policy
    policy_output_dir = os.path.join(output_dir, policy_folder)
    os.makedirs(policy_output_dir, exist_ok=True)
    
    for key in sorted(common_keys):
        print(f"  Processing: {key}")
        
        # Parse both versions
        original_data = parse_new_snapshot_file(original_files[key])
        refactored_data = parse_new_snapshot_file(refactored_files[key])
        
        if original_data is None or refactored_data is None:
            print(f"    ⚠️  Warning: Failed to parse data")
            continue
        
        # Create comparison plot
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Group Read 20: Original vs Refactored - {policy_name}\n{key}', 
                    fontsize=16, fontweight='bold')
        
        versions = ['Original', 'Refactored']
        colors = ['#FF6B6B', '#4ECDC4']
        line_styles = ['-', '--']
        
        datasets = [original_data, refactored_data]
        
        # Plot 1: Lost Objects
        ax = axes[0, 0]
        for i, (version, data) in enumerate(zip(versions, datasets)):
            ax.plot(data['time'], data['lost_objects_percent'], 
                   label=version, color=colors[i], linestyle=line_styles[i], linewidth=2)
        ax.set_xlabel('Time (years)', fontsize=12)
        ax.set_ylabel('Lost Objects (%)', fontsize=12)
        ax.set_title('Lost Objects Over Time', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Plot 2: Wet Tubes
        ax = axes[0, 1]
        for i, (version, data) in enumerate(zip(versions, datasets)):
            ax.plot(data['time'], data['wet_tubes_percent'], 
                   label=version, color=colors[i], linestyle=line_styles[i], linewidth=2)
        ax.set_xlabel('Time (years)', fontsize=12)
        ax.set_ylabel('Wet Tubes (%)', fontsize=12)
        ax.set_title('Wet Tubes Over Time', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Plot 3: Objects in Cache
        ax = axes[1, 0]
        for i, (version, data) in enumerate(zip(versions, datasets)):
            ax.plot(data['time'], data['objects_in_cache_percent'], 
                   label=version, color=colors[i], linestyle=line_styles[i], linewidth=2)
        ax.set_xlabel('Time (years)', fontsize=12)
        ax.set_ylabel('Objects in Cache (%)', fontsize=12)
        ax.set_title('Objects in Cache Over Time', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Plot 4: Expired Tubes
        ax = axes[1, 1]
        for i, (version, data) in enumerate(zip(versions, datasets)):
            # Dashed line for expired by time
            ax.plot(data['time'], data['tubes_expired_by_time_percent'], 
                   linestyle=':', alpha=0.6, color=colors[i], linewidth=1.5)
            # Solid line for total expired
            ax.plot(data['time'], data['total_expired_percent'], 
                   label=f'{version} (Total)', color=colors[i], linestyle=line_styles[i], linewidth=2)
        ax.set_xlabel('Time (years)', fontsize=12)
        ax.set_ylabel('Expired Tubes (%)', fontsize=12)
        ax.set_title('Expired Tubes Over Time\n(Dashed: By Time, Solid: Total)', 
                    fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add difference table
        fig.text(0.98, 0.5, 
                f'Final Lost Objects:\n'
                f'Original:     {original_data["lost_objects_percent"][-1]:.2f}%\n'
                f'Refactored:   {refactored_data["lost_objects_percent"][-1]:.2f}%\n'
                f'Difference:   {abs(original_data["lost_objects_percent"][-1] - refactored_data["lost_objects_percent"][-1]):.2f}%\n\n'
                f'Final Cache:\n'
                f'Original:     {original_data["objects_in_cache_percent"][-1]:.2f}%\n'
                f'Refactored:   {refactored_data["objects_in_cache_percent"][-1]:.2f}%\n'
                f'Difference:   {abs(original_data["objects_in_cache_percent"][-1] - refactored_data["objects_in_cache_percent"][-1]):.2f}%',
                ha='left', va='center', fontsize=10, family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout(rect=[0, 0, 0.96, 0.96])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'{policy_folder}_comparison_{key}_{timestamp}.png'
        output_path = os.path.join(policy_output_dir, output_filename)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"    ✓ Saved: {output_path}")
        print(f"    Original Lost Objects:   {original_data['lost_objects_percent'][-1]:.2f}%")
        print(f"    Refactored Lost Objects: {refactored_data['lost_objects_percent'][-1]:.2f}%")
        diff = abs(original_data['lost_objects_percent'][-1] - refactored_data['lost_objects_percent'][-1])
        if diff < 0.01:
            print(f"    ✅ IDENTICAL! (diff: {diff:.4f}%)")
        elif diff < 0.1:
            print(f"    ✓ Very close (diff: {diff:.4f}%)")
        else:
            print(f"    ⚠️  DIFFERENCE DETECTED! (diff: {diff:.2f}%)")

def main():
    """Main comparison function."""
    print("="*80)
    print("GROUP READ 20: ORIGINAL vs REFACTORED COMPARISON")
    print("="*80)
    
    base_dir = 'input/snaps/new_snaps_group_reads'
    original_folder = os.path.join(base_dir, '20_group_read')
    refactored_folder = os.path.join(base_dir, '20_group_refactored')
    output_dir = 'output/refactored_comparison'
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Define policies
    policies = {
        'Clustered Random': 'clustered_random',
        'SHA': 'sha',
        'Copysets': 'copysets',
        'Tube Replication': 'tube_replication'
    }
    
    for policy_name, policy_folder in policies.items():
        compare_versions_for_policy(policy_name, policy_folder, 
                                    original_folder, refactored_folder, output_dir)
    
    print("\n" + "="*80)
    print(f"Comparison complete! Check {output_dir}/ folder")
    print("="*80)

if __name__ == '__main__':
    main()
