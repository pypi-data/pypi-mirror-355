# AzulMARL

[![codecov](https://codecov.io/gh/AzulImplementation/AzulMARL/branch/main/graph/badge.svg)](https://codecov.io/gh/AzulImplementation/AzulMARL)
[![PyPI version](https://badge.fury.io/py/ParkingLotGym.svg)](https://pypi.org/project/parkinglotgym/)

PettingZoo AI env for Azul multiplayer board game to enable AI agent training.

![AzulRendering](images/azul_rendering.gif)

## Most important libraries used

- [![GitHub](https://img.shields.io/badge/GitHub-AzulImplementation/AzulGameEngine-black?style=flat&logo=github)](https://github.com/AzulImplementation/AzulGameEngine)
- [![GitHub](https://img.shields.io/badge/GitHub-Farama-Foundation/PettingZoo-black?style=flat&logo=github)](https://github.com/Farama-Foundation/PettingZoo)

## Usage

### Initiating the env via PettingZoo

```python
from azul_marl_env import azul_v1_2players, azul_v1_3players, azul_v1_4players

env_2players = azul_v1_2players()
env_3players = azul_v1_3players()
env_4players = azul_v1_4players()

env_2players_custom_max_moves = azul_v1_2players(max_moves=100)
```

### Initiating the env directly

```python
from azul_marl_env import AzulEnv

env = AzulEnv(player_count=2)
env = AzulEnv(player_count=3)
env = AzulEnv(player_count=4) 

env = AzulEnv(player_count=2, max_moves=100)
```

### Making moves

```python
from azul_marl_env import azul_v1_2players
import random

# Create and reset the environment
env = azul_v1_2players()
observation, info = env.reset()

for agent in env.agent_iter():
    valid_moves = info["valid_moves"]
    action = random.choice(valid_moves)
    # Execute the move
    observation, reward, terminated, truncated, info = env.step(action)
    # Render the environment
    env.render()
    if terminated or truncated:
        break

env.close()
```

### Example of a complete game using random valid moves

```python
from azul_marl_env import azul_v1_2players
import random

def play_random_game():
    env = azul_v1_2players()
    observation, info = env.reset()
    
    for agent in env.agent_iter():
        valid_moves = info["valid_moves"]            
        action = random.choice(valid_moves)
        observation, reward, terminated, truncated, info = env.step(action)
        
        if terminated or truncated:
            print(f"Game finished! Final scores: {[player['score'] for player in observation['players']]}")
            break
    
    env.close()

play_random_game()
```

## Environment Details
    
    Factory count (num_factories):
    - 2 player game -> 5
    - 3 player game -> 7
    - 4 player game -> 9

- **Action Space**: MultiDiscrete([num_factories + 1, 5, 20, 5])
  - First value: Factory index. Index 0 is taken for the center so the factory indexes are: 0 based factory index + 1.
  - Second value: Tile color (0-4 representing different colors)
  - Third value: Number of tiles to place on floor (0-19)
  - Fourth value: Pattern line index (0-4)

- **Observation Space**: Dictionary containing:
  - `factories`: Box(0, 4, (num_factories, 5), int32) - Tile counts in each factory
  - `center`: Box(0, 3 * num_factories, (5,), int32) - Tile counts in center
  - `players`: Tuple of player states, each containing:
    - `pattern_lines`: Box(0, 5, (5, 5), int32) - Current pattern lines
    - `wall`: Box(0, 5, (5, 5), int32) - Wall state
    - `floor`: Box(0, 5, (7,), int32) - Floor tiles
    - `is_starting`: Discrete(2) - First player marker
    - `score`: Discrete(241) - Player's score
  - `bag`: Box(0, 100, (5,), int32) - Remaining tiles in bag
  - `lid`: Box(0, 100, (5,), int32) - Discarded tiles

- **Reward**: 
  - `-1` for each step until game end
  - `-2` for invalid moves
  - Final Azul score is added to cumulative reward at game end

- **Done**: `True` when:
  - Game is completed (at least one player filled at least one horizontal wall)
  - `False` otherwise

  - **Truncated**: `True` when:
  - Maximum moves reached (player_count * 150 by default)
  - `False` otherwise

- **Info**: Contains `valid_moves` list for the current player