#!/usr/bin/env python3
"""
SanctSim Parameter Sweep Runner
Coordinates multiple Claude Code instances to run comprehensive parameter sweeps
across different models, agent counts, and alpha values.
"""

import subprocess
import time
import json
import os
import sys
import signal
import threading
from datetime import datetime
from typing import List, Dict, Tuple
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

# Configuration for the sweep
SWEEP_CONFIG = {
    'num_agents': [2, 5, 7, 10, 15, 20],
    'alpha_values': [0.5, 1, 1.6, 2, 4, 10],
    'models': {
        # OpenRouter models
        'claude-3.5-sonnet': {
            'provider': 'openrouter',
            'model_name': 'anthropic/claude-3.5-sonnet'
        },
        'claude-3.5-haiku': {
            'provider': 'openrouter', 
            'model_name': 'anthropic/claude-3.5-haiku'
        },
        'claude-4-opus': {
            'provider': 'openrouter',
            'model_name': 'anthropic/claude-4-opus-20250522'
        },
        'claude-4-sonnet': {
            'provider': 'openrouter',
            'model_name': 'anthropic/claude-4-sonnet-20250522'
        },
        'o1-mini': {
            'provider': 'openai',
            'model_name': 'o1-mini-2024-09-12'
        },
        'o3': {
            'provider': 'openai',
            'model_name': 'o3-2025-04-16',
        },
        'o3-mini-low': {
            'provider': 'openai',
            'model_name': 'o3-mini-2025-01-31',
            'reasoning_effort': 'low'
        },
        'o3-mini-med': {
            'provider': 'openai',
            'model_name': 'o3-mini-2025-01-31',
            'reasoning_effort': 'medium'
        },
        'o3-mini-high': {
            'provider': 'openai',
            'model_name': 'o3-mini-2025-01-31',
            'reasoning_effort': 'high'
        },
        'o4-mini-low': {
            'provider': 'openai',
            'model_name': 'o4-mini-2025-04-16',
            'reasoning_effort': 'low'
        },
        'o4-mini-med': {
            'provider': 'openai',
            'model_name': 'o4-mini-2025-04-16',
            'reasoning_effort': 'medium'
        },
        'o4-mini-high': {
            'provider': 'openai',
            'model_name': 'o4-mini-2025-04-16',
            'reasoning_effort': 'high'
        },
        'llama': {
            'provider': 'openrouter',
            'model_name': 'meta-llama/llama-3.1-8b-instruct'
        },
        'qwen': {
            'provider': 'openrouter',
            'model_name': 'qwen/qwen-2.5-vl-7b-instruct'
        }
    },
    'num_rounds': 15,  # Default number of rounds
    'max_parallel_jobs': 12,  # Max number of simultaneous simulations (optimized for 8-core system)
    'timeout_minutes': 600,  # Timeout per simulation (10 hours)
    'retry_attempts': 2,  # Retry failed runs
}

class SweepRunner:
    def __init__(self, config: Dict):
        self.config = config
        self.results_dir = f"sweep/sweep_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.log_file = f"{self.results_dir}/sweep_log.txt"
        self.progress_file = f"{self.results_dir}/progress.json"
        self.active_processes = {}
        self.completed_runs = []
        self.failed_runs = []
        self.total_runs = 0
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories for the sweep."""
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(f"{self.results_dir}/logs", exist_ok=True)
        os.makedirs(f"{self.results_dir}/results", exist_ok=True)
        
    def log(self, message: str):
        """Log message to file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
            
    def save_progress(self):
        """Save current progress to file."""
        progress = {
            'total_runs': self.total_runs,
            'completed': len(self.completed_runs),
            'failed': len(self.failed_runs),
            'active': len(self.active_processes),
            'completed_runs': self.completed_runs,
            'failed_runs': self.failed_runs,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
            
    def generate_run_configs(self) -> List[Dict]:
        """Generate all possible run configurations."""
        configs = []
        
        for num_agents, alpha, (model_name, model_config) in itertools.product(
            self.config['num_agents'],
            self.config['alpha_values'], 
            self.config['models'].items()
        ):
            run_config = {
                'num_agents': num_agents,
                'alpha': alpha,
                'model_name': model_name,
                'model_config': model_config,
                'num_rounds': self.config['num_rounds'],
                'run_id': f"{model_name}_{num_agents}agents_alpha{alpha}"
            }
            configs.append(run_config)
            
        return configs
        
    def build_command(self, run_config: Dict) -> List[str]:
        """Build the command to run a single simulation."""
        model_config = run_config['model_config']
        
        cmd = [
            'python', 'code/main.py',
            '--api-provider', model_config['provider'],
            '--model-name', model_config['model_name'],
            '--num-agents', str(run_config['num_agents']),
            '--num-rounds', str(run_config['num_rounds']),
            '--alpha', str(run_config['alpha'])
        ]
        
        # Add reasoning effort for OpenAI models if specified
        if 'reasoning_effort' in model_config:
            cmd.extend(['--reasoning-effort', model_config['reasoning_effort']])
            
        return cmd
        
    def run_single_simulation(self, run_config: Dict) -> Dict:
        """Run a single simulation."""
        run_id = run_config['run_id']
        self.log(f"Starting run: {run_id}")
        
        try:
            # Build command
            cmd = self.build_command(run_config)
            
            # Create log files for this run
            stdout_log = f"{self.results_dir}/logs/{run_id}_stdout.log"
            stderr_log = f"{self.results_dir}/logs/{run_id}_stderr.log"
            
            # Start the process
            with open(stdout_log, 'w') as stdout_file, open(stderr_log, 'w') as stderr_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True,
                    cwd=os.getcwd()
                )
                
                # Store process info
                self.active_processes[run_id] = {
                    'process': process,
                    'start_time': time.time(),
                    'config': run_config
                }
                
                # Wait for completion with timeout
                timeout_seconds = self.config['timeout_minutes'] * 60
                try:
                    return_code = process.wait(timeout=timeout_seconds)
                    
                    if return_code == 0:
                        self.log(f"✓ Completed run: {run_id}")
                        
                        # Check if result file was created
                        expected_file = self.find_result_file(run_config)
                        if expected_file:
                            # If file is in root directory, move it to sweep results directory
                            if not expected_file.startswith(self.results_dir):
                                result_dest = f"{self.results_dir}/results/{os.path.basename(expected_file)}"
                                if os.path.exists(expected_file):
                                    os.rename(expected_file, result_dest)
                                    self.log(f"  → Result moved to: {result_dest}")
                            else:
                                self.log(f"  → Result saved to: {expected_file}")
                        
                        result = {
                            'status': 'success',
                            'run_id': run_id,
                            'config': run_config,
                            'return_code': return_code,
                            'duration': time.time() - self.active_processes[run_id]['start_time']
                        }
                    else:
                        self.log(f"✗ Failed run: {run_id} (return code: {return_code})")
                        result = {
                            'status': 'failed',
                            'run_id': run_id,
                            'config': run_config,
                            'return_code': return_code,
                            'error': f"Process exited with code {return_code}",
                            'duration': time.time() - self.active_processes[run_id]['start_time']
                        }
                        
                except subprocess.TimeoutExpired:
                    self.log(f"⏰ Timeout run: {run_id} (after {self.config['timeout_minutes']} minutes)")
                    process.kill()
                    result = {
                        'status': 'timeout',
                        'run_id': run_id,
                        'config': run_config,
                        'error': f"Timeout after {self.config['timeout_minutes']} minutes",
                        'duration': timeout_seconds
                    }
                    
        except Exception as e:
            self.log(f"✗ Error in run: {run_id} - {str(e)}")
            result = {
                'status': 'error',
                'run_id': run_id,
                'config': run_config,
                'error': str(e),
                'duration': 0
            }
            
        finally:
            # Clean up process tracking
            if run_id in self.active_processes:
                del self.active_processes[run_id]
                
        return result
        
    def find_result_file(self, run_config: Dict) -> str:
        """Find the expected result file for a run."""
        model_name = run_config['model_config']['model_name'].replace('/', '_')
        num_agents = run_config['num_agents']
        num_rounds = run_config['num_rounds']
        alpha = run_config['alpha']
        
        # Build filename with reasoning effort if present
        base_filename = f"simulation_results_{model_name}_{num_agents}agents_{num_rounds}rounds_alpha{alpha}"
        
        # Add reasoning effort if specified
        if 'reasoning_effort' in run_config['model_config']:
            base_filename += f"_reasoning{run_config['model_config']['reasoning_effort']}"
            
        expected_filename = f"{base_filename}.json"
        
        # Since main.py now saves to sweep directories, we need to check there
        # Look for the file in the current sweep results directory first
        sweep_results_path = os.path.join(self.results_dir, "results", expected_filename)
        
        # Also check the root directory for backwards compatibility
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_path = os.path.join(base_dir, expected_filename)
        
        # Retry logic with small delays for file detection
        import time
        for attempt in range(5):  # Try up to 5 times
            # Check sweep results directory first
            if os.path.exists(sweep_results_path):
                return sweep_results_path
            # Check root directory as fallback
            if os.path.exists(root_path):
                return root_path
            time.sleep(0.2)  # Wait 200ms between attempts
        
        return None
        
    def estimate_total_time(self, run_configs: List[Dict]) -> str:
        """Estimate total sweep time."""
        total_runs = len(run_configs)
        max_parallel = self.config['max_parallel_jobs']
        avg_time_per_run = 10 * 60  # 10 minutes average
        
        # Calculate time accounting for parallelization
        if total_runs <= max_parallel:
            total_time = avg_time_per_run
        else:
            # Time for parallel batches + remaining sequential
            parallel_batches = total_runs // max_parallel
            remaining = total_runs % max_parallel
            total_time = (parallel_batches * avg_time_per_run) + (avg_time_per_run if remaining > 0 else 0)
            
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        
        return f"{hours}h {minutes}m"
        
    def run_sweep(self, filter_models: List[str] = None, filter_agents: List[int] = None, 
                  filter_alphas: List[float] = None, dry_run: bool = False):
        """Run the complete parameter sweep."""
        
        # Generate all run configurations
        all_configs = self.generate_run_configs()
        
        # Apply filters if specified
        if filter_models:
            all_configs = [c for c in all_configs if c['model_name'] in filter_models]
        if filter_agents:
            all_configs = [c for c in all_configs if c['num_agents'] in filter_agents]
        if filter_alphas:
            all_configs = [c for c in all_configs if c['alpha'] in filter_alphas]
            
        self.total_runs = len(all_configs)
        
        # Print sweep overview
        self.log("="*80)
        self.log("SANCTSIM PARAMETER SWEEP")
        self.log("="*80)
        self.log(f"Total runs: {self.total_runs}")
        self.log(f"Models: {len(set(c['model_name'] for c in all_configs))}")
        self.log(f"Agent counts: {sorted(set(c['num_agents'] for c in all_configs))}")
        self.log(f"Alpha values: {sorted(set(c['alpha'] for c in all_configs))}")
        self.log(f"Max parallel jobs: {self.config['max_parallel_jobs']}")
        self.log(f"Estimated total time: {self.estimate_total_time(all_configs)}")
        self.log(f"Results directory: {self.results_dir}")
        
        if dry_run:
            self.log("\n=== DRY RUN - CONFIGURATIONS TO BE EXECUTED ===")
            for i, config in enumerate(all_configs[:10], 1):  # Show first 10
                self.log(f"{i:3d}. {config['run_id']}")
            if len(all_configs) > 10:
                self.log(f"     ... and {len(all_configs) - 10} more")
            return
            
        # Confirm before starting
        response = input(f"\nReady to start sweep with {self.total_runs} runs? (y/n): ")
        if response.lower() != 'y':
            self.log("Sweep cancelled by user")
            return
            
        # Run the sweep
        self.log(f"\nStarting sweep at {datetime.now()}")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.config['max_parallel_jobs']) as executor:
            # Submit all jobs
            future_to_config = {
                executor.submit(self.run_single_simulation, config): config 
                for config in all_configs
            }
            
            # Process completed jobs
            for future in as_completed(future_to_config):
                result = future.result()
                
                if result['status'] == 'success':
                    self.completed_runs.append(result)
                else:
                    self.failed_runs.append(result)
                    
                # Update progress
                self.save_progress()
                
                # Print progress
                completed = len(self.completed_runs)
                failed = len(self.failed_runs)
                total = completed + failed
                
                self.log(f"Progress: {total}/{self.total_runs} ({total/self.total_runs*100:.1f}%) - "
                        f"✓ {completed} ✗ {failed}")
                        
        # Final summary
        total_time = time.time() - start_time
        self.log("="*80)
        self.log("SWEEP COMPLETED")
        self.log("="*80)
        self.log(f"Total time: {total_time/3600:.1f} hours")
        self.log(f"Successful runs: {len(self.completed_runs)}")
        self.log(f"Failed runs: {len(self.failed_runs)}")
        self.log(f"Success rate: {len(self.completed_runs)/self.total_runs*100:.1f}%")
        self.log(f"Results saved to: {self.results_dir}")
        
        # Handle failed runs
        if self.failed_runs:
            self.log(f"\nFailed runs:")
            for run in self.failed_runs:
                self.log(f"  - {run['run_id']}: {run.get('error', 'Unknown error')}")
                
        self.save_progress()

def main():
    """Main function with command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run SanctSim parameter sweeps")
    parser.add_argument('--models', nargs='+', help='Filter specific models')
    parser.add_argument('--agents', nargs='+', type=int, help='Filter specific agent counts')
    parser.add_argument('--alphas', nargs='+', type=float, help='Filter specific alpha values')
    parser.add_argument('--num-rounds', type=int, help='Number of rounds per simulation (overrides default)')
    parser.add_argument('--max-parallel', type=int, default=12, help='Max parallel jobs')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout per run (minutes)')
    parser.add_argument('--dry-run', action='store_true', help='Show configurations without running')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    
    args = parser.parse_args()
    
    # List models if requested
    if args.list_models:
        print("Available models:")
        for model_name, config in SWEEP_CONFIG['models'].items():
            print(f"  {model_name}: {config['provider']}/{config['model_name']}")
        return
        
    # Update config with command line args
    config = SWEEP_CONFIG.copy()
    config['max_parallel_jobs'] = args.max_parallel
    config['timeout_minutes'] = args.timeout
    
    # Override num_rounds if specified
    if args.num_rounds:
        config['num_rounds'] = args.num_rounds
    
    # Create and run sweep
    runner = SweepRunner(config)
    
    try:
        runner.run_sweep(
            filter_models=args.models,
            filter_agents=args.agents,
            filter_alphas=args.alphas,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        runner.log("\nSweep interrupted by user")
        # Clean up any running processes
        for run_id, proc_info in runner.active_processes.items():
            proc_info['process'].terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()