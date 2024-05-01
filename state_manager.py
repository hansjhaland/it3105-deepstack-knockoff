from card_deck import CardDeck, Card
import copy
import numpy as np

# MARK: PlayerState
class PlayerState:
    def __init__(self, acting_player, players, current_state_acting_player, public_cards: Card, pot: int, num_raises_left: int, 
                 bet_to_call: int, stage: str, origin_action: str, round_action_history: list[str], depth: int, strategy_matrix: np.ndarray | None):
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
        
        self._strategy_matrix = strategy_matrix
        # NOTE: Assume cumulative and positive regret has 
        # same "shape" as strategy matrix, but with 
        # 0 as initial values
        if strategy_matrix is None:
            self.cumulative_regret = None
            self.positive_regret = None
        else:
            self.cumulative_regret = strategy_matrix * 0
            self.positive_regret = strategy_matrix * 0
        self.acting_player_evaluation = None
        self.other_player_evaluation = None
        
        self.round_action_history = round_action_history
        self.origin_action = origin_action
        self.children = []
        self.actions_to_children = []
        
    def set_strategy_matrix(self, strategy_matrix: np.ndarray):
        self._strategy_matrix = strategy_matrix
        
    def get_strategy_matrix(self):
        return self._strategy_matrix
     
     
# MARK: ChanceState        
class ChanceState:
    
    def __init__(self, card_deck: list[Card], stage: str, max_num_events: int, player_state: PlayerState, event: list[Card]):
        self.card_deck = card_deck
        self.stage = stage
        self.depth = 0
        # TODO: Should have depth of 0 in the new stage 
        self.player_state = player_state
        self.event = event # NOTE: Event is list of public cards that was drawn from card deck. Empty list indicates "initial" chance state
        
        self.max_num_events = max_num_events # One event corresponds to one public card being drawn (or one set of three cards for the flop)
        
        self.children = [] # Children will modify the public cards and stage of the player_state
        self.child_events = []
        
        
# MARK: TerminalState        
class TerminalState:
    
    def __init__(self, acting_player, players, pot: int, origin_action: str, depth: int, stage: str, winner = None):
        self.acting_player = acting_player
        self.players = players
        self.pot = pot
        self.winner = winner
        self.payouts = {}
        
        self.origin_action = origin_action
        self.depth = depth
        self.stage = stage
        self.children = []


# MARK: State manager
class PokerStateManager:

    def __init__(self, num_chips_bet: int, small_blind_chips: int, big_blind_chips: int, legal_num_raises_per_stage: int, use_limited_deck: bool):
        # NOTE: Setting same rules as the game manager
        self.num_chips_bet = num_chips_bet
        self.small_blind_chips = small_blind_chips
        self.big_blind_chips = big_blind_chips
        self.legal_num_raises_per_stage = legal_num_raises_per_stage
        
        self.use_limited_deck = use_limited_deck
        
        # NOTE: Arbitrary number
        self.max_num_events = 3 
        
    
# MARK: Tree generation

    def generate_root_state(self, acting_player, players, public_cards: list[Card], pot: int, num_raises_left: int, bet_to_call: int, 
                            stage: str, initial_round_action_history: list[str], initial_depth: int, strategy_matrix: np.ndarray | None = None):
        return PlayerState(acting_player, players, acting_player, public_cards, pot, num_raises_left, bet_to_call, stage, "root", initial_round_action_history, initial_depth, strategy_matrix)
    
    
    def generate_subtree_to_given_stage_and_depth(self, state: PlayerState | TerminalState, end_stage: str, end_depth: int):
        stage_dict = {"pre-flop": 0,
                      "flop": 1,
                      "turn": 2,
                      "river": 3,
                      "showdown": 4}
        
        if isinstance(state, TerminalState):
            return
        
        if len(state.players) == 1:
            return
        
        if stage_dict[state.stage] >= stage_dict[end_stage] and state.depth >= end_depth:
            return
        
        if stage_dict[state.stage] > stage_dict[end_stage]:
            return
        
        next_state_type = self.determine_next_state_type(state)
                
        if next_state_type == "PLAYER":
            self.generate_all_child_states(state)
            for child in state.children:
                self.generate_subtree_to_given_stage_and_depth(child, end_stage, end_depth)
            
        if next_state_type == "CHANCE":
            chance_state = self.get_chance_state_with_event_children(state)
            state.children.append(chance_state)
            for child in chance_state.children: # Player state is stored in each event/child
                # NOTE: The second level chance node, i.e. event node, has only one child which is the next player state
                self.generate_subtree_to_given_stage_and_depth(child.children[0], end_stage, end_depth)
                
        if next_state_type == "SHOWDOWN":
            showdown_state = PlayerState(state.acting_player, state.players, state.current_state_acting_player, 
                                         state.public_cards, state.pot, state.num_raises_left, state.bet_to_call, "showdown", 
                                         "call", state.round_action_history, state.depth+1, state.get_strategy_matrix())
            self.get_all_showdown_outcomes(showdown_state)
            state.actions_to_children.append("call") # NOTE: Assuming transition to showdown is preceded by call
            state.children.append(showdown_state)
                
        return
    
    
        # NOTE: Only considers PLAYER STATES
    def generate_all_child_states(self, state: PlayerState):
        for action in ["fold", "call", "raise"]:
            child_state, generated_action = self.generate_child_state_from_action(state, action)
            if child_state is not None and generated_action not in state.actions_to_children:
                state.children.append(child_state)
                state.actions_to_children.append(generated_action)
    
    
    def generate_child_state_from_action(self, state: PlayerState | TerminalState, action) -> tuple[PlayerState, str]:
        # Verify that child state for action has not already been generated
        if isinstance(state, TerminalState):
        # NOTE: Cannot generate child states from terminal state
            return None, None            
        
        if self.already_generated_state(state, action):
            return None, None
        action_to_generated_state = action
        if action == "raise":
            players = state.players
            player = state.current_state_acting_player
            current_bet = state.bet_to_call
            bet_amount, action, num_raises_left, players = PokerStateManager.handle_raise(player, state.num_raises_left, current_bet, self.num_chips_bet, players,)
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
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, pot, num_raises_left, bet_to_call, state.stage, action_to_generated_state, updated_round_history, new_depth, state.get_strategy_matrix())
        if self.already_generated_state(state, action):
            return None, None
        if action == "call": 
            player = state.current_state_acting_player
            players = state.players
            current_bet = state.bet_to_call
            bet_amount, action, players = PokerStateManager.handle_call(player, current_bet, players)
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
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, pot, state.num_raises_left, state.bet_to_call, state.stage, action_to_generated_state, updated_round_history, new_depth, state.get_strategy_matrix())
        if self.already_generated_state(state, action):
            return None, None
        if action == "fold": 
            # Fold always result in terminal state
            state_copy = copy.deepcopy(state)
            player = state_copy.current_state_acting_player
            players = state_copy.players.copy()
            next_index = (players.index(player) + 1) % len(players)
            next_player = players[next_index]
            action_to_generated_state, players = PokerStateManager.handle_fold(player, players)
            if player == state.acting_player:
                if self.begin_new_round(players, state_copy.round_action_history):
                    # print("NEW ROUND", state.round_action_history)
                    updated_round_history = [action]
                else:
                    updated_round_history = [*state_copy.round_action_history, action]
                new_depth = state.depth + 1
                # print("HERE !!!")
                # child_state = TerminalState(player, players, state_copy.pot, action_to_generated_state, state.depth+1, state.stage)
                child_state = PlayerState(state_copy.acting_player, players, next_player, state_copy.public_cards, state_copy.pot, state_copy.num_raises_left, state_copy.bet_to_call, state_copy.stage, action_to_generated_state, updated_round_history, new_depth, state.get_strategy_matrix())
            else:
                if self.begin_new_round(players, state_copy.round_action_history):
                    # print("NEW ROUND", state.round_action_history)
                    updated_round_history = [action]
                else:
                    updated_round_history = [*state_copy.round_action_history, action]
                new_depth = state.depth + 1
                if len(players) == 1: # Acting player has won
                    # print("HEEEEEEERE")
                    # child_state = TerminalState(player, players, state_copy.pot, action_to_generated_state, state.depth+1, state.stage)
                    child_state = PlayerState(state_copy.acting_player, players, next_player, state_copy.public_cards, state_copy.pot, state_copy.num_raises_left, state_copy.bet_to_call, state_copy.stage, action_to_generated_state, updated_round_history, new_depth, state.get_strategy_matrix())
                else:
                    print("HERE") #NOTE: Never gets here with two players
                    child_state = PlayerState(state_copy.acting_player, players, next_player, state_copy.public_cards, state_copy.pot, state_copy.num_raises_left, state_copy.bet_to_call, state_copy.stage, action_to_generated_state, updated_round_history, new_depth, state.get_strategy_matrix())
        return child_state, action_to_generated_state
    
    
    def get_chance_state_with_event_children(self, state: PlayerState) -> ChanceState:
        cards_to_exclude = []
        for player in state.players:
            if state.public_cards == []:
                cards_to_exclude = [*player.hole_cards]
            else:
                cards_to_exclude = [*cards_to_exclude, *player.hole_cards]
        card_deck = CardDeck(limited=self.use_limited_deck)
        card_deck.exclude(cards_to_exclude)
        card_deck.shuffle()
        
        next_stage = PokerStateManager.get_next_stage(state.stage)
        
        chance_state = ChanceState(card_deck, next_stage, self.max_num_events, state, [])
        
        num_public_cards_to_draw = 3 if next_stage == "flop" else 1
        
        for _ in range(self.max_num_events):
            event_card_deck = copy.deepcopy(card_deck)
            new_public_cards = event_card_deck.deal(num_public_cards_to_draw)
            card_deck.exclude(new_public_cards)
        
            event_state: PlayerState = copy.deepcopy(state)
            # NOTE: Depth refers to the depth WITHIN a stage. Since a chance node initiates a new stage, the depth should be set to 0.
            event_state.depth = 1
            event_state.round_action_history = []
            event_public_cards = [*state.public_cards, *new_public_cards]
            event_state.stage = next_stage
            event_state.public_cards = event_public_cards
            event_state.num_raises_left = self.legal_num_raises_per_stage
            
            chance_event = ChanceState(event_card_deck, next_stage, self.max_num_events, event_state, new_public_cards)
            chance_event.children.append(event_state)  
            
            chance_state.children.append(chance_event)
            chance_state.child_events.append(new_public_cards)
            
        return chance_state
    
    
    def get_all_showdown_outcomes(self, state: PlayerState):
        showdown_state = copy.deepcopy(state)
        showdown_state.origin_action = "showdown"
        showdown_state.stage = "showdown"
        state.children.append(showdown_state)
        for player in showdown_state.players:
            result_state = TerminalState(showdown_state.acting_player, showdown_state.players, showdown_state.pot, "showdown", showdown_state.depth+1, stage="showdown", winner=player)
            showdown_state.children.append(result_state)
        tie_state = TerminalState(showdown_state.acting_player, showdown_state.players, showdown_state.pot/2, "showdown", showdown_state.depth+1, stage="showdown", winner=None)
        showdown_state.children.append(tie_state)
    

# MARK: Helper methods

    def begin_new_round(self, players, round_history: list[str]) -> bool:
        return len(players) == len(round_history)
       
            
    def already_generated_state(self, state: PlayerState, action: str) -> bool:
        for child in state.children:
            if child.origin_action == action:
                return True
        return False
    
        
    def determine_next_state_type(self, state: PlayerState) -> str:
        # NOTE: Next state is chance node if current state is end of stage
        
        round_history = state.round_action_history
        is_end_of_stage = PokerStateManager.can_go_to_next_stage(round_history)
        
        if is_end_of_stage:
            if state.stage == "river":
                return "SHOWDOWN"
            return "CHANCE"
        return "PLAYER"
    
 
# MARK: Stateic methods
 
    @staticmethod
    def get_child_state_by_action(state: PlayerState, action: str) -> PlayerState | ChanceState | TerminalState | None:
        for child in state.children:
            if child.origin_action == action:
                return child
        return None # Returns None if action is invalid from state and therefore no child
   
    
    @staticmethod
    def get_player_state_after_event(chance_state: ChanceState, event: list[Card]) -> PlayerState:
        for possible_state in chance_state.children:
            if possible_state.event == event:
                preceding_player_state = possible_state.children[0]
                return preceding_player_state
            
    @staticmethod
    def can_go_to_next_stage(round_actions: list[str]) -> bool:
        action_counts = {"fold": 0, "call": 0, "raise": 0}
        if len(round_actions) == 0:
            return False
        for action in round_actions:
            action_counts[action] += 1
        if action_counts["raise"] > 0:
            return False
        if action_counts["fold"] + action_counts["call"] == len(round_actions):
            return True
        return False # NOTE: Should not end up here! 
    
    @staticmethod
    def get_next_stage(current_stage: str) -> str:
        # NOTE: Currently handles only one "round", not the beginning of a new round
        if current_stage == "pre-flop":
            return "flop"
        elif current_stage == "flop":
            return "turn"
        elif current_stage == "turn":
            return "river"
        elif current_stage == "river":
            return "showdown"
    
    @staticmethod
    def handle_fold(player, current_hand_players):
        if player in current_hand_players:
            current_hand_players.remove(player)
        return  "fold", current_hand_players
    
    @staticmethod
    def handle_call(player, current_bet, current_hand_players):
        call_amount = current_bet - player.current_bet
        bet_amount = 0
        action = "call"
        if call_amount > player.num_chips:
            action, current_hand_players = PokerStateManager.handle_fold(player, current_hand_players)
        else:
            player.bet(call_amount)
            bet_amount = call_amount
        return bet_amount, action, current_hand_players
    
    @staticmethod
    def handle_raise(player, num_remaining_raises: int, current_bet, big_blind_chips, current_hand_players):
        raise_amount = big_blind_chips + (current_bet - player.current_bet) # NOTE: Assuming a raise means that you first go "even" with the current bet
        bet_amount = 0
        action = "raise"
        if raise_amount > player.num_chips or num_remaining_raises == 0:
           bet_amount, action, current_hand_players = PokerStateManager.handle_call(player, current_bet, current_hand_players)
        else:
            num_remaining_raises -= 1
            player.bet(raise_amount)
            bet_amount = raise_amount
        return  bet_amount, action, num_remaining_raises, current_hand_players

     
  
# MARK: Main        
if __name__ == "__main__":
    from game_manager import PokerGameManager
    
    game_manager = PokerGameManager()
    game_manager.add_poker_agent("rollout", 100, "Bob")
    game_manager.add_poker_agent("rollout", 100, "Alice")
    # game_manager.add_poker_agent("rollout", 100, "Chris") # NOTE: Recursion error for three players
    card_deck = CardDeck()
    for player in game_manager.poker_agents:
        player.recieve_hole_cards(card_deck.deal(2))
    
    state_manager = PokerStateManager(game_manager.num_chips_bet, 
                                      game_manager.small_blind_chips, 
                                      game_manager.big_blind_chips, 
                                      game_manager.legal_num_raises_per_stage, 
                                      game_manager.use_limited_deck)
    
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
    state_manager.generate_subtree_to_given_stage_and_depth(root_state, 
                                                            end_stage="showdown", 
                                                            end_depth=16)
    
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
    
    # print_subtree(root_state)
    
    # print("========================================================\n")
    def iterative_print_subtree(state: PlayerState):
        nodes = state.children
        while not nodes == []:
            child = nodes.pop()
            if isinstance(child, PlayerState):
                print("PLAYER", child.origin_action, child.depth, child.stage)
            if isinstance(child, TerminalState):
                print("TERMINAL", child.origin_action, child.depth, child.stage)
            if isinstance(child, ChanceState):
                print("CHANCE", child.event, child.player_state.depth, child.stage, child.player_state.stage)
            if not child.children == []:
                for grand_child in child.children:
                    nodes.append(grand_child)
                    
    iterative_print_subtree(root_state)
    
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
    