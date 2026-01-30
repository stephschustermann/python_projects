#!/usr/bin/env python3
"""
Compare 4 different policies across the same parameters:
- Clustered Random
- Random with SHA
- Copysets (Triplets)
- Tube Replication

For each matching filename, create a 4-subplot comparison showing all policies.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime
from collections import defaultdict

# Policy folder mappings
POLICY_FOLDERS = {
    'Clustered Random': 'input/snaps/new_snaps_clustered_random_small',
    'SHA': 'input/snaps/new_snaps_sha',
    'Copysets': 'input/snaps/new_snaps_triplets_copysets',
    'Tube Replication': 'input/snaps/new_snaps_tube_replication'
}

# Colors for each policy
POLICY_COLORS = {
    'Clustered Random': '#1f77b4',  # blue
    'SHA': '#ff7f0e',               # orange
    'Copysets': '#2ca02c',          # green
    'Tube Replication': '#d62728'   # red
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
    # Example: maxReads_100_accessRate_500_dist_Uniform_20260113_183910.txt
    # Returns: maxReads_100_accessRate_500_dist_Uniform
    
    parts = filename.replace('.txt', '').split('_')
    
    # Find where the timestamp starts (typically 8 digits followed by 6 digits)
    param_parts = []
    for i, part in enumerate(parts):
        if len(part) == 8 and part.isdigit():
            # This is the date part of timestamp
            break
        param_parts.append(part)
    
    return '_'.join(param_parts)

def find_matching_files():
    """Find files with matching parameter patterns across all policy folders."""
    
    file_groups = defaultdict(dict)
    
    for policy_name, folder_path in POLICY_FOLDERS.items():
        if not os.path.exists(folder_path):
            print(f"Warning: Folder not found: {folder_path}")
            continue
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        
        for filename in files:
            param_pattern = extract_param_pattern(filename)
            file_groups[param_pattern][policy_name] = os.path.join(folder_path, filename)
    
    # Filter to only files present in all 4 policies
    complete_groups = {pattern: policies for pattern, policies in file_groups.items() 
                       if len(policies) == 4}
    
    return complete_groups

def compare_policies(file_groups, output_dir='output/policy_comparisons'):
    """Create comparison visualizations for each file group."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nFound {len(file_groups)} matching parameter patterns")
    
    for param_pattern, policy_files in sorted(file_groups.items()):
        print(f"\nProcessing: {param_pattern}")
        
        # Parse all policy files
        policy_data = {}
        policy_metrics = {}
        
        for policy_name, filepath in policy_files.items():
            data = parse_snaps_file(filepath)
            if data:
                metrics = calculate_metrics(data)
                if metrics:
                    policy_data[policy_name] = data
                    policy_metrics[policy_name] = metrics
        
        if len(policy_data) < 4:
            print(f"  Skipping {param_pattern} - not all policies have valid data")
            continue
        
        # Create comparison plot
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Policy Comparison\n{param_pattern}', 
                     fontsize=16, fontweight='bold')
        
        # Plot 1: Lost Objects Percentage
        ax1 = axes[0, 0]
        for policy_name in ['Clustered Random', 'SHA', 'Copysets', 'Tube Replication']:
            if policy_name in policy_metrics:
                data = policy_data[policy_name]
                metrics = policy_metrics[policy_name]
                ax1.plot(data['timestamp'], metrics['lost_objects_percent'], 
                        linewidth=2, label=policy_name, color=POLICY_COLORS[policy_name])
        
        ax1.set_xlabel('Time (years)', fontsize=12)
        ax1.set_ylabel('Lost Objects (%)', fontsize=12)
        ax1.set_title('Lost Objects Over Time', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 10)
        
        # Plot 2: Wet Tubes Percentage
        ax2 = axes[0, 1]
        for policy_name in ['Clustered Random', 'SHA', 'Copysets', 'Tube Replication']:
            if policy_name in policy_data:
                data = policy_data[policy_name]
                ax2.plot(data['timestamp'], data['tubes_wetted_percent'], 
                        linewidth=2, label=policy_name, color=POLICY_COLORS[policy_name])
        
        ax2.set_xlabel('Time (years)', fontsize=12)
        ax2.set_ylabel('Wet Tubes (%)', fontsize=12)
        ax2.set_title('Wet Tubes Over Time', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 10)
        
        # Plot 3: Objects in Cache Percentage
        ax3 = axes[1, 0]
        for policy_name in ['Clustered Random', 'SHA', 'Copysets', 'Tube Replication']:
            if policy_name in policy_metrics:
                data = policy_data[policy_name]
                metrics = policy_metrics[policy_name]
                ax3.plot(data['timestamp'], metrics['objects_in_cache_percent'], 
                        linewidth=2, label=policy_name, color=POLICY_COLORS[policy_name])
        
        ax3.set_xlabel('Time (years)', fontsize=12)
        ax3.set_ylabel('Objects in Cache (%)', fontsize=12)
        ax3.set_title('Objects in Cache Over Time', fontsize=14, fontweight='bold')
        ax3.legend(loc='best', fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, 10)
        
        # Plot 4: Expired Tubes Percentage
        ax4 = axes[1, 1]
        
        # Plot expired by time (dashed) and total expired (solid) for each policy
        for policy_name in ['Clustered Random', 'SHA', 'Copysets', 'Tube Replication']:
            if policy_name in policy_data and policy_name in policy_metrics:
                data = policy_data[policy_name]
                metrics = policy_metrics[policy_name]
                
                # Expired by time (dashed)
                ax4.plot(data['timestamp'], data['tubes_expired_by_time_percent'], 
                        linewidth=1.5, color=POLICY_COLORS[policy_name],
                        linestyle='--', alpha=0.7)
                
                # Total expired (solid)
                ax4.plot(data['timestamp'], metrics['total_expired_percent'], 
                        linewidth=2, label=policy_name, color=POLICY_COLORS[policy_name])
        
        ax4.set_xlabel('Time (years)', fontsize=12)
        ax4.set_ylabel('Expired Tubes (%)', fontsize=12)
        ax4.set_title('Expired Tubes Over Time\n(Dashed: By Time, Solid: Total)', 
                     fontsize=14, fontweight='bold')
        ax4.legend(loc='best', fontsize=10)
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, 10)
        
        plt.tight_layout()
        
        # Save the figure
        output_filename = f'policy_comparison_{param_pattern}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Saved: {output_path}")
        
        # Print summary
        print(f"  Final Lost Objects:")
        for policy_name in ['Clustered Random', 'SHA', 'Copysets', 'Tube Replication']:
            if policy_name in policy_metrics:
                final_loss = policy_metrics[policy_name]['lost_objects_percent'][-1]
                print(f"    {policy_name:20s}: {final_loss:6.2f}%")

if __name__ == '__main__':
    print("="*80)
    print("POLICY COMPARISON ANALYSIS")
    print("="*80)
    
    # Find matching files
    file_groups = find_matching_files()
    
    if not file_groups:
        print("\nNo matching files found across all 4 policy folders!")
        print("\nExpected folders:")
        for policy, folder in POLICY_FOLDERS.items():
            print(f"  - {folder}")
    else:
        # Create comparisons
        compare_policies(file_groups)
        
        print("\n" + "="*80)
        print(f"Comparison complete! Check output/policy_comparisons/ folder")
        print("="*80)
