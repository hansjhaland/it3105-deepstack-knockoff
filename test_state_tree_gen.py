from game_manager import PokerGameManager
from state_manager import PokerStateManager
from card_deck import CardDeck

game_manager = PokerGameManager()
# NOTE: Recursion error for more than two players. 
# This should be fine since trees are only relevant for resolver, which only works for two players.
game_manager.add_poker_agent("rollout", 100, "Bob")
game_manager.add_poker_agent("rollout", 100, "Alice")

state_manager = PokerStateManager(game_manager.num_chips_bet, 
                                    game_manager.small_blind_chips, 
                                    game_manager.big_blind_chips, 
                                    game_manager.legal_num_raises_per_stage, 
                                    game_manager.use_limited_deck)

card_deck = CardDeck()
for player in game_manager.poker_agents:
    player.recieve_hole_cards(card_deck.deal(2))
    
# MARK: Pre-flop to flop   
pre_flop_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                players=game_manager.poker_agents, 
                                                public_cards=[], 
                                                pot=0, 
                                                num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                bet_to_call=game_manager.current_bet,
                                                stage="pre-flop",
                                                initial_round_action_history=[],
                                                initial_depth=0
                                                )

state_manager.generate_subtree_to_given_stage_and_depth(pre_flop_state, 
                                                        end_stage="flop", 
                                                        end_depth=1)


# MARK: Flop to turn
public_cards = card_deck.deal(3)
flop_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                players=game_manager.poker_agents, 
                                                public_cards=public_cards, 
                                                pot=0, 
                                                num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                bet_to_call=game_manager.current_bet,
                                                stage="flop",
                                                initial_round_action_history=[],
                                                initial_depth=0
                                                )

state_manager.generate_subtree_to_given_stage_and_depth(flop_state, 
                                                        end_stage="turn", 
                                                        end_depth=1)


# MARK: Turn to river
public_cards = [*public_cards, *card_deck.deal(1)]
turn_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                players=game_manager.poker_agents, 
                                                public_cards=public_cards, 
                                                pot=0, 
                                                num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                bet_to_call=game_manager.current_bet,
                                                stage="turn",
                                                initial_round_action_history=[],
                                                initial_depth=0
                                                )

state_manager.generate_subtree_to_given_stage_and_depth(turn_state, 
                                                        end_stage="river", 
                                                        end_depth=1)


# MARK: River to showdoen
public_cards = [*public_cards, *card_deck.deal(1)]
river_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                players=game_manager.poker_agents, 
                                                public_cards=public_cards, 
                                                pot=0, 
                                                num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                bet_to_call=game_manager.current_bet,
                                                stage="river",
                                                initial_round_action_history=[],
                                                initial_depth=0
                                                )

state_manager.generate_subtree_to_given_stage_and_depth(river_state, 
                                                        end_stage="showdown", 
                                                        end_depth=1)


# MARK: Print "trees"
print("Pre-flop")
PokerStateManager.iterative_print_subtree(pre_flop_state)
print()
print("Flop")
PokerStateManager.iterative_print_subtree(flop_state)
print()
print("Turn")
PokerStateManager.iterative_print_subtree(turn_state)
print()
print("River")
PokerStateManager.iterative_print_subtree(river_state)
print()