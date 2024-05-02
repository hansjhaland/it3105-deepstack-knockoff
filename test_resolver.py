from game_manager import PokerGameManager
from state_manager import PokerStateManager
from poker_oracle import PokerOracle
from resolver import Resolver 
from card_deck import CardDeck
from neural_networks import NeuralNetwork

import time

use_limited_deck = True

poker_oracle = PokerOracle(use_limited_deck)
game_manager = PokerGameManager(use_limited_deck)
state_manager = PokerStateManager(game_manager.num_chips_bet, 
                                    game_manager.small_blind_chips, 
                                    game_manager.big_blind_chips, 
                                    game_manager.legal_num_raises_per_stage, 
                                    game_manager.use_limited_deck)
resolver = Resolver(state_manager, poker_oracle)

card_deck = CardDeck(use_limited_deck)
card_deck.shuffle()

game_manager.add_poker_agent("resolver", 100, "Acting")
game_manager.add_poker_agent("resolver", 100, "Other")

for player in game_manager.poker_agents:
    player.recieve_hole_cards(card_deck.deal(2))

acting_player = game_manager.poker_agents[0]

initital_strategy = resolver.get_initial_strategy()
initital_acting_ranges, initial_other_ranges = resolver.get_initial_ranges([], acting_player.hole_cards)


# MARK: Pre-flop to Flop    
start_time = time.time()
pre_flop_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                            players=game_manager.poker_agents, 
                                            public_cards=[], 
                                            pot=0, 
                                            num_raises_left=game_manager.legal_num_raises_per_stage, 
                                            bet_to_call=game_manager.current_bet,
                                            stage="pre-flop",
                                            initial_round_action_history=[],
                                            initial_depth=0,
                                            strategy_matrix=initital_strategy
                                            )
end_stage = "flop"
end_depth = 1
num_rollouts = 10
pre_flop_strategy = resolver.resolve(pre_flop_state, initital_acting_ranges, initial_other_ranges, end_stage, end_depth, num_rollouts)
print(pre_flop_strategy)
# NOTE: 2 - 4 seconds with 10 rollouts
print(f"Finished resolving form pre-flop to flop in {time.time() - start_time:.3f} seconds.")
print()


# MARK: Flop to Turn
start_time = time.time()
public_cards = card_deck.deal(3)
flop_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                            players=game_manager.poker_agents, 
                                            public_cards=public_cards, 
                                            pot=0, 
                                            num_raises_left=game_manager.legal_num_raises_per_stage, 
                                            bet_to_call=game_manager.current_bet,
                                            stage="flop",
                                            initial_round_action_history=[],
                                            initial_depth=0,
                                            strategy_matrix=initital_strategy
                                            )
end_stage = "turn"
end_depth = 1
flop_strategy = resolver.resolve(flop_state, initital_acting_ranges, initial_other_ranges, end_stage, end_depth, num_rollouts)
print(flop_strategy)
# NOTE: 2 - 4 seconds with 10 rollouts
print(f"Finished resolving form flop to turn in {time.time() - start_time:.3f} seconds.")
print()


# MARK: Turn to River
start_time = time.time()
public_cards = [*public_cards, *card_deck.deal(1)]
turn_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                            players=game_manager.poker_agents, 
                                            public_cards=public_cards, 
                                            pot=0, 
                                            num_raises_left=game_manager.legal_num_raises_per_stage, 
                                            bet_to_call=game_manager.current_bet,
                                            stage="turn",
                                            initial_round_action_history=[],
                                            initial_depth=0,
                                            strategy_matrix=initital_strategy
                                            )
end_stage = "river"
end_depth = 1
turn_strategy = resolver.resolve(turn_state, initital_acting_ranges, initial_other_ranges, end_stage, end_depth, num_rollouts)
print(turn_strategy)
# NOTE: 2 - 4 seconds with 10 rollouts
print(f"Finished resolving form turn to river in {time.time() - start_time:.3f} seconds.")
print()


# MARK: River to Showdown
start_time = time.time()
public_cards = [*public_cards, *card_deck.deal(1)]
river_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                            players=game_manager.poker_agents, 
                                            public_cards=public_cards, 
                                            pot=0, 
                                            num_raises_left=game_manager.legal_num_raises_per_stage, 
                                            bet_to_call=game_manager.current_bet,
                                            stage="river",
                                            initial_round_action_history=[],
                                            initial_depth=0,
                                            strategy_matrix=initital_strategy
                                            )
end_stage = "showdown"
end_depth = 1
num_rollouts = 1 # NOTE: Decreased number of rollouts
river_strategy = resolver.resolve(river_state, initital_acting_ranges, initial_other_ranges, end_stage, end_depth, num_rollouts)
print(river_strategy)
# NOTE: 351 seconds (almost 6 minutes) with 10 rollouts, 26 - 33 seconds with 1 rollout
print(f"Finished resolving form river to showdown in {time.time() - start_time:.3f} seconds.")
print()
