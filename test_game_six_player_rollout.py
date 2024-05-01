from game_manager import PokerGameManager

use_limited_deck = True
    
game_manager = PokerGameManager(use_limited_deck=use_limited_deck)

game_manager.add_poker_agent("rollout", 30, "Alex")
game_manager.add_poker_agent("rollout", 30, "Bob")
game_manager.add_poker_agent("rollout", 30, "Chris")
game_manager.add_poker_agent("rollout", 30, "Dave")
game_manager.add_poker_agent("rollout", 30, "Eric")
game_manager.add_poker_agent("rollout", 30, "Fred")

manage_per_hand = True

game_manager.run_one_game(manage_per_hand)