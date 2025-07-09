#!/usr/bin/env python3
"""
Weights & Biases integration for SanctSim simulation results.
This script demonstrates how to log simulation results to W&B for tracking and visualization.
"""

import json
import pandas as pd
from typing import Dict, List
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    print("wandb not installed. Run: pip install wandb")

def load_simulation_results(filename: str) -> List[Dict]:
    """Load simulation results from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def find_sweep_results(sweep_dir: str = "sweep") -> List[str]:
    """Find all simulation result files in sweep directories."""
    import os
    import glob
    
    result_files = []
    
    # Pattern to match sweep result directories
    sweep_pattern = os.path.join(sweep_dir, "sweep_results_*/results/*.json")
    result_files.extend(glob.glob(sweep_pattern))
    
    # Also check root directory for individual result files
    root_pattern = "simulation_results_*.json"
    result_files.extend(glob.glob(root_pattern))
    
    return sorted(result_files)

def extract_simulation_config(data: List[Dict], filename: str = None) -> Dict:
    """Extract simulation configuration for W&B."""
    first_round = data[0]
    
    # Extract model name and alpha from filename if provided
    model_name = 'unknown_model'
    alpha = 1.6  # Default value
    
    if filename:
        import re
        # Extract model name between "simulation_results_" and "_Xagents"
        model_match = re.search(r'simulation_results_([^_]+(?:_[^_]+)*?)_\d+agents', filename)
        if model_match:
            model_name = model_match.group(1).replace('_', '/')
        
        # Extract alpha value from filename (stop at non-digit, non-period characters)
        alpha_match = re.search(r'alpha([0-9]+(?:\.[0-9]+)?)', filename)
        if alpha_match:
            alpha = float(alpha_match.group(1))
    
    config = {
        'num_rounds': len(data),
        'num_agents': len(first_round['agents']),
        'endowment_stage_1': 20,  # From parameters
        'endowment_stage_2': 20,
        'public_good_multiplier': alpha,  # Extracted from filename
        'alpha': alpha,  # Also store as separate field
        'model': model_name,  # Extracted from filename
        'experiment_type': 'public_goods_game'
    }
    return config

def log_to_wandb(data: List[Dict], filename: str = None, project_name: str = "sanctsim-experiments"):
    """Log simulation results to Weights & Biases."""
    if not WANDB_AVAILABLE:
        print("W&B not available. Install with: pip install wandb")
        return
    
    # Extract configuration
    config = extract_simulation_config(data, filename)
    
    # Create more descriptive run name
    model_short = config['model'].replace('anthropic/', '').replace('claude-', 'claude')
    run_name = f"{model_short}_{config['num_agents']}agents_{config['num_rounds']}rounds_alpha{config['alpha']}"
    
    # Initialize W&B run
    run = wandb.init(
        project=project_name,
        config=config,
        name=run_name
    )
    
    # Log round-by-round data
    for round_data in data:
        round_num = round_data['round_number']
        
        # Basic metrics
        metrics = {
            'round': round_num,
            'total_contribution': round_data['sfi_total_contribution'] + round_data['si_total_contribution'],
            'si_total_contribution': round_data['si_total_contribution'],
            'sfi_total_contribution': round_data['sfi_total_contribution'],
            'si_avg_contribution': round_data['si_avg_contribution'],
            'sfi_avg_contribution': round_data['sfi_avg_contribution'],
            'num_si_members': len(round_data['si_members']),
            'num_sfi_members': len(round_data['sfi_members'])
        }
        
        # Agent-specific metrics
        for agent_id, agent_data in round_data['agents'].items():
            prefix = f"agent_{agent_id}"
            metrics.update({
                f"{prefix}_contribution": agent_data['contribution'],
                f"{prefix}_payoff": agent_data['payoff'],
                f"{prefix}_cumulative_payoff": agent_data['cumulative_payoff'],
                f"{prefix}_stage1_payoff": agent_data['stage1_payoff'],
                f"{prefix}_stage2_payoff": agent_data['stage2_payoff'],
                f"{prefix}_institution": 1 if agent_data['institution_choice'] == 'SI' else 0,
                f"{prefix}_punishments_received": agent_data['received_punishments'],
                f"{prefix}_rewards_received": agent_data['received_rewards'],
                f"{prefix}_punishments_given": sum(agent_data['assigned_punishments'].values()) if agent_data['assigned_punishments'] else 0,
                f"{prefix}_rewards_given": sum(agent_data['assigned_rewards'].values()) if agent_data['assigned_rewards'] else 0,
            })
        
        # Cooperation metrics
        contributions = [agent_data['contribution'] for agent_data in round_data['agents'].values()]
        metrics.update({
            'mean_contribution': sum(contributions) / len(contributions),
            'cooperation_rate': sum(1 for c in contributions if c > 0) / len(contributions),
            'high_cooperation_rate': sum(1 for c in contributions if c >= 15) / len(contributions),
            'contribution_variance': pd.Series(contributions).var(),
            'gini_coefficient': calculate_gini(contributions)
        })
        
        # Log metrics for this round
        wandb.log(metrics)
    
    # Log final summary statistics
    final_metrics = calculate_final_metrics(data)
    wandb.log(final_metrics)
    
    # Log the raw data as an artifact
    if filename:
        artifact = wandb.Artifact('simulation_results', type='dataset')
        artifact.add_file(filename)
        run.log_artifact(artifact)
    
    print(f"Results logged to W&B project: {project_name}")
    print(f"View at: {run.url}")
    
    wandb.finish()

def calculate_gini(values: List[float]) -> float:
    """Calculate Gini coefficient for inequality measurement."""
    if not values:
        return 0
    
    sorted_values = sorted(values)
    n = len(values)
    cumsum = pd.Series(sorted_values).cumsum()
    
    return (n + 1 - 2 * sum(cumsum) / cumsum.iloc[-1]) / n if cumsum.iloc[-1] > 0 else 0

def calculate_final_metrics(data: List[Dict]) -> Dict:
    """Calculate final summary metrics."""
    # Extract all contributions
    all_contributions = []
    all_payoffs = []
    si_rounds = 0
    total_punishments = 0
    total_rewards = 0
    
    for round_data in data:
        for agent_data in round_data['agents'].values():
            all_contributions.append(agent_data['contribution'])
            all_payoffs.append(agent_data['payoff'])
            if agent_data['institution_choice'] == 'SI':
                si_rounds += 1
            total_punishments += sum(agent_data['assigned_punishments'].values()) if agent_data['assigned_punishments'] else 0
            total_rewards += sum(agent_data['assigned_rewards'].values()) if agent_data['assigned_rewards'] else 0
    
    return {
        'final_mean_contribution': sum(all_contributions) / len(all_contributions),
        'final_mean_payoff': sum(all_payoffs) / len(all_payoffs),
        'final_cooperation_rate': sum(1 for c in all_contributions if c > 0) / len(all_contributions),
        'si_adoption_rate': si_rounds / (len(data) * len(data[0]['agents'])),
        'total_punishments_all_rounds': total_punishments,
        'total_rewards_all_rounds': total_rewards,
        'final_cumulative_payoff_agent_0': data[-1]['agents']['0']['cumulative_payoff'],
        'final_cumulative_payoff_agent_1': data[-1]['agents']['1']['cumulative_payoff']
    }

def create_wandb_report_template():
    """Create a template for W&B report configuration."""
    report_config = {
        "title": "SanctSim Experiment Analysis",
        "description": "Analysis of public goods game with sanctioning institutions",
        "panels": [
            {
                "title": "Contribution Patterns Over Time",
                "chart_type": "line",
                "metrics": ["agent_0_contribution", "agent_1_contribution"],
                "x_axis": "round"
            },
            {
                "title": "Institution Choice Over Time", 
                "chart_type": "line",
                "metrics": ["num_si_members", "num_sfi_members"],
                "x_axis": "round"
            },
            {
                "title": "Sanctions Activity",
                "chart_type": "line", 
                "metrics": ["agent_0_punishments_given", "agent_1_punishments_given", 
                           "agent_0_rewards_given", "agent_1_rewards_given"],
                "x_axis": "round"
            },
            {
                "title": "Payoff Evolution",
                "chart_type": "line",
                "metrics": ["agent_0_cumulative_payoff", "agent_1_cumulative_payoff"],
                "x_axis": "round"
            },
            {
                "title": "Cooperation Metrics",
                "chart_type": "line",
                "metrics": ["cooperation_rate", "mean_contribution", "gini_coefficient"],
                "x_axis": "round"
            }
        ]
    }
    
    print("=== W&B REPORT TEMPLATE ===")
    print("You can use this configuration to create dashboards in W&B:")
    print(json.dumps(report_config, indent=2))
    
    return report_config

def main():
    """Main function to demonstrate W&B integration."""
    import glob
    import os
    
    print("=== WEIGHTS & BIASES INTEGRATION FOR SANCTSIM ===")
    
    if not WANDB_AVAILABLE:
        print("To use W&B integration:")
        print("1. Install wandb: pip install wandb")
        print("2. Create account at https://wandb.ai")
        print("3. Login: wandb login")
        print("4. Run this script again")
        return
    
    # Find all simulation result files
    result_files = glob.glob("simulation_results_*alpha*.json")
    
    if not result_files:
        print("No simulation result files found with alpha parameter.")
        print("Looking for files matching pattern: simulation_results_*alpha*.json")
        return
    
    print(f"Found {len(result_files)} simulation result files:")
    for i, file in enumerate(result_files):
        print(f"{i+1}. {file}")
    
    print("\nAvailable W&B integration options:")
    print("1. Log all results to W&B")
    print("2. Log specific file to W&B")
    print("3. Show report template configuration")
    print("4. Both log all and show template")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice in ['1', '4']:
        print("\nLogging all files to W&B...")
        for filename in result_files:
            print(f"Processing {filename}...")
            try:
                data = load_simulation_results(filename)
                log_to_wandb(data, filename)
                print(f"✓ Successfully logged {filename}")
            except Exception as e:
                print(f"✗ Error logging {filename}: {e}")
    
    elif choice == '2':
        file_num = int(input(f"Enter file number (1-{len(result_files)}): ").strip()) - 1
        if 0 <= file_num < len(result_files):
            filename = result_files[file_num]
            print(f"\nLogging {filename} to W&B...")
            try:
                data = load_simulation_results(filename)
                log_to_wandb(data, filename)
                print(f"✓ Successfully logged {filename}")
            except Exception as e:
                print(f"✗ Error logging {filename}: {e}")
        else:
            print("Invalid file number")
    
    if choice in ['3', '4']:
        print("\nGenerating report template...")
        create_wandb_report_template()
    
    print("\n=== W&B BENEFITS FOR SANCTSIM ===")
    print("- Track experiments across different models and parameters")
    print("- Compare contribution patterns between different LLMs")
    print("- Visualize cooperation emergence over time")
    print("- Monitor sanctioning behavior and effectiveness")
    print("- Create shareable reports and dashboards")
    print("- Hyperparameter sweeps for different game configurations")

if __name__ == "__main__":
    main()