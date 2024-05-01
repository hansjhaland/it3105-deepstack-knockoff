from game_manager import PokerGameManager
from neural_networks import NeuralNetwork

use_limited_deck = True
    
game_manager = PokerGameManager(use_limited_deck=use_limited_deck)

game_manager.add_poker_agent("combination", 30, "Alex")
game_manager.add_poker_agent("combination", 30, "Bob")


manage_per_hand = True

game_manager.run_one_game(manage_per_hand)