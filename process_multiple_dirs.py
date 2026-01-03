#!/usr/bin/env python3
"""
Process multiple snapshot directories to create both loss/exhausted and storage metrics visualizations.
"""

import subprocess
import sys
import os

def run_visualization(script_name, input_dir, output_dir):
    """Run a visualization script with modified paths."""
    
    # Read the script content
    with open(script_name, 'r') as f:
        script_content = f.read()
    
    # Replace the input and output directories
    script_content = script_content.replace(
        "input_dir = '/Users/stephanie.schustermann/tesis/python_projects/input/snaps/clustered_random_pairwise'",
        f"input_dir = '{input_dir}'"
    )
    
    # Handle different output directory patterns
    if 'snapshot_metrics' in script_name:
        script_content = script_content.replace(
            "output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_metrics/clustered_random_pairwise'",
            f"output_dir = '{output_dir}'"
        )
    else:
        script_content = script_content.replace(
            "output_dir = '/Users/stephanie.schustermann/tesis/python_projects/output/snapshot_storage_metrics/clustered_random_pairwise'",
            f"output_dir = '{output_dir}'"
        )
    
    # Execute the modified script
    exec(script_content, {'__name__': '__main__'})

def main():
    base_input = '/Users/stephanie.schustermann/tesis/python_projects/input/snaps'
    base_output = '/Users/stephanie.schustermann/tesis/python_projects/output'
    
    # Directories to process
    directories = [
        'pairwise_random',
        'pairwise_copysets'
    ]
    
    for dir_name in directories:
        input_dir = os.path.join(base_input, dir_name)
        
        if not os.path.exists(input_dir):
            print(f"⚠ Warning: Directory not found: {input_dir}")
            continue
        
        print("=" * 80)
        print(f"PROCESSING: {dir_name}")
        print("=" * 80)
        
        # Process loss/exhausted metrics
        print(f"\n📊 Generating Loss & Exhausted Tubes Metrics for {dir_name}...")
        output_metrics = os.path.join(base_output, 'snapshot_metrics', dir_name)
        run_visualization('batch_visualize_snapshots.py', input_dir, output_metrics)
        
        # Process storage metrics
        print(f"\n📊 Generating Storage Metrics for {dir_name}...")
        output_storage = os.path.join(base_output, 'snapshot_storage_metrics', dir_name)
        run_visualization('batch_visualize_storage_metrics.py', input_dir, output_storage)
        
        print(f"\n✅ Completed processing for {dir_name}\n")

if __name__ == "__main__":
    main()




