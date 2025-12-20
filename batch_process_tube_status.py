#!/usr/bin/env python3
"""
Batch process all simulation log files to generate tube status tracking graphs.
"""

import os
import glob
import subprocess
import sys

def find_matching_pairs(input_dir):
    """
    Find all matching log and snaps file pairs.
    """
    pairs = []
    
    # Find all log files
    log_files = glob.glob(os.path.join(input_dir, "log_*.txt"))
    
    for log_file in sorted(log_files):
        # Derive the corresponding snaps file name
        basename = os.path.basename(log_file)
        snaps_name = basename.replace("log_", "snaps_")
        snaps_file = os.path.join(input_dir, snaps_name)
        
        # Check if snaps file exists
        if os.path.exists(snaps_file):
            pairs.append((log_file, snaps_file))
        else:
            print(f"Warning: No matching snaps file for {basename}")
    
    return pairs

def generate_output_name(log_file, output_dir):
    """
    Generate output filename based on log filename.
    """
    basename = os.path.basename(log_file)
    # Remove "log_" prefix and ".txt" suffix, add "_status.png"
    name = basename.replace("log_", "").replace(".txt", "_status.png")
    return os.path.join(output_dir, name)

def main():
    input_dir = "input"
    output_dir = "output"
    script = "track_tube_status.py"
    
    # Find all matching pairs
    pairs = find_matching_pairs(input_dir)
    
    print(f"Found {len(pairs)} matching log/snaps file pairs")
    print("="*70)
    
    # Process each pair
    success_count = 0
    error_count = 0
    
    for i, (log_file, snaps_file) in enumerate(pairs, 1):
        log_basename = os.path.basename(log_file)
        output_file = generate_output_name(log_file, output_dir)
        
        print(f"\n[{i}/{len(pairs)}] Processing: {log_basename}")
        print(f"  Output: {os.path.basename(output_file)}")
        
        try:
            # Run the tracking script
            result = subprocess.run(
                ["python3", script, log_file, snaps_file, output_file],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per file
            )
            
            if result.returncode == 0:
                print(f"  ✓ Success")
                success_count += 1
            else:
                print(f"  ✗ Failed with return code {result.returncode}")
                print(f"  Error: {result.stderr[:200]}")
                error_count += 1
        
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout (exceeded 10 minutes)")
            error_count += 1
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            error_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"Total files: {len(pairs)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    print("="*70)

if __name__ == "__main__":
    main()
