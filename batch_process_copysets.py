#!/usr/bin/env python3
"""
Batch process simulation log files with copysets tracking data.
These files are in the with_copysets_track subdirectory.
"""

import os
import glob
import subprocess
import sys

def find_matching_pairs(logs_dir, snaps_dir):
    """
    Find all matching log and snaps file pairs.
    Files should have the same name in both directories.
    """
    pairs = []
    
    # Find all log files
    log_files = glob.glob(os.path.join(logs_dir, "*.txt"))
    
    for log_file in sorted(log_files):
        # Get the basename to find matching snaps file
        basename = os.path.basename(log_file)
        snaps_file = os.path.join(snaps_dir, basename)
        
        # Check if snaps file exists
        if os.path.exists(snaps_file):
            pairs.append((log_file, snaps_file))
        else:
            print(f"Warning: No matching snaps file for {basename}")
    
    return pairs

def generate_output_name(log_file, output_dir):
    """
    Generate output filename based on log filename.
    Example: maxReads_100_accessRate_100_dist_Uniform_20251220_204320.txt
             -> maxReads_100_accessRate_100_dist_Uniform_20251220_204320_copysets_status.png
    """
    basename = os.path.basename(log_file)
    # Remove ".txt" suffix, add "_copysets_status.png"
    name = basename.replace(".txt", "_copysets_status.png")
    return os.path.join(output_dir, name)

def main():
    # Use subdirectories under input/
    logs_dir = "input/logs/with_copysets_track"
    snaps_dir = "input/snaps/with_copysets_track"
    output_dir = "output"
    script = "track_tube_status_with_copysets.py"
    
    # Verify directories exist
    if not os.path.exists(logs_dir):
        print(f"Error: Logs directory not found: {logs_dir}")
        sys.exit(1)
    
    if not os.path.exists(snaps_dir):
        print(f"Error: Snaps directory not found: {snaps_dir}")
        sys.exit(1)
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all matching pairs
    pairs = find_matching_pairs(logs_dir, snaps_dir)
    
    print(f"Found {len(pairs)} matching log/snaps file pairs with copysets tracking")
    print("="*70)
    
    if len(pairs) == 0:
        print("No matching pairs found. Exiting.")
        sys.exit(0)
    
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




