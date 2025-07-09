#!/usr/bin/env python3
"""
SanctSim Sweep Monitor
Provides real-time monitoring and management of parameter sweep progress.
"""

import json
import os
import time
import sys
from datetime import datetime, timedelta
import glob
import psutil
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Optional

class SweepMonitor:
    def __init__(self, results_dir: str = None):
        if results_dir:
            self.results_dir = results_dir
        else:
            # Find the most recent sweep results directory, including nested ones but excluding sweep_with_overriding_bug
            sweep_dirs = glob.glob("sweep_results_*") + glob.glob("sweep/sweep_results_*")
            if not sweep_dirs:
                print("No sweep results directories found")
                sys.exit(1)
            # Sort by modification time to get the most recent
            sweep_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            self.results_dir = sweep_dirs[0]
            
        self.progress_file = f"{self.results_dir}/progress.json"
        self.log_file = f"{self.results_dir}/sweep_log.txt"
        
    def load_progress(self) -> Dict:
        """Load current progress from file."""
        if not os.path.exists(self.progress_file):
            return {}
            
        with open(self.progress_file, 'r') as f:
            return json.load(f)
            
    def get_running_processes(self) -> List[Dict]:
        """Get list of running SanctSim processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if 'python' in proc.info['name'].lower() and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'main.py' in cmdline and ('--alpha' in cmdline or '--num-agents' in cmdline):
                        processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline,
                            'start_time': datetime.fromtimestamp(proc.info['create_time']),
                            'duration': datetime.now() - datetime.fromtimestamp(proc.info['create_time'])
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return processes
        
    def display_status(self):
        """Display current sweep status."""
        progress = self.load_progress()
        
        if not progress:
            print(f"No progress data found in {self.results_dir}")
            return
            
        print("="*80)
        print("SANCTSIM SWEEP STATUS")
        print("="*80)
        print(f"Results Directory: {self.results_dir}")
        print(f"Last Updated: {progress.get('timestamp', 'Unknown')}")
        print()
        
        # Overall progress
        total = progress.get('total_runs', 0)
        completed = progress.get('completed', 0) 
        failed = progress.get('failed', 0)
        active = progress.get('active', 0)
        
        if total > 0:
            completion_rate = (completed + failed) / total * 100
            success_rate = completed / (completed + failed) * 100 if (completed + failed) > 0 else 0
            
            print(f"Overall Progress: {completed + failed}/{total} ({completion_rate:.1f}%)")
            print(f"✓ Successful: {completed}")
            print(f"✗ Failed: {failed}")
            print(f"🔄 Active: {active}")
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Running processes
        running_procs = self.get_running_processes()
        print(f"\nRunning Processes: {len(running_procs)}")
        
        for proc in running_procs:
            # Extract key info from command line
            cmd = proc['cmdline']
            model = "unknown"
            agents = "unknown"
            alpha = "unknown"
            
            parts = cmd.split()
            for i, part in enumerate(parts):
                if part == '--model-name' and i + 1 < len(parts):
                    model = parts[i + 1].split('/')[-1]
                elif part == '--num-agents' and i + 1 < len(parts):
                    agents = parts[i + 1]
                elif part == '--alpha' and i + 1 < len(parts):
                    alpha = parts[i + 1]
                    
            duration = proc['duration']
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            
            print(f"  PID {proc['pid']}: {model} | {agents} agents | α={alpha} | {hours:.0f}h{minutes:.0f}m")
            
    def monitor_live(self, interval: int = 30):
        """Monitor sweep progress in real-time."""
        print(f"Monitoring sweep progress (updating every {interval}s, Ctrl+C to stop)")
        print()
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                self.display_status()
                print(f"\nNext update in {interval} seconds...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            
    def generate_report(self, save_plots: bool = True) -> Dict:
        """Generate comprehensive sweep report."""
        progress = self.load_progress()
        
        if not progress:
            print("No progress data found")
            return {}
            
        completed_runs = progress.get('completed_runs', [])
        failed_runs = progress.get('failed_runs', [])
        
        # Convert to DataFrame for analysis
        if completed_runs:
            df_completed = pd.DataFrame([run['config'] for run in completed_runs])
            df_completed['status'] = 'completed'
            df_completed['duration'] = [run.get('duration', 0) for run in completed_runs]
        else:
            df_completed = pd.DataFrame()
            
        if failed_runs:
            df_failed = pd.DataFrame([run['config'] for run in failed_runs])
            df_failed['status'] = 'failed'
            df_failed['duration'] = [run.get('duration', 0) for run in failed_runs]
        else:
            df_failed = pd.DataFrame()
            
        # Combine data
        if not df_completed.empty and not df_failed.empty:
            df_all = pd.concat([df_completed, df_failed], ignore_index=True)
        elif not df_completed.empty:
            df_all = df_completed
        elif not df_failed.empty:
            df_all = df_failed
        else:
            print("No run data to analyze")
            return {}
            
        # Generate report
        report = {
            'total_runs': len(df_all),
            'completed': len(df_completed),
            'failed': len(df_failed),
            'success_rate': len(df_completed) / len(df_all) * 100,
            'avg_duration': df_all['duration'].mean() / 60,  # in minutes
        }
        
        if save_plots and not df_all.empty:
            self.create_visualizations(df_all, completed_runs)
            
        return report
        
    def create_visualizations(self, df_all: pd.DataFrame, completed_runs: List[Dict]):
        """Create visualization plots for the sweep results."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Success rate by model
        if 'model_name' in df_all.columns:
            success_by_model = df_all.groupby('model_name')['status'].apply(
                lambda x: (x == 'completed').sum() / len(x) * 100
            ).sort_values(ascending=False)
            
            axes[0, 0].bar(range(len(success_by_model)), success_by_model.values)
            axes[0, 0].set_xticks(range(len(success_by_model)))
            axes[0, 0].set_xticklabels(success_by_model.index, rotation=45, ha='right')
            axes[0, 0].set_ylabel('Success Rate (%)')
            axes[0, 0].set_title('Success Rate by Model')
            axes[0, 0].grid(True, alpha=0.3)
            
        # Plot 2: Success rate by agent count
        if 'num_agents' in df_all.columns:
            success_by_agents = df_all.groupby('num_agents')['status'].apply(
                lambda x: (x == 'completed').sum() / len(x) * 100
            ).sort_index()
            
            axes[0, 1].bar(success_by_agents.index, success_by_agents.values)
            axes[0, 1].set_xlabel('Number of Agents')
            axes[0, 1].set_ylabel('Success Rate (%)')
            axes[0, 1].set_title('Success Rate by Agent Count')
            axes[0, 1].grid(True, alpha=0.3)
            
        # Plot 3: Success rate by alpha
        if 'alpha' in df_all.columns:
            success_by_alpha = df_all.groupby('alpha')['status'].apply(
                lambda x: (x == 'completed').sum() / len(x) * 100
            ).sort_index()
            
            axes[1, 0].bar(success_by_alpha.index, success_by_alpha.values)
            axes[1, 0].set_xlabel('Alpha Value')
            axes[1, 0].set_ylabel('Success Rate (%)')
            axes[1, 0].set_title('Success Rate by Alpha Value')
            axes[1, 0].grid(True, alpha=0.3)
            
        # Plot 4: Runtime distribution
        if 'duration' in df_all.columns and len(df_all) > 0:
            duration_minutes = df_all['duration'] / 60
            axes[1, 1].hist(duration_minutes, bins=20, edgecolor='black', alpha=0.7)
            axes[1, 1].set_xlabel('Duration (minutes)')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].set_title('Runtime Distribution')
            axes[1, 1].grid(True, alpha=0.3)
            
        plt.tight_layout()
        
        # Save plot
        plot_file = f"{self.results_dir}/sweep_analysis.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"Analysis plots saved to: {plot_file}")
        plt.show()
        
    def kill_running_processes(self):
        """Kill all running SanctSim processes."""
        processes = self.get_running_processes()
        
        if not processes:
            print("No running SanctSim processes found")
            return
            
        print(f"Found {len(processes)} running processes:")
        for proc in processes:
            print(f"  PID {proc['pid']}: {proc['cmdline']}")
            
        response = input(f"\nKill all {len(processes)} processes? (y/n): ")
        if response.lower() == 'y':
            killed = 0
            for proc in processes:
                try:
                    psutil.Process(proc['pid']).terminate()
                    killed += 1
                    print(f"Killed PID {proc['pid']}")
                except psutil.NoSuchProcess:
                    print(f"PID {proc['pid']} already terminated")
                except Exception as e:
                    print(f"Error killing PID {proc['pid']}: {e}")
                    
            print(f"Terminated {killed} processes")
        else:
            print("Operation cancelled")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor SanctSim parameter sweeps")
    parser.add_argument('--results-dir', help='Sweep results directory')
    parser.add_argument('--live', action='store_true', help='Live monitoring mode')
    parser.add_argument('--interval', type=int, default=30, help='Update interval for live mode (seconds)')
    parser.add_argument('--report', action='store_true', help='Generate analysis report')
    parser.add_argument('--kill', action='store_true', help='Kill all running processes')
    parser.add_argument('--list-sweeps', action='store_true', help='List available sweep directories')
    
    args = parser.parse_args()
    
    # List sweep directories
    if args.list_sweeps:
        sweep_dirs = glob.glob("sweep_results_*") + glob.glob("sweep/sweep_results_*")
        if sweep_dirs:
            print("Available sweep directories:")
            sweep_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            for d in sweep_dirs:
                mtime = datetime.fromtimestamp(os.path.getmtime(d))
                print(f"  {d} (modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("No sweep directories found")
        return
        
    # Create monitor
    monitor = SweepMonitor(args.results_dir)
    
    if args.kill:
        monitor.kill_running_processes()
    elif args.live:
        monitor.monitor_live(args.interval)
    elif args.report:
        report = monitor.generate_report()
        print("\n=== SWEEP ANALYSIS REPORT ===")
        for key, value in report.items():
            print(f"{key}: {value}")
    else:
        monitor.display_status()

if __name__ == "__main__":
    main()