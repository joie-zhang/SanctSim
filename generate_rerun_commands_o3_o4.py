#!/usr/bin/env python3
"""
Generate rerun commands for failed o3/o4 SanctSim runs with proper 10-hour timeouts
"""

def generate_o3_o4_rerun_commands():
    """Generate sweep_runner.py commands for failed o3/o4 runs with 10-hour timeouts"""
    
    # Failed runs from the sweep log
    failed_runs = [
        "o4-mini-low_7agents_alpha2",      # Process exited with code 1
        "o3_7agents_alpha0.5",             # Timeout after 30 minutes
        "o4-mini-low_7agents_alpha0.5",    # Timeout after 30 minutes
        "o4-mini-med_7agents_alpha0.5",    # Timeout after 30 minutes
        "o3_7agents_alpha1",               # Timeout after 30 minutes
        "o4-mini-high_7agents_alpha0.5",   # Timeout after 30 minutes
        "o4-mini-low_7agents_alpha1",      # Timeout after 30 minutes
        "o4-mini-high_7agents_alpha1",     # Timeout after 30 minutes
        "o4-mini-med_7agents_alpha1",      # Timeout after 30 minutes
        "o3_7agents_alpha1.6",             # Timeout after 30 minutes
        "o4-mini-high_7agents_alpha1.6",   # Timeout after 30 minutes
        "o4-mini-med_7agents_alpha1.6",    # Timeout after 30 minutes
        "o4-mini-low_7agents_alpha1.6",    # Timeout after 30 minutes
        "o3_7agents_alpha2",               # Timeout after 30 minutes
        "o4-mini-med_7agents_alpha2",      # Timeout after 30 minutes
        "o4-mini-high_7agents_alpha2",     # Timeout after 30 minutes
        "o3_7agents_alpha4",               # Timeout after 30 minutes
        "o4-mini-low_7agents_alpha4",      # Timeout after 30 minutes
        "o4-mini-high_7agents_alpha4",     # Timeout after 30 minutes
        "o4-mini-med_7agents_alpha4",      # Timeout after 30 minutes
        "o3_7agents_alpha10",              # Timeout after 30 minutes
        "o4-mini-low_7agents_alpha10",     # Timeout after 30 minutes
        "o4-mini-high_7agents_alpha10",    # Timeout after 30 minutes
        "o4-mini-med_7agents_alpha10",     # Timeout after 30 minutes
    ]
    
    print("=== O3/O4 FAILED RUNS RERUN COMMANDS ===")
    print(f"Total failed runs to retry: {len(failed_runs)}")
    print("All commands use 10-hour timeout (600 minutes)\n")
    
    # Group by model type for efficient batching
    o3_alphas = set()
    o4_mini_low_alphas = set()
    o4_mini_med_alphas = set()
    o4_mini_high_alphas = set()
    
    for run in failed_runs:
        if run.startswith("o3_"):
            alpha = run.split("_alpha")[1]
            o3_alphas.add(alpha)
        elif run.startswith("o4-mini-low_"):
            alpha = run.split("_alpha")[1]
            o4_mini_low_alphas.add(alpha)
        elif run.startswith("o4-mini-med_"):
            alpha = run.split("_alpha")[1]
            o4_mini_med_alphas.add(alpha)
        elif run.startswith("o4-mini-high_"):
            alpha = run.split("_alpha")[1]
            o4_mini_high_alphas.add(alpha)
    
    print("=== RECOMMENDED EXECUTION ORDER ===")
    print("Run these in order, with 10-hour timeout for each batch:\n")
    
    # 1. O3 model (most expensive, run alone)
    if o3_alphas:
        print("1. O3 MODEL (Run alone - most expensive)")
        alphas_str = " ".join(sorted(o3_alphas))
        print(f"   python sweep_runner.py --models o3 --agents 7 --alphas {alphas_str} --max-parallel 1 --timeout 600")
        print(f"   Expected time: {len(o3_alphas)} * 10 hours = {len(o3_alphas) * 10} hours")
        print()
    
    # 2. O4-mini-high (second most expensive)
    if o4_mini_high_alphas:
        print("2. O4-MINI-HIGH (Run with limited parallelism)")
        alphas_str = " ".join(sorted(o4_mini_high_alphas))
        print(f"   python sweep_runner.py --models o4-mini-high --agents 7 --alphas {alphas_str} --max-parallel 1 --timeout 600")
        print(f"   Expected time: {len(o4_mini_high_alphas)} * 10 hours = {len(o4_mini_high_alphas) * 10} hours")
        print()
    
    # 3. O4-mini-med (medium expensive)
    if o4_mini_med_alphas:
        print("3. O4-MINI-MED (Run with limited parallelism)")
        alphas_str = " ".join(sorted(o4_mini_med_alphas))
        print(f"   python sweep_runner.py --models o4-mini-med --agents 7 --alphas {alphas_str} --max-parallel 2 --timeout 600")
        print(f"   Expected time: {len(o4_mini_med_alphas)} * 5 hours = {len(o4_mini_med_alphas) * 5} hours")
        print()
    
    # 4. O4-mini-low (least expensive)
    if o4_mini_low_alphas:
        print("4. O4-MINI-LOW (Can run with more parallelism)")
        alphas_str = " ".join(sorted(o4_mini_low_alphas))
        print(f"   python sweep_runner.py --models o4-mini-low --agents 7 --alphas {alphas_str} --max-parallel 2 --timeout 600")
        print(f"   Expected time: {len(o4_mini_low_alphas)} * 5 hours = {len(o4_mini_low_alphas) * 5} hours")
        print()
    
    # Alternative: Individual commands for maximum control
    print("=== ALTERNATIVE: INDIVIDUAL COMMANDS ===")
    print("For maximum control, run each individually:")
    print()
    
    # Generate individual commands
    model_mapping = {
        "o3": {"provider": "openai", "model_name": "o3-2025-04-16"},
        "o4-mini-low": {"provider": "openai", "model_name": "o4-mini-2025-04-16", "reasoning_effort": "low"},
        "o4-mini-med": {"provider": "openai", "model_name": "o4-mini-2025-04-16", "reasoning_effort": "medium"},
        "o4-mini-high": {"provider": "openai", "model_name": "o4-mini-2025-04-16", "reasoning_effort": "high"},
    }
    
    for run in sorted(failed_runs):
        # Parse run_id to extract model and alpha
        parts = run.split("_")
        if parts[0] == "o3":
            model_key = "o3"
            alpha = parts[2].replace("alpha", "")
        elif parts[0] == "o4-mini-low":
            model_key = "o4-mini-low"
            alpha = parts[2].replace("alpha", "")
        elif parts[0] == "o4-mini-med":
            model_key = "o4-mini-med"
            alpha = parts[2].replace("alpha", "")
        elif parts[0] == "o4-mini-high":
            model_key = "o4-mini-high"
            alpha = parts[2].replace("alpha", "")
        else:
            continue
        
        model_info = model_mapping[model_key]
        cmd = f"python code/main.py --api-provider {model_info['provider']} --model-name {model_info['model_name']} --num-agents 7 --num-rounds 15 --alpha {alpha}"
        if "reasoning_effort" in model_info:
            cmd += f" --reasoning-effort {model_info['reasoning_effort']}"
        
        print(f"# {run}")
        print(cmd)
        print()
    
    # Summary and recommendations
    print("=== EXECUTION SUMMARY ===")
    total_runs = len(failed_runs)
    o3_runs = len(o3_alphas)
    o4_runs = total_runs - o3_runs
    
    print(f"Total failed runs: {total_runs}")
    print(f"O3 runs: {o3_runs} (most expensive)")
    print(f"O4-mini runs: {o4_runs} (various effort levels)")
    print()
    
    # Time estimates
    print("=== TIME ESTIMATES ===")
    print("Conservative estimates with 10-hour timeout:")
    print(f"O3 runs: {o3_runs} × 10 hours = {o3_runs * 10} hours")
    print(f"O4-mini runs: {o4_runs} × 5 hours = {o4_runs * 5} hours")
    print(f"Total estimated time: {o3_runs * 10 + o4_runs * 5} hours")
    print()
    
    print("=== COST CONSIDERATIONS ===")
    print("⚠️  WARNING: These are expensive models!")
    print("- O3 runs are extremely expensive")
    print("- O4-mini runs are expensive but more reasonable")
    print("- Consider running a small test first (e.g., one alpha value)")
    print("- Monitor costs closely during execution")
    print()
    
    print("=== TROUBLESHOOTING NOTES ===")
    print("- All timeouts now set to 600 minutes (10 hours)")
    print("- One run (o4-mini-low_7agents_alpha2) failed with code 1 - check logs")
    print("- Monitor system resources during long runs")
    print("- Consider running during off-peak hours")
    print("- Save progress frequently")

if __name__ == "__main__":
    generate_o3_o4_rerun_commands()