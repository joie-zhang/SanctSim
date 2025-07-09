#!/usr/bin/env python3
"""
Analyze SanctSim sweep results to identify missing/failed combinations
"""

import os
import glob
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Expected configurations from sweep_runner.py
EXPECTED_MODELS = [
    'claude-3.5-sonnet', 'claude-3.5-haiku', 'claude-4-opus', 'claude-4-sonnet',
    'o1-mini', 'o3', 'o3-mini-low', 'o3-mini-med', 'o3-mini-high',
    'o4-mini-low', 'o4-mini-med', 'o4-mini-high', 'llama', 'qwen'
]

EXPECTED_ALPHAS = [0.5, 1, 1.6, 2, 4, 10]
EXPECTED_AGENTS = [7]  # Based on the current sweep pattern

# Model categorization by expected runtime
FAST_MODELS = ['claude-3.5-haiku', 'llama', 'qwen']
MEDIUM_MODELS = ['claude-3.5-sonnet', 'o1-mini', 'o3-mini-low', 'o3-mini-med', 'o4-mini-low', 'o4-mini-med']
SLOW_MODELS = ['claude-4-opus', 'claude-4-sonnet', 'o3', 'o3-mini-high', 'o4-mini-high']

def extract_run_info_from_filename(filename: str) -> Tuple[str, int, float]:
    """Extract model, agents, and alpha from result filename"""
    # Handle different filename patterns
    patterns = [
        r'simulation_results_(.+?)_(\d+)agents_\d+rounds_alpha([\d.]+)\.json',
        r'(.+?)_(\d+)agents_alpha([\d.]+)_stdout\.log',
        r'(.+?)_(\d+)agents_alpha([\d.]+)_stderr\.log',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            model_raw = match.group(1)
            agents = int(match.group(2))
            alpha = float(match.group(3))
            
            # Normalize model names
            model = normalize_model_name(model_raw)
            return model, agents, alpha
    
    return None, None, None

def normalize_model_name(model_raw: str) -> str:
    """Normalize model names to match expected format"""
    # Handle different model name formats
    mapping = {
        'anthropic_claude-3.5-sonnet': 'claude-3.5-sonnet',
        'anthropic_claude-3.5-haiku': 'claude-3.5-haiku',
        'anthropic_claude-opus-4-20250514': 'claude-4-opus',
        'anthropic_claude-sonnet-4-20250514': 'claude-4-sonnet',
        'o1-mini-2024-09-12': 'o1-mini',
        'o3-2025-04-16': 'o3',
        'o3-mini-2025-01-31': 'o3-mini',  # This needs sub-classification
        'o4-mini-2025-04-16': 'o4-mini',  # This needs sub-classification
        'meta-llama_llama-3.1-8b-instruct': 'llama',
        'qwen_qwen-2.5-vl-7b-instruct': 'qwen',
    }
    
    # Handle special cases for effort levels
    if model_raw in mapping:
        return mapping[model_raw]
    
    # Handle effort-based models by looking at the context
    if 'o3-mini' in model_raw:
        return 'o3-mini'  # Base name, effort determined by context
    if 'o4-mini' in model_raw:
        return 'o4-mini'  # Base name, effort determined by context
    
    return model_raw

def find_successful_runs() -> Set[Tuple[str, int, float]]:
    """Find all successful runs from result files"""
    successful = set()
    
    # Look for JSON result files
    result_files = glob.glob('/Users/joie/Desktop/SanctSim/sweep/*/results/*.json')
    
    for file_path in result_files:
        filename = os.path.basename(file_path)
        model, agents, alpha = extract_run_info_from_filename(filename)
        if model and agents and alpha:
            successful.add((model, agents, alpha))
    
    return successful

def find_attempted_runs() -> Set[Tuple[str, int, float]]:
    """Find all attempted runs from log files"""
    attempted = set()
    
    # Look for stdout log files
    log_files = glob.glob('/Users/joie/Desktop/SanctSim/sweep/*/logs/*_stdout.log')
    
    for file_path in log_files:
        filename = os.path.basename(file_path)
        model, agents, alpha = extract_run_info_from_filename(filename)
        if model and agents and alpha:
            attempted.add((model, agents, alpha))
    
    return attempted

def generate_expected_runs() -> Set[Tuple[str, int, float]]:
    """Generate all expected run combinations"""
    expected = set()
    
    for model in EXPECTED_MODELS:
        for agents in EXPECTED_AGENTS:
            for alpha in EXPECTED_ALPHAS:
                expected.add((model, agents, alpha))
    
    return expected

def categorize_by_runtime(runs: List[Tuple[str, int, float]]) -> Dict[str, List[Tuple[str, int, float]]]:
    """Categorize runs by expected runtime"""
    categorized = {
        'fast': [],
        'medium': [],
        'slow': []
    }
    
    for model, agents, alpha in runs:
        if model in FAST_MODELS:
            categorized['fast'].append((model, agents, alpha))
        elif model in MEDIUM_MODELS:
            categorized['medium'].append((model, agents, alpha))
        elif model in SLOW_MODELS:
            categorized['slow'].append((model, agents, alpha))
        else:
            # Default to medium for unknown models
            categorized['medium'].append((model, agents, alpha))
    
    return categorized

def analyze_failure_patterns(attempted: Set, successful: Set) -> Dict[str, List]:
    """Analyze failure patterns"""
    failed = attempted - successful
    
    failure_patterns = defaultdict(list)
    
    for model, agents, alpha in failed:
        failure_patterns[model].append((agents, alpha))
    
    return dict(failure_patterns)

def generate_rerun_commands(missing_runs: List[Tuple[str, int, float]]) -> List[str]:
    """Generate command lines for missing runs"""
    commands = []
    
    # Model to provider mapping
    model_configs = {
        'claude-3.5-sonnet': ('openrouter', 'anthropic/claude-3.5-sonnet'),
        'claude-3.5-haiku': ('openrouter', 'anthropic/claude-3.5-haiku'),
        'claude-4-opus': ('openrouter', 'anthropic/claude-opus-4-20250514'),
        'claude-4-sonnet': ('openrouter', 'anthropic/claude-sonnet-4-20250514'),
        'o1-mini': ('openai', 'o1-mini-2024-09-12'),
        'o3': ('openai', 'o3-2025-04-16'),
        'o3-mini-low': ('openai', 'o3-mini-2025-01-31'),
        'o3-mini-med': ('openai', 'o3-mini-2025-01-31'),
        'o3-mini-high': ('openai', 'o3-mini-2025-01-31'),
        'o4-mini-low': ('openai', 'o4-mini-2025-04-16'),
        'o4-mini-med': ('openai', 'o4-mini-2025-04-16'),
        'o4-mini-high': ('openai', 'o4-mini-2025-04-16'),
        'llama': ('openrouter', 'meta-llama/llama-3.1-8b-instruct'),
        'qwen': ('openrouter', 'qwen/qwen-2.5-vl-7b-instruct'),
    }
    
    for model, agents, alpha in missing_runs:
        if model in model_configs:
            provider, model_name = model_configs[model]
            cmd = f"python code/main.py --api-provider {provider} --model-name {model_name} --num-agents {agents} --num-rounds 15 --alpha {alpha}"
            
            # Add reasoning effort for o3/o4 models
            if '-low' in model:
                cmd += " --reasoning-effort low"
            elif '-med' in model:
                cmd += " --reasoning-effort medium"
            elif '-high' in model:
                cmd += " --reasoning-effort high"
            
            commands.append(cmd)
    
    return commands

def main():
    print("=== SanctSim Sweep Analysis ===\n")
    
    # Get all combinations
    expected_runs = generate_expected_runs()
    successful_runs = find_successful_runs()
    attempted_runs = find_attempted_runs()
    
    print(f"Expected total runs: {len(expected_runs)}")
    print(f"Successful runs: {len(successful_runs)}")
    print(f"Attempted runs: {len(attempted_runs)}")
    print(f"Never attempted: {len(expected_runs - attempted_runs)}")
    print(f"Failed runs: {len(attempted_runs - successful_runs)}")
    
    # Show successful runs
    print("\n=== SUCCESSFUL RUNS ===")
    for model, agents, alpha in sorted(successful_runs):
        print(f"✓ {model} - {agents} agents - alpha {alpha}")
    
    # Show failed runs (attempted but not successful)
    failed_runs = attempted_runs - successful_runs
    print(f"\n=== FAILED RUNS ({len(failed_runs)}) ===")
    failure_patterns = analyze_failure_patterns(attempted_runs, successful_runs)
    for model, failures in sorted(failure_patterns.items()):
        print(f"✗ {model}: {len(failures)} failures")
        for agents, alpha in sorted(failures):
            print(f"  - {agents} agents, alpha {alpha}")
    
    # Show never attempted runs
    never_attempted = expected_runs - attempted_runs
    print(f"\n=== NEVER ATTEMPTED ({len(never_attempted)}) ===")
    for model, agents, alpha in sorted(never_attempted):
        print(f"- {model} - {agents} agents - alpha {alpha}")
    
    # All missing runs (never attempted + failed)
    missing_runs = list(never_attempted | failed_runs)
    print(f"\n=== ALL MISSING RUNS ({len(missing_runs)}) ===")
    
    # Categorize by runtime
    categorized = categorize_by_runtime(missing_runs)
    
    print(f"\nFast models ({len(categorized['fast'])} runs):")
    for model, agents, alpha in sorted(categorized['fast']):
        print(f"  {model} - {agents} agents - alpha {alpha}")
    
    print(f"\nMedium models ({len(categorized['medium'])} runs):")
    for model, agents, alpha in sorted(categorized['medium']):
        print(f"  {model} - {agents} agents - alpha {alpha}")
    
    print(f"\nSlow models ({len(categorized['slow'])} runs):")
    for model, agents, alpha in sorted(categorized['slow']):
        print(f"  {model} - {agents} agents - alpha {alpha}")
    
    # Generate rerun commands
    print(f"\n=== RERUN COMMANDS ===")
    commands = generate_rerun_commands(missing_runs)
    
    print(f"\nFast models commands:")
    fast_commands = generate_rerun_commands(categorized['fast'])
    for i, cmd in enumerate(fast_commands, 1):
        print(f"{i:2d}. {cmd}")
    
    print(f"\nMedium models commands:")
    medium_commands = generate_rerun_commands(categorized['medium'])
    for i, cmd in enumerate(medium_commands, 1):
        print(f"{i:2d}. {cmd}")
    
    print(f"\nSlow models commands:")
    slow_commands = generate_rerun_commands(categorized['slow'])
    for i, cmd in enumerate(slow_commands, 1):
        print(f"{i:2d}. {cmd}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total expected combinations: {len(expected_runs)}")
    print(f"Successful: {len(successful_runs)} ({len(successful_runs)/len(expected_runs)*100:.1f}%)")
    print(f"Missing: {len(missing_runs)} ({len(missing_runs)/len(expected_runs)*100:.1f}%)")
    print(f"  - Never attempted: {len(never_attempted)}")
    print(f"  - Failed: {len(failed_runs)}")
    print(f"\nRuntime distribution of missing runs:")
    print(f"  - Fast: {len(categorized['fast'])} runs")
    print(f"  - Medium: {len(categorized['medium'])} runs")
    print(f"  - Slow: {len(categorized['slow'])} runs")

if __name__ == "__main__":
    main()