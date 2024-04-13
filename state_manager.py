import sys
from card_deck import CardDeck
from game_manager import PokerGameManager
import copy

# NOTE: Starting with two-player case only
class PokerStateManager:

    def __init__(self, game_manager: PokerGameManager):
        # NOTE: Setting same rules as the game manager
        self.num_chips_bet = game_manager.num_chips_bet
        self.small_blind_chips = game_manager.small_blind_chips
        self.big_blind_chips = game_manager.big_blind_chips
        self.legal_num_raises_per_stage = game_manager.legal_num_raises_per_stage
        
        self.use_limited_deck = game_manager.use_limited_deck
        
        self.max_num_events = 1 # NOTE: Arbitrary number
        
        
    def generate_root_state(self, acting_player, players, public_cards, pot, num_raises_left, bet_to_call, stage, initial_round_action_history, initial_depth):
        return PlayerState(acting_player, players, acting_player, public_cards, pot, num_raises_left, bet_to_call, stage, "root", initial_round_action_history, initial_depth)
    
    
    def generate_child_state_from_action(self, state, action):
        # Verify that child state for action has not already been generated
        if isinstance(state, TerminalState):
        # NOTE: Cannot generate child states from terminal state
            return None, None            
        
        if self.already_generated_state(state, action):
            return None, None
        action_to_generated_state = action
        if action == "raise":
            player = state.current_state_acting_player
            players = state.players
            current_bet = state.bet_to_call
            bet_amount, action, num_raises_left, players = PokerGameManager.handle_raise(player, state.num_raises_left, current_bet, self.num_chips_bet, players,)
            # If action is set to something else than raise, then the code will continue to the next apropriate "first level" if statement
            if action == "raise":
                action_to_generated_state = action
                pot = state.pot + bet_amount
                bet_to_call = player.current_bet + bet_amount
                next_index = (players.index(player) + 1) % len(players)
                next_player = players[next_index]
                if self.begin_new_round(players, state.round_action_history):
                    # print("NEW ROUND", state.round_action_history)
                    updated_round_history = [action]
                else:
                    updated_round_history = [*state.round_action_history, action]
                new_depth = state.depth + 1
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, pot, num_raises_left, bet_to_call, state.stage, action_to_generated_state, updated_round_history, new_depth)
        if self.already_generated_state(state, action):
            return None, None
        if action == "call": 
            player = state.current_state_acting_player
            players = state.players
            current_bet = state.bet_to_call
            bet_amount, action, players = PokerGameManager.handle_call(player, current_bet, players)
            if action == "call":
                action_to_generated_state = action
                pot = state.pot + bet_amount
                next_index = (players.index(player) + 1) % len(players)
                next_player = players[next_index]
                if self.begin_new_round(players, state.round_action_history):
                    # print("NEW ROUND", state.round_action_history)
                    updated_round_history = [action]
                else:
                    updated_round_history = [*state.round_action_history, action]
                new_depth = state.depth + 1
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, pot, state.num_raises_left, state.bet_to_call, state.stage, action_to_generated_state, updated_round_history, new_depth)
        if self.already_generated_state(state, action):
            return None, None
        if action == "fold": 
            # Fold always result in terminal state
            state_copy = copy.deepcopy(state)
            player = state_copy.current_state_acting_player
            players = state_copy.players.copy()
            next_index = (players.index(player) + 1) % len(players)
            next_player = players[next_index]
            action_to_generated_state, players = PokerGameManager.handle_fold(player, players)
            if player == state.acting_player:
                child_state = TerminalState(player, players, state_copy.pot, action_to_generated_state, state.depth+1, state.stage)
            else:
                if self.begin_new_round(players, state_copy.round_action_history):
                    # print("NEW ROUND", state.round_action_history)
                    updated_round_history = [action]
                else:
                    updated_round_history = [*state_copy.round_action_history, action]
                new_depth = state.depth + 1
                if len(players) == 1: # Acting player has won
                    child_state = TerminalState(player, players, state_copy.pot, action_to_generated_state, state.depth+1, state.stage)
                else:
                    print("HERE") #NOTE: Never gets here with two players
                    child_state = PlayerState(state_copy.acting_player, players, next_player, state_copy.public_cards, state_copy.pot, state_copy.num_raises_left, state_copy.bet_to_call, state_copy.stage, action_to_generated_state, updated_round_history, new_depth)
        return child_state, action_to_generated_state
    
    def begin_new_round(self, players, round_history):
        return len(players) == len(round_history)
            
    def already_generated_state(self, state, action) -> bool:
        for child in state.children:
            if child.origin_action == action:
                return True
        return False
    
    
    @staticmethod
    def get_child_state_by_action(state, action):
        for child in state.children:
            if child.origin_action == action:
                return child
        return None # Returns None if action is invalid from state and therefore no child
    
    # NOTE: Only considers PLAYER STATES
    def generate_all_child_states(self, state, end_stage, end_depth):
        # if state.stage == end_stage and state.depth >= end_depth:
        #     return
        for action in ["fold", "call", "raise"]:
            child_state, _ = self.generate_child_state_from_action(state, action)
            if child_state is not None:
                state.children.append(child_state)
    
    
    def generate_subtree_to_given_stage_and_depth(self, state, end_stage, end_depth):
        stage_dict = {"pre-flop": 0,
                      "flop": 1,
                      "turn": 2,
                      "river": 3,
                      "showdown": 4}
        
        
        if isinstance(state, TerminalState):
            return
        
        if len(state.players) == 1:
            return
        
        # if state.stage == end_stage and state.depth == end_depth:
        #     return
        
        if stage_dict[state.stage] >= stage_dict[end_stage] and state.depth >= end_depth:
            return
        
        next_state_type = self.determine_next_state_type(state)
        
        # print(state.stage, state.depth, next_state_type)
        
        if next_state_type == "PLAYER":
            self.generate_all_child_states(state, end_stage, end_depth)
            for child in state.children:
                self.generate_subtree_to_given_stage_and_depth(child, end_stage, end_depth)
            
        if next_state_type == "CHANCE":
            chance_state = self.get_chance_state_with_event_children(state)
            state.children.append(chance_state)
            for child in chance_state.children: # Player state is stored in each event/child
                # print(type(child.player_state))
                # print("STAGE IS", child.player_state.stage)
                # NOTE: The second level chance node, i.e. event node, has only one child which is the next player state
                self.generate_subtree_to_given_stage_and_depth(child.children[0], end_stage, end_depth)
                
        if next_state_type == "SHOWDOWN":
            self.get_all_showdown_outcomes(state)
                
        return
        
    def get_all_showdown_outcomes(self, state):
        for player in state.players:
            result_state = TerminalState(state.acting_player, state.players, state.pot, "showdown", state.depth+1, stage="showdown", winner=player)
            state.children.append(result_state)
        tie_state = TerminalState(state.acting_player, state.players, state.pot/2, "showdown", state.depth+1, stage="showdown", winner=None)
        state.children.append(tie_state)
        
    def determine_next_state_type(self, state):
        # NOTE: Next state is chance node if current state is end of stage
        
        round_history = state.round_action_history
        # num_players_in_round: int = len(state.players)
        # print(len(state.players), state.depth)
        # current_round_index = num_players_in_round + (state.depth % num_players_in_round)
        # current_round_history = round_history[-current_round_index:]
        
        # is_end_of_stage = PokerGameManager.can_go_to_next_stage(current_round_history)
        
        # print(round_history)
        is_end_of_stage = PokerGameManager.can_go_to_next_stage(round_history)
        
        if is_end_of_stage:
            if state.stage == "river":
                return "SHOWDOWN"
            return "CHANCE"
        return "PLAYER"
    
    
    def get_chance_state_with_event_children(self, state):
        cards_to_exclude = []
        for player in state.players:
            if state.public_cards == []:
                cards_to_exclude = [*player.hole_cards]
            else:
                cards_to_exclude = [*cards_to_exclude, *player.hole_cards]
        card_deck = CardDeck(limited=self.use_limited_deck)
        card_deck.exclude(cards_to_exclude)
        card_deck.shuffle()
        
        
        next_stage = PokerGameManager.get_next_stage(state.stage)
        
        chance_state = ChanceState(card_deck, next_stage, self.max_num_events, state, [])
        
        num_public_cards_to_draw = 3 if next_stage == "flop" else 1
        
        for _ in range(self.max_num_events):
            event_card_deck = copy.deepcopy(card_deck)
            new_public_cards = event_card_deck.deal(num_public_cards_to_draw)
            card_deck.exclude(new_public_cards)
        
            event_state: PlayerState = copy.deepcopy(state)
            # NOTE: Depth referrs to the depth WITHIN a stage. Since a chance node initiates a new stage, the depth should be set to 0.
            event_state.depth = 0
            event_state.round_action_history = []
            event_public_cards = [*state.public_cards, *new_public_cards]
            event_state.stage = next_stage
            event_state.public_cards = event_public_cards
            event_state.num_raises_left = self.legal_num_raises_per_stage
            
            chance_event = ChanceState(event_card_deck, next_stage, self.max_num_events, event_state, new_public_cards)
            chance_event.children.append(event_state)  
            
            chance_state.children.append(chance_event)
            
        return chance_state
    
    
    # TODO: FROM RESOLVER EXPLAINATION IN TASK DESCRIPTION: NEED TO GENERATE A COMPLETE SUBTREE TO A PRE-DEFINED DEPTH OF A STAGE!
    
    # TODO: Add "showdown" classification for state
    
    # TODO: SIMPLIFICATION FOR CHANCE NODES: HARD LIMIT ON NUMBER RANDOM EVENTS THAT CAN BE PERFORMED ON A CHANCE NODE.
    # EACH CHILD IS ASSOCIATED WITH A DIFFERENT PUBLIC CARD (OR CARDS IN CASE FOR THE FLOP STAGE)
    
    
class PlayerState:
    # TODO: Consider removing default values, cause more confusion than help i think
    def __init__(self, acting_player, players, current_state_acting_player, public_cards, pot, num_raises_left, bet_to_call, stage, origin_action, round_action_history, depth):
        self.acting_player = acting_player
        self.players = players
        self.current_state_acting_player = current_state_acting_player
        self.public_cards = public_cards
        self.pot = pot
        self.num_raises_left = num_raises_left
        self.bet_to_call = bet_to_call
        self.stage = stage
        self.winner = None
        
        self.depth = depth
        
        self.round_action_history = round_action_history
        self.origin_action = origin_action
        self.children = []
        
        
class ChanceState:
    
    def __init__(self, card_deck, stage, max_num_events, player_state, event):
        self.card_deck = card_deck
        self.stage = stage
        self.player_state = player_state
        self.event = event # NOTE: Event is list of public cards that was drawn from card deck. Empty list indicates "initial" chance state
        
        self.max_num_events = max_num_events # One event corresponds to one public card being drawn (or one set of three cards for the flop)
        
        self.children = [] # Children will modify the public cards and stage of the player_state
        
        
class TerminalState:
    
    def __init__(self, acting_player, players, pot, origin_action, depth, stage, winner = None):
        self.acting_player = acting_player
        self.players = players
        self.pot = pot
        self.winner = winner
        self.payouts = {}
        
        self.origin_action = origin_action
        self.depth = depth
        self.stage = stage
        self.children = []
        
        
if __name__ == "__main__":
    game_manager = PokerGameManager()
    game_manager.add_poker_agent("rollout", 100, "Bob")
    game_manager.add_poker_agent("rollout", 100, "Alice")
    # game_manager.add_poker_agent("rollout", 100, "Chris") # NOTE: Recursion error for three players
    card_deck = CardDeck()
    for player in game_manager.poker_agents:
        player.recieve_hole_cards(card_deck.deal(2))
    
    state_manager = PokerStateManager(game_manager)
    
    root_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                   players=game_manager.poker_agents, 
                                                   public_cards=[], 
                                                   pot=0, 
                                                   num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                   bet_to_call=game_manager.current_bet,
                                                   stage="pre-flop",
                                                   initial_round_action_history=[],
                                                   initial_depth=0
                                                   )
    
    # TODO: Works for end_stage="pre-flop" and depth = 0 OR 1.
    # For some reason the tree reaches beyond the limit in subtree method...
    state_manager.generate_subtree_to_given_stage_and_depth(root_state, 
                                                            end_stage="pre-flop", 
                                                            end_depth=2)
    
    def print_subtree(state, depth = 0):
        for child in state.children:
            if isinstance(child, PlayerState):
                print("PLAYER", child.origin_action, child.depth, child.stage)
                # print("PLAYER", child.origin_action, depth, child.stage)
            if isinstance(child, TerminalState):
                print("TERMINAL", child.origin_action, child.depth, child.stage)
                # print("TERMINAL", child.origin_action, depth, child.stage)
            if isinstance(child, ChanceState):
                print("CHANCE", child.event, child.player_state.depth, child.stage, child.player_state.stage)
                # print("CHANCE", child.event, depth, child.stage, child.player_state.stage)
            print_subtree(child, depth + 1)
            
    print_subtree(root_state)
    
    # def get_all_children(state, depth=0):
    #     for child in state.children:
    #         # if depth == 5:
    #         #     return
    #         if isinstance(child, PlayerState):
    #             print(child.origin_action, depth)
    #         if isinstance(child, ChanceState):
    #             print(child.event, depth)
    #         state_manager.generate_all_child_states(child)
    #         get_all_children(child, depth + 1)
    
    # get_all_children(root_state)
    