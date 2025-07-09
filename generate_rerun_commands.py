#!/usr/bin/env python3
"""
Generate efficient rerun commands for missing SanctSim sweep combinations
"""

def generate_sweep_commands():
    """Generate sweep_runner.py commands for efficient re-runs"""
    
    print("=== EFFICIENT RERUN COMMANDS ===\n")
    
    # Fast models (should complete quickly)
    print("1. FAST MODELS (Expected: ~30 minutes total)")
    print("   Run these first to get quick results:")
    print("   python sweep_runner.py --models claude-3.5-haiku --alphas 1.0 2.0 4.0 10.0 --agents 7 --max-parallel 4")
    print("   python sweep_runner.py --models llama qwen --agents 7 --max-parallel 4")
    print()
    
    # Medium models - split into batches
    print("2. MEDIUM MODELS (Expected: ~2-4 hours total)")
    print("   Batch 1 - Claude 3.5 Sonnet failures:")
    print("   python sweep_runner.py --models claude-3.5-sonnet --alphas 1.0 2.0 4.0 10.0 --agents 7 --max-parallel 2")
    print()
    print("   Batch 2 - O1-mini failures:")
    print("   python sweep_runner.py --models o1-mini --alphas 1.0 2.0 10.0 --agents 7 --max-parallel 2")
    print()
    print("   Batch 3 - O3-mini low effort:")
    print("   python sweep_runner.py --models o3-mini-low --agents 7 --max-parallel 2")
    print()
    print("   Batch 4 - O3-mini medium effort:")
    print("   python sweep_runner.py --models o3-mini-med --agents 7 --max-parallel 2")
    print()
    print("   Batch 5 - O4-mini low effort:")
    print("   python sweep_runner.py --models o4-mini-low --agents 7 --max-parallel 2")
    print()
    print("   Batch 6 - O4-mini medium effort:")
    print("   python sweep_runner.py --models o4-mini-med --agents 7 --max-parallel 2")
    print()
    
    # Slow models - run individually or in small batches
    print("3. SLOW MODELS (Expected: 4-8 hours total)")
    print("   Run these with lower parallelism and longer timeouts:")
    print("   python sweep_runner.py --models claude-4-opus --agents 7 --max-parallel 1 --timeout 120")
    print("   python sweep_runner.py --models claude-4-sonnet --agents 7 --max-parallel 1 --timeout 120")
    print("   python sweep_runner.py --models o3 --agents 7 --max-parallel 1 --timeout 240")
    print("   python sweep_runner.py --models o3-mini-high --agents 7 --max-parallel 1 --timeout 120")
    print("   python sweep_runner.py --models o4-mini-high --agents 7 --max-parallel 1 --timeout 120")
    print()
    
    # Priority commands for essential models
    print("4. PRIORITY COMMANDS (Run these first if time is limited)")
    print("   Focus on the most important model/alpha combinations:")
    print("   python sweep_runner.py --models claude-3.5-haiku claude-3.5-sonnet o1-mini --alphas 1.0 2.0 --agents 7 --max-parallel 3")
    print("   python sweep_runner.py --models llama qwen --alphas 1.0 2.0 --agents 7 --max-parallel 2")
    print()
    
    # Single command for all failed runs (not recommended due to time)
    print("5. COMPREHENSIVE RERUN (Use only if you have 8+ hours)")
    print("   This will attempt all missing combinations:")
    print("   python sweep_runner.py --agents 7 --max-parallel 6 --timeout 180")
    print("   (Note: This excludes already successful runs)")
    print()
    
    # Debugging commands for problematic runs
    print("6. DEBUG COMMANDS (For investigating specific failures)")
    print("   Run individual combinations that failed:")
    print("   python code/main.py --api-provider openrouter --model-name anthropic/claude-3.5-haiku --num-agents 7 --num-rounds 15 --alpha 1.0")
    print("   python code/main.py --api-provider openrouter --model-name anthropic/claude-3.5-sonnet --num-agents 7 --num-rounds 15 --alpha 1.0")
    print("   python code/main.py --api-provider openai --model-name o1-mini-2024-09-12 --num-agents 7 --num-rounds 15 --alpha 2.0")
    print()
    
    print("=== RECOMMENDED EXECUTION ORDER ===")
    print("1. Start with Fast Models (30 mins)")
    print("2. Run Priority Commands if time limited")
    print("3. Execute Medium Models in batches (2-4 hours)")
    print("4. Run Slow Models with patience (4-8 hours)")
    print("5. Use Debug Commands for individual failures")
    print()
    
    print("=== TROUBLESHOOTING NOTES ===")
    print("- Claude-4-opus failures: HTTP 400 errors suggest API issues")
    print("- O1-mini failures: Likely punishment parsing errors")
    print("- O3/O4 never attempted: Need to verify API access")
    print("- Parsing errors: May need code fixes before rerunning")
    print("- Timeout recommendations: Fast=30min, Medium=60min, Slow=120-240min")

if __name__ == "__main__":
    generate_sweep_commands()