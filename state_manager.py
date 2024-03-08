
from game_manager import PokerGameManager

# NOTE: Starting with two-player case only
class PokerStateManager:

    def __init__(self, game_manager: PokerGameManager):
        # NOTE: Setting same rules as the game manager
        self.num_chips_bet = game_manager.num_chips_bet
        self.small_blind_chips = game_manager.small_blind_chips
        self.big_blind_chips = game_manager.big_blind_chips
        self.legal_num_raises_per_stage = game_manager.legal_num_raises_per_stage
        
        # In general, nodes are of type "perspective", "opponent", "chance", "end".

    # NOTE: To be used as root node in Resolver
    def generate_root_state(self, perspective_player, players, public_cards, pot, num_raises, bet_to_call):
        return State(perspective_player, players, public_cards, pot, num_raises, bet_to_call)
    
    def generate_child_state_from_action(self, state, action):
        pass
    
    def generate_all_child_states(self, state):
        pass
    
    
class State:
    
    def __init__(self, perspective_player, players, public_cards, pot, num_raises, bet_to_call):
        self.perspective_player = perspective_player
        self.players = players
        self.public_cards = public_cards
        self.pot = pot
        self.num_raises = num_raises
        self.bet_to_call = bet_to_call
        
        self.children = []