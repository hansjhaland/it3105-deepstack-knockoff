from card_deck import CardDeck
from game_manager import PokerGameManager

# NOTE: Starting with two-player case only
class PokerStateManager:

    def __init__(self, game_manager: PokerGameManager):
        # NOTE: Setting same rules as the game manager
        self.num_chips_bet = game_manager.num_chips_bet
        self.small_blind_chips = game_manager.small_blind_chips
        self.big_blind_chips = game_manager.big_blind_chips
        self.legal_num_raises_per_stage = game_manager.legal_num_raises_per_stage
        
        # In general, nodes are of type "acting", "opponent", "chance", "end".

    # NOTE: To be used as root node in Resolver
    def generate_root_state(self, acting_player, players, public_cards, pot, num_raises_left, bet_to_call):
        return PlayerState(acting_player, players, acting_player, public_cards, pot, num_raises_left, bet_to_call)
    # def generate_root_state(self, acting_player, players, public_cards, pot, num_raises_left, bet_to_call, initial_round_action_history):
    #     return PlayerState(acting_player, players, acting_player, public_cards, pot, num_raises_left, bet_to_call, initial_round_action_history)
    
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
            bet_amount, action, num_raises_left, players = PokerGameManager.handle_raise(player, self.legal_num_raises_per_stage, current_bet, self.num_chips_bet, players,)
            # If action is set to something else than raise, then the code will continue to the next apropriate "first level" if statement
            if action == "raise":
                action_to_generated_state = action
                pot = state.pot + bet_amount
                bet_to_call = player.current_bet + bet_amount
                next_index = (players.index(player) + 1) % len(players)
                next_player = players[next_index]
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, pot, num_raises_left, bet_to_call, state.stage, action_to_generated_state)
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
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, pot, state.num_raises_left, state.bet_to_call, state.stage, action_to_generated_state)
        if self.already_generated_state(state, action):
            return None, None
        if action == "fold": 
            # Fold always result in terminal state
            player = state.current_state_acting_player
            players = state.players.copy()
            next_index = (players.index(player) + 1) % len(players)
            next_player = players[next_index]
            action_to_generated_state, players = PokerGameManager.handle_fold(player, players)
            if player == state.acting_player:
                child_state = TerminalState(players, state.pot, action_to_generated_state, action_to_generated_state)
            else:
                child_state = PlayerState(state.acting_player, players, next_player, state.public_cards, state.pot, state.num_raises_left, state.bet_to_call, state.stage, action_to_generated_state)
        return child_state, action_to_generated_state
    
    def already_generated_state(self, state, action) -> bool:
        for child in state.children:
            if child.origin_action == action:
                return True
        return False
    
    # def handle_fold(self, state):
    #     remaining_players = state.players.remove(state.acting_player)
    #     if len(remaining_players) == 1:
    #         # End of game
    #         return
    #     next_index = (state.acting_index + 1) % len(remaining_players)
    #     next_acting_player = remaining_players[next_index]
    #     child_state = PlayerState(next_acting_player, remaining_players, state.public_cards, state.pot, state.num_raises_left, state.bet_to_call)
    #     state.children.append(child_state)
        
    # def handle_call(self, state):
    #     chips_for_call = state.bet_to_call - state.acting_player.current_bet
    #     state.acting_player.bet(chips_for_call)
    #     state.pot += chips_for_call
    #     next_index = (state.acting_index + 1) % len(state.players)
    #     next_acting_player = state.players[next_index]
    #     # Can go to next stage?
    #     to_next_stage = True
    #     for player in state.players:
    #         if player.current_bet != state.bet_to_call:
    #             to_next_stage = False
    #     if not to_next_stage:
    #         child_state = PlayerState(next_acting_player, state.players, state.public_cards, state.pot, state.num_raises_left, state.bet_to_call, state.stage)
    #         state.children.append(child_state)
    #     else:
    #         # If stage is 0 (pre-flop), 1 (flop) or 2 (turn) then add a chance node
    #         # Else go to showdown
    #         if state.stage < 3:
    #             chance_state = ChanceState(state.public_cards, state.acting_player.hole_cards, state.stage + 1)
    #             state.children.append(chance_state)
    #         else:
    #             # TODO: Handle showdown here?
    #             pass
    
    
    def is_legal_action(self, state, action):
        if action == "fold":
            return len(state.players)  > 1 # Thinking that a player can't fold if he's the only one left
        if action == "call":
            return state.acting_player.get_chips() > 0 # Think this is how i have written it in game_manager
        if action == "raise":
            return self.can_raise(state)
        return False
        
    def can_raise(self, state):
        if state.num_raises_left > 0:
            if state.acting_player.current_bet >= state.bet_to_call:
                return True
            if state.acting_player.current_bet < state.bet_to_call:
                cal_diff = state.bet_to_call - state.acting_player.current_bet
                if state.acting_player.num_chips > cal_diff:
                    return True
                return False
        return False     
    
    def generate_all_child_states(self, state):
        for action in ["fold", "call", "raise"]:
            child_state, _ = self.generate_child_state_from_action(state, action)
            if child_state is not None:
                state.children.append(child_state)
                
    # def generate_all_states_remaining_in_hand(self, root_state):
        
        
    
    
    
class PlayerState:
    
    def __init__(self, acting_player, players, current_state_acting_player, public_cards, pot, num_raises_left, bet_to_call, stage="pre-flop", origin_action="root", round_action_history=[]):
        # TODO: May need to distinguish between "perspective player" which is the acting player
        # in the root state, and the "acting player" which is the player who is currently acting
        # in an arbitrary state.
        self.acting_player = acting_player
        self.players = players
        self.current_state_acting_player = current_state_acting_player
        self.public_cards = public_cards
        self.pot = pot
        self.num_raises_left = num_raises_left
        self.bet_to_call = bet_to_call
        self.stage: int = stage
        self.winner = None
        
        self.round_action_history = round_action_history
        self.origin_action = origin_action
        self.children = []
        
        
class ChanceState:
    
    def __init__(self, acting_player, public_cards, hole_cards, stage, origin_action):
        self.card_deck = CardDeck() # REMEMBER TO ADD OPTION TO LIMIT DECK
        self.card_deck.exclude(public_cards)
        self.card_deck.exclude(hole_cards)
        self.stage = stage
        
        self.acting_player = acting_player
        self.origin_action = origin_action
        self.children = []
        
        
class TerminalState:
    
    def __init__(self, acting_player, players, pot, origin_action):
        self.acting_player = acting_player
        self.players = players
        self.pot = pot
        self.winner = None
        self.payouts = {}
        
        self.origin_action = origin_action
        self.children = []
        
        
if __name__ == "__main__":
    game_manager = PokerGameManager()
    game_manager.add_poker_agent("rollout", 100, "Bob")
    game_manager.add_poker_agent("rollout", 100, "Alice")
    
    state_manager = PokerStateManager(game_manager)
    
    root_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                   players=game_manager.poker_agents, 
                                                   public_cards=[], 
                                                   pot=0, 
                                                   num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                   bet_to_call=game_manager.current_bet)
    
    state_manager.generate_all_child_states(root_state)
    
    # [print(child.origin_action) for child in root_state.children]
    
    
    
    def get_all_children(state, depth=1):
        for child in state.children:
            if depth == 5:
                return
            print(child.origin_action, depth)
            state_manager.generate_all_child_states(child)
            get_all_children(child, depth + 1)
    
    get_all_children(root_state)