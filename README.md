# LLM Cooperation Simulation Framework

This repository contains code for simulating and analyzing cooperation between Large Language Model (LLM) agents in a public goods game with institutional choice. The framework allows evaluating how different LLM architectures navigate social dilemmas, balance self-interest with collective welfare, and utilize norm enforcement mechanisms.

## Repository Structure

The codebase consists of the following key components:

- **Core Simulation Files**:
  - `agent.py`: Implements the Agent class representing simulation participants
  - `environment.py`: Manages the game environment and round progression
  - `institution.py`: Defines the Sanctioning and Sanction-Free institutions
  - `parameters.py`: Contains all configurable simulation parameters
  - `main.py`: Entry point for running the simulation

- **API Client Files**:
  - `azure_openai_client.py`: Client for Azure OpenAI API
  - `openai_client.py`: Client for OpenAI API
  - `openrouter_client.py`: Client for OpenRouter API
  - `kluster_ai_client.py`: Client for KlusterAI API (referenced but not included)

- **Analysis Files**:
  - `paste.txt`: Contains code for analyzing decision-making strategies in simulation results

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install openai pandas numpy matplotlib backoff tqdm
```

## Configuration

The simulation is configured through `parameters.py`, which contains the following key settings:

- `NUM_AGENTS`: Number of agents in the simulation (default: 7)
- `NUM_ROUNDS`: Number of rounds in the simulation (default: 15)
- `PUBLIC_GOOD_MULTIPLIER`: Multiplication factor for public good contributions (default: 1.6)
- `INITIAL_TOKENS`: Starting tokens for each agent (default: 1000)
- `ENDOWMENT_STAGE_1`: Tokens given to each agent per round (default: 20)
- `ENDOWMENT_STAGE_2`: Additional tokens for sanctioning (default: 20)
- `PUNISHMENT_EFFECT`: Impact of punishment on receiver (default: 3)
- `REWARD_EFFECT`: Impact of reward on receiver (default: 1)

## Usage

To run a simulation, execute the main script with appropriate parameters:

```bash
python main.py --api-provider azure --deployment-name MODEL_NAME --azure-endpoint ENDPOINT --num-rounds 15 --num-agents 7
```

### API Configuration

The simulation supports multiple API providers:

1. **Azure OpenAI**:
```bash
python main.py --api-provider azure --deployment-name YOUR_DEPLOYMENT --azure-endpoint YOUR_ENDPOINT
```

2. **OpenAI**:
```bash
python main.py --api-provider openai --model-name MODEL_NAME
```

3. **OpenRouter**:
```bash
python main.py --api-provider openrouter --model-name MODEL_NAME
```

4. **KlusterAI**:
```bash
python main.py --api-provider kluster --model-name MODEL_NAME
```

### Environment Variables

You can also configure API access via environment variables:
- Azure: `AZURE_API_KEY`, `AZURE_ENDPOINT`, `AZURE_DEPLOYMENT_NAME`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`
- OpenRouter: `OPENROUTER_API_KEY`
- KlusterAI: `KLUSTER_API_KEY`

## Output Data

Simulation results are saved as JSON files with the naming pattern:
```
simulation_results_{model_name}_{num_agents}agents_{num_rounds}rounds_{run_id}.json
```

Each file contains detailed data about agent decisions, including:
- Institution choices (SI vs. SFI) with reasoning
- Contribution amounts with reasoning
- Punishment/reward allocations with reasoning
- Payoffs for each round
- Cumulative statistics

## Analysis

The repository includes code for analyzing agent reasoning patterns:

1. Run the simulation to generate result files
2. Use the analysis code in `paste.txt` to classify reasoning strategies
3. Generate comparative visualizations between model architectures

The analysis classifies reasoning into categories including:
- Economic Reasoning (payoff maximization, Nash equilibrium, free-riding)
- Social Cooperation (cooperative arguments, social norms, reputation)
- Risk Management (risk aversion, complexity aversion)
- Control & Strategy (control-based reasoning, learning, status quo bias)

## Citation

If using this codebase for research, please cite our paper:


## License

This project is provided for research purposes.
