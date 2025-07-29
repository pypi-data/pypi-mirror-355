from azul_marl_env.azul_env import AzulEnv

def env(**kwargs):
    return AzulEnv(**kwargs)

def azul_v1_2players(max_moves=None):
    return env(player_count=2, max_moves=max_moves)

def azul_v1_3players(max_moves=None):
    return env(player_count=3, max_moves=max_moves)

def azul_v1_4players(max_moves=None):
    return env(player_count=4, max_moves=max_moves)