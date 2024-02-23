class PokerGameManager:
    
    def __init__(self):
        self.poker_agents = []
        self.pot = 0
    
    # NOTE: Based on "Generate Poker Agents" from slides
    def add_poker_agent(self, agent_type: str, chips: int) -> None:
        poker_agent = PokerAgent(agent_type, chips)
        self.poker_agents.append(poker_agent)
    
    # NOTE: Based on "Manage Game" from slides
    def run_one_game():
        pass
    
    def prepare_new_game(self, keep_players: bool):
        if not keep_players:
            self.poker_agents = []
        self.pot = 0
    
    # NOTE: Based on "Monitor Players" from slides
    def monitor_players():
        pass
    
    # NOTE: Based on "Texas Hold'em Simulator" from slides
    def texas_holdem_simulator(self, num_players: int, num_games: int):
        pass
    
# TODO: Maybe create different agent objects for each type. Resolver, Rollout, Combination, Human
class PokerAgent:
    def __init__(self, type: str, initial_chips: int):
        self.type = type
        self.chips = initial_chips