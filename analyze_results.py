#!/usr/bin/env python3
"""
Analysis script for SanctSim simulation results.
Analyzes agent contribution patterns and payoffs over time.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

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

def analyze_contributions(data: List[Dict]) -> pd.DataFrame:
    """Analyze contribution patterns over time."""
    rounds = []
    agent_0_contributions = []
    agent_1_contributions = []
    total_contributions = []
    agent_0_payoffs = []
    agent_1_payoffs = []
    agent_0_cumulative = []
    agent_1_cumulative = []
    agent_0_institutions = []
    agent_1_institutions = []
    agent_0_punishments_received = []
    agent_1_punishments_received = []
    agent_0_rewards_received = []
    agent_1_rewards_received = []
    agent_0_punishments_given = []
    agent_1_punishments_given = []
    agent_0_rewards_given = []
    agent_1_rewards_given = []
    
    for round_data in data:
        round_num = round_data['round_number']
        rounds.append(round_num)
        
        # Get contributions
        agent_0_contrib = round_data['agents']['0']['contribution']
        agent_1_contrib = round_data['agents']['1']['contribution']
        agent_0_contributions.append(agent_0_contrib)
        agent_1_contributions.append(agent_1_contrib)
        total_contributions.append(agent_0_contrib + agent_1_contrib)
        
        # Get payoffs
        agent_0_payoffs.append(round_data['agents']['0']['payoff'])
        agent_1_payoffs.append(round_data['agents']['1']['payoff'])
        agent_0_cumulative.append(round_data['agents']['0']['cumulative_payoff'])
        agent_1_cumulative.append(round_data['agents']['1']['cumulative_payoff'])
        
        # Get institutions
        agent_0_institutions.append(round_data['agents']['0']['institution_choice'])
        agent_1_institutions.append(round_data['agents']['1']['institution_choice'])
        
        # Get sanctions (punishments and rewards)
        agent_0_punishments_received.append(round_data['agents']['0']['received_punishments'])
        agent_1_punishments_received.append(round_data['agents']['1']['received_punishments'])
        agent_0_rewards_received.append(round_data['agents']['0']['received_rewards'])
        agent_1_rewards_received.append(round_data['agents']['1']['received_rewards'])
        
        # Count punishments/rewards given
        agent_0_punishments = round_data['agents']['0']['assigned_punishments']
        agent_1_punishments = round_data['agents']['1']['assigned_punishments']
        agent_0_rewards = round_data['agents']['0']['assigned_rewards']
        agent_1_rewards = round_data['agents']['1']['assigned_rewards']
        
        agent_0_punishments_given.append(sum(agent_0_punishments.values()) if agent_0_punishments else 0)
        agent_1_punishments_given.append(sum(agent_1_punishments.values()) if agent_1_punishments else 0)
        agent_0_rewards_given.append(sum(agent_0_rewards.values()) if agent_0_rewards else 0)
        agent_1_rewards_given.append(sum(agent_1_rewards.values()) if agent_1_rewards else 0)
    
    df = pd.DataFrame({
        'round': rounds,
        'agent_0_contribution': agent_0_contributions,
        'agent_1_contribution': agent_1_contributions,
        'total_contribution': total_contributions,
        'agent_0_payoff': agent_0_payoffs,
        'agent_1_payoff': agent_1_payoffs,
        'agent_0_cumulative': agent_0_cumulative,
        'agent_1_cumulative': agent_1_cumulative,
        'agent_0_institution': agent_0_institutions,
        'agent_1_institution': agent_1_institutions,
        'agent_0_punishments_received': agent_0_punishments_received,
        'agent_1_punishments_received': agent_1_punishments_received,
        'agent_0_rewards_received': agent_0_rewards_received,
        'agent_1_rewards_received': agent_1_rewards_received,
        'agent_0_punishments_given': agent_0_punishments_given,
        'agent_1_punishments_given': agent_1_punishments_given,
        'agent_0_rewards_given': agent_0_rewards_given,
        'agent_1_rewards_given': agent_1_rewards_given
    })
    
    return df

def analyze_theoretical_payoffs(contribution_levels: List[int], multiplier: float, endowment: int = 20) -> Dict:
    """Analyze theoretical payoffs for different contribution levels."""
    results = {}
    
    for contrib in contribution_levels:
        # Each agent contributes 'contrib', keeps (endowment - contrib)
        # Total contribution = 2 * contrib (for 2 agents)
        # Each agent gets (2 * contrib * multiplier) / 2 = contrib * multiplier
        # Total payoff = (endowment - contrib) + (contrib * multiplier)
        kept = endowment - contrib
        received_from_pool = contrib * multiplier
        total_payoff = kept + received_from_pool
        
        results[contrib] = {
            'kept': kept,
            'received': received_from_pool,
            'total': total_payoff,
            'net_gain': total_payoff - endowment
        }
    
    return results

def plot_contributions(df: pd.DataFrame, save_path: str = None, metadata: Dict = None):
    """Plot contribution patterns over time."""
    fig, axes = plt.subplots(3, 2, figsize=(15, 15))
    
    # Create title with metadata if available
    if metadata:
        title_prefix = f"{metadata['model_name']} (α={metadata['alpha']}) - "
    else:
        title_prefix = ""
    
    # Plot 1: Individual contributions over time
    axes[0, 0].plot(df['round'], df['agent_0_contribution'], 'b-o', label='Agent 0', linewidth=2)
    axes[0, 0].plot(df['round'], df['agent_1_contribution'], 'r-s', label='Agent 1', linewidth=2)
    axes[0, 0].set_xlabel('Round')
    axes[0, 0].set_ylabel('Contribution')
    axes[0, 0].set_title(f'{title_prefix}Individual Contributions Over Time')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Total contributions over time
    axes[0, 1].plot(df['round'], df['total_contribution'], 'g-o', linewidth=2)
    axes[0, 1].set_xlabel('Round')
    axes[0, 1].set_ylabel('Total Contribution')
    axes[0, 1].set_title('Total Contributions Over Time')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Round payoffs
    axes[1, 0].plot(df['round'], df['agent_0_payoff'], 'b-o', label='Agent 0', linewidth=2)
    axes[1, 0].plot(df['round'], df['agent_1_payoff'], 'r-s', label='Agent 1', linewidth=2)
    axes[1, 0].set_xlabel('Round')
    axes[1, 0].set_ylabel('Round Payoff')
    axes[1, 0].set_title('Round Payoffs Over Time')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Cumulative payoffs
    axes[1, 1].plot(df['round'], df['agent_0_cumulative'], 'b-o', label='Agent 0', linewidth=2)
    axes[1, 1].plot(df['round'], df['agent_1_cumulative'], 'r-s', label='Agent 1', linewidth=2)
    axes[1, 1].set_xlabel('Round')
    axes[1, 1].set_ylabel('Cumulative Payoff')
    axes[1, 1].set_title('Cumulative Payoffs Over Time')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # Plot 5: Punishments over time
    axes[2, 0].plot(df['round'], df['agent_0_punishments_received'], 'b-o', label='Agent 0 Received', linewidth=2)
    axes[2, 0].plot(df['round'], df['agent_1_punishments_received'], 'r-s', label='Agent 1 Received', linewidth=2)
    axes[2, 0].plot(df['round'], df['agent_0_punishments_given'], 'b--^', label='Agent 0 Given', linewidth=2, alpha=0.7)
    axes[2, 0].plot(df['round'], df['agent_1_punishments_given'], 'r--v', label='Agent 1 Given', linewidth=2, alpha=0.7)
    axes[2, 0].set_xlabel('Round')
    axes[2, 0].set_ylabel('Punishment Tokens')
    axes[2, 0].set_title('Punishments Over Time')
    axes[2, 0].legend()
    axes[2, 0].grid(True, alpha=0.3)
    
    # Plot 6: Rewards over time
    axes[2, 1].plot(df['round'], df['agent_0_rewards_received'], 'b-o', label='Agent 0 Received', linewidth=2)
    axes[2, 1].plot(df['round'], df['agent_1_rewards_received'], 'r-s', label='Agent 1 Received', linewidth=2)
    axes[2, 1].plot(df['round'], df['agent_0_rewards_given'], 'b--^', label='Agent 0 Given', linewidth=2, alpha=0.7)
    axes[2, 1].plot(df['round'], df['agent_1_rewards_given'], 'r--v', label='Agent 1 Given', linewidth=2, alpha=0.7)
    axes[2, 1].set_xlabel('Round')
    axes[2, 1].set_ylabel('Reward Tokens')
    axes[2, 1].set_title('Rewards Over Time')
    axes[2, 1].legend()
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    plt.show()

def print_summary_stats(df: pd.DataFrame, data: List[Dict]):
    """Print summary statistics."""
    print("=== SIMULATION SUMMARY ===")
    print(f"Total Rounds: {len(df)}")
    print(f"Agent 0 Institution Choices: {df['agent_0_institution'].unique()}")
    print(f"Agent 1 Institution Choices: {df['agent_1_institution'].unique()}")
    
    # Detect multiplier from actual data
    sample_round = data[0]
    sample_contrib = sample_round['agents']['0']['contribution']
    sample_stage1 = sample_round['agents']['0']['stage1_payoff']
    sample_endowment = 20  # From parameters
    
    # Calculate multiplier: stage1_payoff = (endowment - contribution) + (total_contrib * multiplier / num_agents)
    total_contrib = sum(agent_data['contribution'] for agent_data in sample_round['agents'].values())
    received_from_pool = sample_stage1 - (sample_endowment - sample_contrib)
    multiplier = received_from_pool / sample_contrib if sample_contrib > 0 else 2.0
    
    print(f"Public Good Multiplier: {multiplier:.1f}")
    print(f"Endowment per stage: {sample_endowment} tokens")
    print()
    
    print("=== CONTRIBUTION PATTERNS ===")
    print(f"Agent 0 - Mean: {df['agent_0_contribution'].mean():.2f}, Std: {df['agent_0_contribution'].std():.2f}")
    print(f"Agent 1 - Mean: {df['agent_1_contribution'].mean():.2f}, Std: {df['agent_1_contribution'].std():.2f}")
    print(f"Total - Mean: {df['total_contribution'].mean():.2f}, Std: {df['total_contribution'].std():.2f}")
    print()
    
    print("=== INSTITUTION ANALYSIS ===")
    si_rounds_0 = (df['agent_0_institution'] == 'SI').sum()
    si_rounds_1 = (df['agent_1_institution'] == 'SI').sum()
    print(f"Agent 0 - SI rounds: {si_rounds_0}/{len(df)} ({si_rounds_0/len(df)*100:.1f}%)")
    print(f"Agent 1 - SI rounds: {si_rounds_1}/{len(df)} ({si_rounds_1/len(df)*100:.1f}%)")
    print()
    
    print("=== SANCTIONS ANALYSIS ===")
    total_punishments_0 = df['agent_0_punishments_given'].sum()
    total_punishments_1 = df['agent_1_punishments_given'].sum()
    total_rewards_0 = df['agent_0_rewards_given'].sum()
    total_rewards_1 = df['agent_1_rewards_given'].sum()
    
    print(f"Agent 0 - Total punishments given: {total_punishments_0}, Total rewards given: {total_rewards_0}")
    print(f"Agent 1 - Total punishments given: {total_punishments_1}, Total rewards given: {total_rewards_1}")
    
    punishments_received_0 = df['agent_0_punishments_received'].sum()
    punishments_received_1 = df['agent_1_punishments_received'].sum()
    rewards_received_0 = df['agent_0_rewards_received'].sum()
    rewards_received_1 = df['agent_1_rewards_received'].sum()
    
    print(f"Agent 0 - Total punishments received: {punishments_received_0}, Total rewards received: {rewards_received_0}")
    print(f"Agent 1 - Total punishments received: {punishments_received_1}, Total rewards received: {rewards_received_1}")
    print()
    
    print("=== PAYOFF ANALYSIS ===")
    print(f"Agent 0 - Mean Round Payoff: {df['agent_0_payoff'].mean():.2f}")
    print(f"Agent 1 - Mean Round Payoff: {df['agent_1_payoff'].mean():.2f}")
    print(f"Agent 0 - Final Cumulative: {df['agent_0_cumulative'].iloc[-1]:.2f}")
    print(f"Agent 1 - Final Cumulative: {df['agent_1_cumulative'].iloc[-1]:.2f}")
    print()
    
    print("=== THEORETICAL ANALYSIS ===")
    alpha = multiplier / 2  # Individual return rate
    print(f"Alpha (individual return rate): {alpha:.2f}")
    print(f"With α = {alpha:.2f} {'< 1' if alpha < 1 else '>= 1'} and endowment = {sample_endowment}:")
    print("- Contributing 0: Payoff = 20 + 0 = 20")
    print("- Contributing 10: Payoff = 10 + ? = ?")
    print("- Contributing 20: Payoff = 0 + ? = ?")
    print("- Nash Equilibrium (selfish): Contribute 0" if alpha < 1 else "- Nash Equilibrium: Contribute all")
    print("- Social Optimum: Contribute 20")
    
    avg_contrib = df[['agent_0_contribution', 'agent_1_contribution']].mean().mean()
    print(f"- Observed: Contribute {avg_contrib:.1f} (behavioral equilibrium)")
    print()
    
    if alpha < 1:
        print("=== WHY AGENTS CONTRIBUTE DESPITE α < 1 ===")
        print("Economic theory predicts zero contribution when α < 1, but we observe significant cooperation!")
        print("Possible explanations:")
        print("1. LLM reasoning emphasizes mutual benefit over individual optimization")
        print("2. Agents recognize that reciprocal cooperation yields higher payoffs")
        print("3. Learning from repeated interactions builds trust")
        print("4. Behavioral/social preferences override pure economic rationality")
        print("5. Strategic considerations in multi-round games")

def analyze_cooperation_stability(df: pd.DataFrame):
    """Analyze cooperation stability."""
    print("\n=== COOPERATION STABILITY ANALYSIS ===")
    
    # Check for deviations
    deviations = df[df['agent_0_contribution'] != df['agent_1_contribution']]
    print(f"Rounds with different contributions: {len(deviations)}")
    
    # Check contribution consistency
    unique_contributions = df['agent_0_contribution'].unique()
    print(f"Unique contribution levels: {unique_contributions}")
    
    # Calculate cooperation index (contribution / max possible)
    cooperation_index = df['total_contribution'] / (2 * 20)  # 2 agents * 20 max each
    print(f"Mean cooperation index: {cooperation_index.mean():.3f}")
    print(f"Cooperation stability (1 - std): {1 - cooperation_index.std():.3f}")

def extract_metadata_from_filename(filename: str) -> Dict:
    """Extract model name and alpha from filename."""
    import re
    import os
    
    basename = os.path.basename(filename)
    
    # Extract model name
    model_match = re.search(r'simulation_results_([^_]+(?:_[^_]+)*?)_\d+agents', basename)
    model_name = model_match.group(1).replace('_', '/') if model_match else 'unknown_model'
    
    # Extract alpha value (stop at non-digit, non-period characters)
    alpha_match = re.search(r'alpha([0-9]+(?:\.[0-9]+)?)', basename)
    alpha = float(alpha_match.group(1)) if alpha_match else 1.6
    
    # Extract number of agents
    agents_match = re.search(r'(\d+)agents', basename)
    num_agents = int(agents_match.group(1)) if agents_match else 2
    
    # Extract number of rounds
    rounds_match = re.search(r'(\d+)rounds', basename)
    num_rounds = int(rounds_match.group(1)) if rounds_match else 15
    
    return {
        'model_name': model_name,
        'alpha': alpha,
        'num_agents': num_agents,
        'num_rounds': num_rounds,
        'basename': basename
    }

def main():
    """Main analysis function."""
    import glob
    import sys
    
    # Find all simulation result files with alpha parameter
    result_files = glob.glob("simulation_results_*alpha*.json")
    
    if not result_files:
        print("No simulation result files found with alpha parameter.")
        print("Looking for files matching pattern: simulation_results_*alpha*.json")
        return
    
    # If multiple files, let user choose or analyze all
    if len(result_files) == 1:
        filename = result_files[0]
        print(f"Found 1 file: {filename}")
    else:
        print(f"Found {len(result_files)} simulation result files:")
        for i, file in enumerate(result_files):
            print(f"{i+1}. {file}")
        
        try:
            choice = input(f"\nEnter file number (1-{len(result_files)}) or 'all' for batch analysis: ").strip()
            if choice.lower() == 'all':
                # Batch analysis
                for filename in result_files:
                    print(f"\n{'='*80}")
                    print(f"ANALYZING: {filename}")
                    print(f"{'='*80}")
                    analyze_single_file(filename)
                return
            else:
                file_num = int(choice) - 1
                if 0 <= file_num < len(result_files):
                    filename = result_files[file_num]
                else:
                    print("Invalid choice")
                    return
        except (EOFError, ValueError):
            # Default to first file if running non-interactively
            filename = result_files[0]
            print(f"Running non-interactively, using: {filename}")
    
    analyze_single_file(filename)

def analyze_single_file(filename: str):
    """Analyze a single simulation file."""
    # Extract metadata
    metadata = extract_metadata_from_filename(filename)
    
    print(f"Model: {metadata['model_name']}")
    print(f"Alpha (multiplier): {metadata['alpha']}")
    print(f"Agents: {metadata['num_agents']}, Rounds: {metadata['num_rounds']}")
    print()
    
    # Load data
    data = load_simulation_results(filename)
    
    # Analyze contributions
    df = analyze_contributions(data)
    
    # Print summary statistics
    print_summary_stats(df, data)
    
    # Analyze cooperation stability
    analyze_cooperation_stability(df)
    
    # Create plots with dynamic filename
    plot_filename = f"analysis_{metadata['basename'].replace('.json', '.png')}"
    plot_contributions(df, plot_filename, metadata)
    
    # Analyze theoretical payoffs using detected multiplier
    print("\n=== THEORETICAL PAYOFF ANALYSIS ===")
    theoretical = analyze_theoretical_payoffs([0, 5, 10, 15, 20], metadata['alpha'])
    for contrib, payoff_info in theoretical.items():
        print(f"Contribution {contrib}: Total payoff = {payoff_info['total']}, Net gain = {payoff_info['net_gain']}")

if __name__ == "__main__":
    main()