# SanctSim Parameter Sweep Guide

This guide explains how to use the parameter sweep system to run large-scale experiments across multiple models, agent counts, and alpha values using multiple Claude Code instances.

## Quick Start

### 1. Basic Sweep
```bash
# Run a comprehensive sweep with default settings
python sweep_runner.py

# Run with specific models only
python sweep_runner.py --models claude-3.5-sonnet o4-mini-low

# Run with specific agent counts
python sweep_runner.py --agents 2 5 10

# Run with specific alpha values
python sweep_runner.py --alphas 0.5 1.6 2.0
```

### 2. Monitoring Progress
```bash
# Check current status
python sweep_monitor.py

# Live monitoring (updates every 30 seconds)
python sweep_monitor.py --live

# Generate analysis report
python sweep_monitor.py --report
```

### 3. Managing Processes
```bash
# Kill all running simulations
python sweep_monitor.py --kill

# List available sweep directories
python sweep_monitor.py --list-sweeps
```

## System Overview

### Components

1. **`sweep_runner.py`** - Main sweep orchestrator
2. **`sweep_monitor.py`** - Progress monitoring and management
3. **`sweep_config.json`** - Configuration presets
4. **Results directories** - Organized output storage

### Architecture

```
SanctSim/
├── sweep_runner.py          # Main sweep script
├── sweep_monitor.py         # Monitoring script
├── sweep_config.json        # Configuration presets
├── sweep_results_YYYYMMDD_HHMMSS/
│   ├── logs/               # Individual run logs
│   ├── results/            # Simulation result files
│   ├── progress.json       # Progress tracking
│   ├── sweep_log.txt       # Main sweep log
│   └── sweep_analysis.png  # Analysis plots
```

## Supported Models

### OpenRouter Models
- `claude-3.5-sonnet` - Anthropic Claude 3.5 Sonnet
- `claude-3.5-haiku` - Anthropic Claude 3.5 Haiku  
- `claude-4-opus` - Anthropic Claude 4 Opus (when available)
- `o1` - OpenAI o1
- `o3` - OpenAI o3 (when available)
- `llama-3.1-8b` - Meta Llama 3.1 8B Instruct
- `qwen-2.5-7b` - Qwen 2.5 7B Instruct

### OpenAI Direct Models
- `o4-mini-low` - o4 Mini with low reasoning effort
- `o4-mini-high` - o4 Mini with high reasoning effort

## Parameter Ranges

### Agent Counts
- Default: `[2, 5, 10, 15, 20]`
- Range: 2-50 agents supported

### Alpha Values (Public Good Multiplier)
- Default: `[0.5, 1.0, 1.6, 2.0, 4.0, 10.0]`
- Range: 0.1-20.0 supported
- Critical values:
  - α < 1.0: Free-riding predicted (Nash equilibrium = 0)
  - α = 1.0: Indifference point
  - α > 1.0: Cooperation can be Nash equilibrium

### Other Parameters
- Rounds: Default 15 (configurable)
- Endowments: 20 tokens per stage (fixed)

## Usage Examples

### 1. Model Comparison Study
```bash
# Compare major models on standard parameters
python sweep_runner.py \
  --models claude-3.5-sonnet o4-mini-high o1 \
  --agents 5 10 \
  --alphas 1.6 \
  --max-parallel 3
```

### 2. Alpha Sensitivity Analysis
```bash
# Test how cooperation changes with alpha
python sweep_runner.py \
  --models claude-3.5-sonnet \
  --agents 5 \
  --alphas 0.1 0.5 1.0 1.5 2.0 3.0 5.0 10.0 \
  --max-parallel 4
```

### 3. Scaling Analysis
```bash
# Test how group size affects cooperation
python sweep_runner.py \
  --models claude-3.5-sonnet o4-mini-low \
  --agents 2 5 10 15 20 25 30 \
  --alphas 1.6 \
  --max-parallel 6
```

### 4. Quick Test Run
```bash
# Fast test with subset of parameters
python sweep_runner.py \
  --models claude-3.5-sonnet \
  --agents 2 \
  --alphas 1.6 \
  --timeout 10 \
  --dry-run  # Show what would run without executing
```

## Advanced Features

### Resource Management
- **Parallel Execution**: Run multiple simulations simultaneously
- **Timeout Protection**: Automatic timeout for stuck simulations
- **Memory Monitoring**: Track resource usage
- **Process Management**: Clean shutdown and cleanup

### Error Handling
- **Retry Logic**: Automatic retry for failed runs
- **Error Logging**: Detailed error tracking
- **Graceful Degradation**: Continue sweep if individual runs fail
- **Recovery**: Resume interrupted sweeps

### Progress Tracking
- **Real-time Monitoring**: Live progress updates
- **Detailed Logging**: Comprehensive log files
- **Visual Progress**: Charts and graphs
- **Estimated Completion**: Time remaining calculations

## Output Structure

### Results Directory
```
sweep_results_20240706_143022/
├── logs/
│   ├── claude-3.5-sonnet_5agents_alpha1.6_stdout.log
│   ├── claude-3.5-sonnet_5agents_alpha1.6_stderr.log
│   └── ...
├── results/
│   ├── simulation_results_anthropic_claude-3.5-sonnet_5agents_15rounds_alpha1.6.json
│   └── ...
├── progress.json                # Progress tracking data
├── sweep_log.txt               # Main sweep log
└── sweep_analysis.png          # Analysis visualization
```

### Progress File Format
```json
{
  "total_runs": 180,
  "completed": 156,
  "failed": 4,
  "active": 2,
  "completed_runs": [...],
  "failed_runs": [...],
  "timestamp": "2024-07-06T14:30:22"
}
```

## Performance Optimization

### Parallel Execution
```bash
# Optimize for your system
python sweep_runner.py --max-parallel 8  # 8-core system
python sweep_runner.py --max-parallel 4  # 4-core system
python sweep_runner.py --max-parallel 2  # Limited resources
```

### Timeout Settings
```bash
# Adjust based on expected runtime
python sweep_runner.py --timeout 60  # 1 hour for large runs
python sweep_runner.py --timeout 15  # 15 minutes for quick tests
```

### Memory Management
- Monitor with `sweep_monitor.py --live`
- Kill processes if needed: `sweep_monitor.py --kill`
- Check system resources before large sweeps

## Best Practices

### 1. Planning Your Sweep
- Start with `--dry-run` to estimate scope
- Use `--list-models` to verify available models
- Check API quotas and rate limits
- Estimate total runtime and costs

### 2. Resource Management
- Don't exceed system capacity
- Monitor memory usage during runs
- Use appropriate timeout values
- Consider API rate limits

### 3. Error Prevention
- Verify API keys are set
- Test individual model configurations first
- Use conservative parallel settings initially
- Monitor early runs for issues

### 4. Data Management
- Regularly backup sweep results
- Clean up old sweep directories
- Archive completed sweeps
- Monitor disk space usage

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Check environment variables
   echo $OPENROUTER_API_KEY
   echo $OPENAI_API_KEY
   ```

2. **Timeout Issues**
   ```bash
   # Increase timeout for complex runs
   python sweep_runner.py --timeout 45
   ```

3. **Memory Issues**
   ```bash
   # Reduce parallel jobs
   python sweep_runner.py --max-parallel 2
   ```

4. **Stuck Processes**
   ```bash
   # Kill and restart
   python sweep_monitor.py --kill
   ```

### Recovery Procedures

1. **Resume Interrupted Sweep**
   - Identify completed runs from results directory
   - Manually restart with remaining configurations
   - Use filters to exclude completed runs

2. **Handle Failed Runs**
   - Check error logs in `logs/` directory
   - Retry specific configurations manually
   - Investigate systematic failures

3. **Data Recovery**
   - Result files are saved immediately upon completion
   - Logs contain detailed execution information
   - Progress tracking survives interruptions

## Cost Estimation

### API Costs (Approximate)
- **Claude 3.5 Sonnet**: $0.50-2.00 per simulation
- **o4 Mini**: $0.10-0.50 per simulation  
- **o1 Models**: $1.00-5.00 per simulation
- **Open Source Models**: $0.05-0.20 per simulation

### Time Estimates
- **Simple run** (2 agents, 15 rounds): 5-15 minutes
- **Complex run** (20 agents, 15 rounds): 15-45 minutes
- **Full sweep** (180 configurations): 8-24 hours

### Resource Requirements
- **CPU**: 1 core per parallel job
- **Memory**: 1-2GB per simulation
- **Storage**: 10-50MB per result file
- **Network**: Depends on API provider

## Getting Help

1. **Check logs**: Always start with the log files
2. **Monitor processes**: Use `sweep_monitor.py` for real-time info
3. **Test configurations**: Use `--dry-run` and small subsets
4. **Resource monitoring**: Check system resources during runs

## Example Complete Workflow

```bash
# 1. Plan the sweep
python sweep_runner.py --models claude-3.5-sonnet --agents 2 5 --alphas 1.6 2.0 --dry-run

# 2. Start the sweep
python sweep_runner.py --models claude-3.5-sonnet --agents 2 5 --alphas 1.6 2.0 --max-parallel 2

# 3. Monitor progress (in another terminal)
python sweep_monitor.py --live

# 4. Generate report when complete
python sweep_monitor.py --report

# 5. Analyze results
python analyze_results.py  # Analyze individual files
python wandb_integration.py  # Upload to W&B if desired
```

This system provides a powerful platform for conducting comprehensive behavioral economics experiments with LLMs across multiple parameter dimensions.