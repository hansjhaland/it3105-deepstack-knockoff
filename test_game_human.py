from game_manager import PokerGameManager

use_limited_deck = True
    
game_manager = PokerGameManager(use_limited_deck=use_limited_deck)

game_manager.add_poker_agent("human", 30, "Player 1")
game_manager.add_poker_agent("human", 30, "Player 2")

manage_per_hand = False

game_manager.run_one_game(manage_per_hand)