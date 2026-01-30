#!/usr/bin/env python3
"""
Analyze and visualize the percentage of lost objects over a 10-year period
from the new snapshot format.
"""

import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime


def parse_new_snapshot_file(filepath):
    """
    Parse the new snapshot file format and calculate loss percentage over time.
    
    Columns:
    0: timestamp (in years)
    10: objects_lost_since_last_snap
    12: total objects in the system
    """
    
    times = []
    cumulative_lost = []
    total_objects_in_system = []
    initial_objects = None
    running_lost_count = 0
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Skip header line
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(',')
            if len(parts) < 13:
                continue
            
            try:
                timestamp = float(parts[0])
                objects_lost = int(parts[10])
                total_objects = int(parts[12])
                
                # Set initial object count from first data point
                if initial_objects is None and total_objects > 0:
                    initial_objects = total_objects
                
                # Accumulate lost objects
                running_lost_count += objects_lost
                
                times.append(timestamp)
                cumulative_lost.append(running_lost_count)
                total_objects_in_system.append(total_objects)
                
            except (ValueError, IndexError) as e:
                continue
    
    # Calculate loss percentage
    loss_percentages = []
    if initial_objects and initial_objects > 0:
        for lost in cumulative_lost:
            loss_pct = (lost / initial_objects) * 100
            loss_percentages.append(loss_pct)
    
    return times, cumulative_lost, loss_percentages, total_objects_in_system, initial_objects


def plot_loss_analysis(times, cumulative_lost, loss_percentages, total_objects, 
                       initial_objects, filename):
    """Create comprehensive plots showing object loss over time."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    snapshot_name = os.path.basename(filename).replace('.txt', '')
    fig.suptitle(f'Object Loss Analysis Over 10 Years\n{snapshot_name}', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Loss Percentage Over Time
    ax1.plot(times, loss_percentages, color='tab:red', linewidth=2, alpha=0.8)
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Lost Objects (%)', fontsize=12)
    ax1.set_title('Percentage of Objects Lost Over Time', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max(times) if times else 10)
    if loss_percentages:
        ax1.set_ylim(0, max(loss_percentages) * 1.05)
    
    # Add final percentage annotation
    if times and loss_percentages:
        final_loss = loss_percentages[-1]
        ax1.annotate(f'Final: {final_loss:.2f}%', 
                    xy=(times[-1], final_loss),
                    xytext=(times[-1] * 0.7, final_loss * 0.9),
                    fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3'))
    
    # Plot 2: Cumulative Lost Objects (absolute count)
    ax2.plot(times, cumulative_lost, color='tab:orange', linewidth=2, alpha=0.8)
    ax2.set_xlabel('Time (years)', fontsize=12)
    ax2.set_ylabel('Cumulative Lost Objects (count)', fontsize=12)
    ax2.set_title('Cumulative Number of Lost Objects', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max(times) if times else 10)
    if cumulative_lost:
        ax2.ticklabel_format(style='plain', axis='y')
    
    # Plot 3: Total Objects Remaining in System
    ax3.plot(times, total_objects, color='tab:green', linewidth=2, alpha=0.8)
    ax3.set_xlabel('Time (years)', fontsize=12)
    ax3.set_ylabel('Total Objects in System', fontsize=12)
    ax3.set_title('Total Objects Remaining in System', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max(times) if times else 10)
    ax3.ticklabel_format(style='plain', axis='y')
    
    # Add horizontal line at initial count
    if initial_objects:
        ax3.axhline(y=initial_objects, color='gray', linestyle='--', 
                   linewidth=1, alpha=0.5, label=f'Initial: {initial_objects:,}')
        ax3.legend(loc='upper right')
    
    # Plot 4: Summary Statistics
    ax4.axis('off')
    
    if times and loss_percentages and cumulative_lost and total_objects:
        final_time = times[-1]
        final_loss_pct = loss_percentages[-1]
        final_lost_count = cumulative_lost[-1]
        final_remaining = total_objects[-1]
        
        # Calculate loss rate
        if final_time > 0:
            avg_loss_rate_per_year = final_lost_count / final_time
        else:
            avg_loss_rate_per_year = 0
        
        summary_text = f"""
        SUMMARY STATISTICS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        Initial Objects:        {initial_objects:>15,}
        
        After {final_time:.1f} years:
        
        Total Lost:             {final_lost_count:>15,}
        Loss Percentage:        {final_loss_pct:>14.2f}%
        
        Objects Remaining:      {final_remaining:>15,}
        Remaining Percentage:   {100 - final_loss_pct:>14.2f}%
        
        Average Loss Rate:      {avg_loss_rate_per_year:>15,.0f} objects/year
        
        Data Points:            {len(times):>15,}
        Time Range:             {times[0]:.2f} - {final_time:.2f} years
        """
        
        ax4.text(0.1, 0.5, summary_text, fontsize=12, family='monospace',
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save the figure
    output_dir = '/Users/stephanie/Documents/thesis/python_projects/output/object_loss_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'loss_analysis_{snapshot_name}_{timestamp}.png'
    output_path = os.path.join(output_dir, output_filename)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Plot saved to: {output_path}")
    
    return output_path


def print_summary(times, cumulative_lost, loss_percentages, total_objects, initial_objects):
    """Print summary statistics to console."""
    
    if not times or not loss_percentages:
        print("No data to summarize")
        return
    
    print("\n" + "="*60)
    print("OBJECT LOSS ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\nInitial Objects:           {initial_objects:,}")
    print(f"Time Period:               {times[0]:.2f} - {times[-1]:.2f} years")
    print(f"Number of Snapshots:       {len(times):,}")
    
    print(f"\n{'Time (years)':<15} {'Lost Objects':<20} {'Loss %':<15} {'Remaining':<20}")
    print("-" * 70)
    
    # Print summary at key intervals
    intervals = [0, 1, 2, 5, 7.5, 10]
    for target_time in intervals:
        # Find closest time point
        closest_idx = min(range(len(times)), key=lambda i: abs(times[i] - target_time))
        if abs(times[closest_idx] - target_time) <= 0.5:  # Within 0.5 years
            t = times[closest_idx]
            lost = cumulative_lost[closest_idx]
            pct = loss_percentages[closest_idx]
            remaining = total_objects[closest_idx]
            print(f"{t:<15.2f} {lost:<20,} {pct:<15.4f} {remaining:<20,}")
    
    # Always print the final values
    print("-" * 70)
    final_time = times[-1]
    final_lost = cumulative_lost[-1]
    final_pct = loss_percentages[-1]
    final_remaining = total_objects[-1]
    print(f"{final_time:<15.2f} {final_lost:<20,} {final_pct:<15.4f} {final_remaining:<20,}")
    
    # Calculate average loss rate
    if final_time > 0:
        avg_rate = final_lost / final_time
        print(f"\nAverage Loss Rate:         {avg_rate:,.0f} objects/year")
    
    print("="*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_object_loss_percentage.py <snapshot_file>")
        print("\nExample:")
        print("  python analyze_object_loss_percentage.py input/snaps/snaps_output_2_20260112_181304.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"Reading snapshot file: {filepath}")
    
    times, cumulative_lost, loss_percentages, total_objects, initial_objects = \
        parse_new_snapshot_file(filepath)
    
    if not times:
        print("Error: No valid data found in file")
        sys.exit(1)
    
    print(f"✓ Successfully parsed {len(times)} data points")
    
    # Print summary statistics
    print_summary(times, cumulative_lost, loss_percentages, total_objects, initial_objects)
    
    # Create visualization
    print("Creating visualization...")
    output_path = plot_loss_analysis(times, cumulative_lost, loss_percentages, 
                                     total_objects, initial_objects, filepath)
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
