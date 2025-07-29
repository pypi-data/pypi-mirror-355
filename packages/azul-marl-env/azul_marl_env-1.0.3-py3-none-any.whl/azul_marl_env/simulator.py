from azul_env import AzulEnv
import time
import random

env = AzulEnv(player_count=2)

state, info = env.reset()

# Render initial state
print("Initial state:")
env.render()
print(f"Valid moves for starting player: {len(info.get('valid_moves', []))}")
time.sleep(2)  # Give time for the plot to display

step_count = 0
for agent in env.agent_iter():
    observation, reward, termination, truncation, info = env.last()
    if termination or truncation:
        break
    
    # Get valid moves from info
    valid_moves = info.get('valid_moves')
    print(valid_moves)
    
    if valid_moves:
        # Pick a random valid move
        action = random.choice(valid_moves)
        print(f"Step {step_count}: Agent {agent} taking valid action {action} from {len(valid_moves)} valid moves")
    else:
        # Fallback to random action if no valid moves (shouldn't happen)
        action = env.action_space(agent).sample()
        print(f"Step {step_count}: Agent {agent} taking random action {action} (no valid moves found)")
        print(f"DEBUG: valid_moves was {valid_moves}")
    
    env.step(action)
    
    # Render after step to show updated state
    env.render()
    step_count += 1
    time.sleep(0.1)  # Give time for the plot to display

print("Simulation completed!")
print(f"Total steps: {step_count}")
print(f"Final scores: {[player['score'] for player in env.state['players']]}")
env.close()