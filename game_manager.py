from poker_oracle import PokerOracle
from card_deck import Card

class PokerGameManager:
    
    def __init__(self):
        self.poker_agents: list[PokerAgent] = []
        self.pot = 0
        self.current_bet = 0
        self.poker_oracle = PokerOracle()
        self.public_cards: list[Card] = []
        self.num_chips_bet = 2
        self.small_blind_player: PokerAgent = None
        self.small_blind_chips: int = self.num_chips_bet / 2
        self.big_blind_player: PokerAgent = None
        self.big_blind_chips: int = self.num_chips_bet
        self.small_blind_player_index = 0 # Needs to "rotate" with modulo operation
    
    # NOTE: Based on "Generate Poker Agents" from slides
    def add_poker_agent(self, agent_type: str, chips: int) -> None:
        poker_agent = PokerAgent(agent_type, chips)
        self.poker_agents.append(poker_agent)
    
    # NOTE: Based on "Manage Game" from slides
    def run_one_game(self):
        # Assumes two or more players
        remaining_players = self.poker_agents
        is_first_hand = True
        while len(remaining_players) > 1:
            legal_num_raises_per_hand = 2 # To shorten each hand
            # Reset deck of cards
            card_deck = self.poker_oracle.get_deck_of_cards()
            
            # Shuffle deck
            card_deck.shuffle()
            
            # Deal out hole cards to each player
            for player in remaining_players:
                player.recieve_hole_cards(card_deck.deal(2))
            
            # TODO: MAY BE BETTER TO DECIDE PLAYER ORDER AT START OF EACH HAND BASED ON REMAINING PLAYER
            # WHERE SMALL BLIND IS FIRST PLAYER, BIG BLIND IS SECOND PLAYER, etc
        
            self.small_blind_player = self.poker_agents[self.small_blind_player_index]
            big_blind_player_index = (self.small_blind_player_index + 1) % len(remaining_players) 
            self.big_blind_player = self.poker_agents[big_blind_player_index]
            # Prepare which player should be next small blind. 
            # NOTE: May need to handle this differently when more than 2 player play and one player run out of chips
            self.small_blind_player_index = big_blind_player_index
            
            self.pot += self.small_blind_player.bet(self.small_blind_chips)
            self.pot += self.big_blind_player.bet(self.big_blind_chips)
            
            self.current_bet = self.big_blind_player.current_bet
        
            for player in remaining_players:
                
                pass
    

            
            if not is_first_hand:
            # Deal out public card
                self.public_cards = card_deck.deal(1)
        pass
    
    def prepare_new_game(self, keep_players: bool):
        if not keep_players:
            self.poker_agents = []
        self.pot = 0
        self.public_cards = []
        
    def set_small_blind_chips(self, num_chips: int):
        self.small_blind_chips = num_chips
        
    def set_big_blind_chips(self, num_chips: int):
        self.big_blind_chips = num_chips
    
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
        self.num_chips = initial_chips
        self.hole_cards: list[Card] = None
        self.current_bet = 0
        
    def recieve_hole_cards(self, hole_cards: list[Card]):
        self.hole_cards = hole_cards
        
    def bet(self, num_chips: int) -> int:
        self.current_bet = num_chips
        self.num_chips -= num_chips
        
        return self.current_bet
    
    # Implementing get action for a pure rollout based agent
    def get_action(self, public_cards: list[Card], num_opponents: int, rollout_count: int, poker_oracle: PokerOracle) -> str:
        # TODO: Should get probabilities from a pre-generated (and preferably saved) cheat sheet
        win_probability = poker_oracle.rollout_hole_pair_evaluator(self.hole_cards, public_cards, num_opponents, rollout_count)
        if win_probability >= 0.95:
            return "all-in"
        if win_probability >= 0.7:
            return "raise"
        if win_probability >= 0.4:
            return "call"
        else:
            return "fold" 