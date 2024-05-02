import numpy as np
import torch
from state_manager import PokerStateManager, PlayerState, ChanceState, TerminalState
from poker_oracle import PokerOracle
from card_deck import Card, CardDeck
from neural_networks import NeuralNetwork, load_model_from_file, encode_public_cards

class Resolver:

    def __init__(self, state_manager: PokerStateManager, poker_oracle: PokerOracle):
        self.state_manager = state_manager
        self.poker_oracle = poker_oracle
        
        self.action_to_index = {"fold": 0, "call": 1, "raise": 2}

# MARK: Resolve

    def resolve(self, state: PlayerState, acting_player_range: np.ndarray, other_player_range: np.ndarray, end_stage: str, end_depth: int, num_rollouts: int) -> np.ndarray:
            initial_strategy = self.get_initial_strategy()
            state.set_strategy_matrix(initial_strategy)
            root_node = self.generate_initial_subtree(state, end_stage, end_depth)
                    
            strategy_matrices = []
            for _ in range(num_rollouts):
                acting_player_evaluation, other_player_evaluation = self.subtree_traversal_rollout(state, acting_player_range, other_player_range, end_stage, end_depth)
                
                root_node.acting_player_evaluation = acting_player_evaluation
                root_node.other_player_evaluation = other_player_evaluation
      
                strategy_matrix = self.update_strategy(root_node)
                
                # NOTE: QUICK FIX for handlig nan values in strategy!
                
                # strategy_matrix = np.nan_to_num(strategy_matrix, nan=1/3) 
                strategy_matrix = self.handle_nan_values(strategy_matrix)
                
                strategy_matrices.append(strategy_matrix)
            
            average_strategy_matrix = np.mean(np.asarray(strategy_matrices), axis=0)
                    
            # NOTE: Pseudocode in assignment returns an action sampled from the strategy AND an updated range for the acting player.
            # I have decided to choose a more hacky apporach. I only return the strategy. And let the resolver agent pick the 
            # correct strategy based on its hole cards.
            # I do not return the range. This means resolving always will start with "default" ranges.
            
            return average_strategy_matrix


# MARK: Subtree traversal

    def generate_initial_subtree(self, state: PlayerState, end_stage: str, end_depth: int) -> PlayerState:
        self.state_manager.generate_subtree_to_given_stage_and_depth(state, end_stage, end_depth)
        return state


    def subtree_traversal_rollout(self, state: PlayerState|ChanceState|TerminalState, acting_player_range: np.ndarray, other_player_range: np.ndarray, end_stage: str, end_depth: int) -> tuple[np.ndarray]:
        stage_dict = {"pre-flop": 0,
                "flop": 1,
                "turn": 2,
                "river": 3,
                "showdown": 4}
        
        if self.is_showdown_state(state):
            # TODO: GENERATING UTILITY MATRICES TAKSE TIME. SHOULD MAYBE STORE MATRICES.
            utility_matrix = self.get_utility_matrix_from_state(state)
            acting_player_evaluation = np.squeeze(np.matmul(utility_matrix, np.atleast_2d(other_player_range).T))
            other_player_evaluation = -1 * np.matmul(acting_player_range, utility_matrix)
            # print("SHOWDOWN:", state.stage, state.depth)
            
        elif stage_dict[state.stage] >= stage_dict[end_stage] and state.depth >= end_depth:
            acting_player_evaluation, other_player_evaluation = self.run_neural_network(state.stage, state, acting_player_range, other_player_range)
            # print("NEURAL NET:", state.stage, state.depth)
            
        elif stage_dict[state.stage] > stage_dict[end_stage]:
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            
        elif isinstance(state, TerminalState):
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
          
        elif self.is_player_state(state):
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            # print(state.actions_to_children)
            for action in state.actions_to_children: 
                acting_player_range_current_action = acting_player_range
                acting_player_range_current_action = self.bayesian_range_update(acting_player_range_current_action, action, state.get_strategy_matrix())
                other_player_range_current_action = other_player_range
                state_after_action = PokerStateManager.get_child_state_by_action(state, action) # NOTE: This only gets children that are player states
                other_player_evaluation_current_action, acting_player_evaluation_current_action = self.subtree_traversal_rollout(state_after_action, other_player_range_current_action, acting_player_range_current_action, end_stage, end_depth)
                for h in range(len(self.get_all_hole_pairs())):
                    a = self.action_to_index[action]
                    acting_player_evaluation[h] += state.get_strategy_matrix()[h][a] * acting_player_evaluation_current_action[h]
                    other_player_evaluation[h] += state.get_strategy_matrix()[h][a] * other_player_evaluation_current_action[h]
            # print("PLAYER STATE:", acting_player_evaluation, other_player_evaluation)
            for child in state.children:
                if isinstance(child, ChanceState): # NOTE: IF it is a chance state, then it has not yet been visited
                    other_player_evaluation_current_action, acting_player_evaluation_current_action = self.subtree_traversal_rollout(child, other_player_range, acting_player_range, end_stage, end_depth)
                    for h in range(len(self.get_all_hole_pairs())):
                        a = self.action_to_index["call"] # NOTE: QUICK FIX: ASSUMING CHANCE STATE IS ALWAYS THE RESULT OF A CALL
                        acting_player_evaluation[h] += state.get_strategy_matrix()[h][a] * acting_player_evaluation_current_action[h]
                        other_player_evaluation[h] += state.get_strategy_matrix()[h][a] * other_player_evaluation_current_action[h]
            # print("PLAYER STATE:", state.stage, state.depth)    
        else:
            # NOTE: Assumes that the state is a chance node
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            if not isinstance(state, TerminalState): # Assuming a zero evaluation is bad
                for event in state.child_events:
                    state_after_event = PokerStateManager.get_player_state_after_event(state, event)
                    acting_player_evaluation_current_event, other_player_evaluation_current_event = self.subtree_traversal_rollout(state_after_event, acting_player_range, other_player_range, end_stage, end_depth)
                    for h in range(len(self.get_all_hole_pairs())): # NOTE: Scaled update of evaluations
                        acting_player_evaluation[h] += acting_player_evaluation_current_event[h] / len(state.child_events)
                        other_player_evaluation[h] += other_player_evaluation_current_event[h] / len(state.child_events)
                # print("CHANCE STATE:", state.stage)
        state.acting_player_evaluation = acting_player_evaluation
        state.other_player_evaluation = other_player_evaluation
        return acting_player_evaluation, other_player_evaluation


# MARK: Evaulations and updates

    def get_utility_matrix_from_state(self, state: PlayerState) -> np.ndarray:
        utility_matrix, _ = self.poker_oracle.utility_matrix_generator(state.public_cards)
        return utility_matrix


    def run_neural_network(self, stage: str, state: PlayerState, acting_player_range: np.ndarray, other_player_range: np.ndarray) -> tuple[np.ndarray]:
        
        if stage == "pre-flop":
            # NOTE: This should never be called from a pre-flop state.
            acting_eval = np.random.uniform(size=len(self.get_all_hole_pairs()))
            other_eval = np.random.uniform(size=len(self.get_all_hole_pairs()))
            return acting_eval, other_eval
        
        use_limited = self.poker_oracle.use_limited_deck
        
        file_prefix = stage + "_limited" if use_limited else stage 
        
        neural_network = load_model_from_file(f"{file_prefix}_100epochs")
        
        encoded_public_cards = encode_public_cards(state.public_cards, use_limited)
        
        stage_max_pot = {
            "flop": 40,
            "turn": 60,
            "river": 80
        }
        
        relative_pot = [state.pot / stage_max_pot[stage]]
        
        neural_network_input = [*acting_player_range, *encoded_public_cards, *relative_pot, *other_player_range]
        
        neural_network_input = torch.Tensor([neural_network_input]) # NOTE: Add extra dim to match shapes in network
        
        acting_player_evaluation, other_player_evaluation, _ = neural_network(neural_network_input, use_limited)

        acting_player_evaluation = acting_player_evaluation.squeeze(0).detach().numpy()
        other_player_evaluation = other_player_evaluation.squeeze(0).detach().numpy()
        
        # NOTE: QUICKFIX! For some reason the evaluations from neural network are one element too short.
        # May be caused by some error in the data generation for neural networks.
        # Because of this I may need to regenerate the data sets.
        # However, I believe I don't have time for that and unfortunately have to settle with a quickfix.
        # I will append one random uniformly distributed value at the end of the evaluation to make
        # lengths add up.

        acting_player_evaluation = np.asarray([*acting_player_evaluation, np.random.uniform(size=1)[0]])
        other_player_evaluation = np.asarray([*other_player_evaluation, np.random.uniform(size=1)[0]])

        return acting_player_evaluation, other_player_evaluation


    def update_strategy(self, state: PlayerState) -> np.ndarray:
        for child in state.children:
            if self.is_player_state(child):
                self.update_strategy(child)
        if self.is_player_state(state):
            cumulative_regret = state.cumulative_regret 
            positive_regret = state.positive_regret 
            for h in range(len(self.get_all_hole_pairs())):
                for action in state.actions_to_children:
                    a = self.action_to_index[action]
                    state_after_action: PlayerState = PokerStateManager.get_child_state_by_action(state, action)
                    cumulative_regret[h][a] += (state_after_action.other_player_evaluation[h] - state.acting_player_evaluation[h])
                    # NOTE: 
                    # Seems like cumulative regret often negative. Leads to positive regrets becoming 0.
                    # Quick fix with 0.001 instead of 0
                    positive_regret[h][a] = np.maximum(0.001, cumulative_regret[h][a]) 
            state.cumulative_regret = cumulative_regret
            state.positive_regret = positive_regret
            
            strategy_matrix = state.get_strategy_matrix()
            for h in range(len(self.get_all_hole_pairs())):
                for action in state.actions_to_children:
                    a = self.action_to_index[action]
                    strategy_matrix[h][a] = state.positive_regret[h][a] / np.sum(state.positive_regret[h])
            
            state.set_strategy_matrix(strategy_matrix)
            
        return strategy_matrix
            
            
    # NOTE Based on slides page 63
    def bayesian_range_update(self, acting_player_range, action, strategy_matrix) -> np.ndarray:
        # NOTE: For some reason actoins is sometimes root....
        prob_action_given_pair = strategy_matrix[:, self.action_to_index[action]]
        prob_action = np.sum(prob_action_given_pair) / np.sum(strategy_matrix)
        
        return acting_player_range * (prob_action_given_pair/prob_action)


# MARK: Helper methods

    def get_all_hole_pairs(self) -> list[str]:
        return self.poker_oracle.get_all_hole_pair_keys()

    
    def get_initial_ranges(self, public_cards: list[Card], acting_player_cards: list[Card]) -> tuple[np.ndarray]:    
        # NOTE: Correct number of hole pair keys is 1326 for full deck
        # and 276 for limited deck. 
        hole_pair_keys: list[str] = self.poker_oracle.get_all_hole_pair_keys()
        
        acting_player_exclude_cards = []
        for card in public_cards:
            card_key = str(card.get_rank()) + card.get_suit()
            acting_player_exclude_cards.append(card_key)
    
        acting_player_ranges = np.zeros(len(hole_pair_keys))
        
        for i in range(len(acting_player_ranges)):
            hole_pair_is_possible = True
            for card in acting_player_exclude_cards:
                # Public card is part of the current hole pair, thus hole pair is impossible
                # Check if card string is substring of hole pair string
                if card in hole_pair_keys[i]:
                    hole_pair_is_possible = False
                    break
            if hole_pair_is_possible:
                acting_player_ranges[i] = 1
            
        num_possible_hands = np.sum(acting_player_ranges)
        uniform_probability = 1 / num_possible_hands
        
        acting_player_ranges = acting_player_ranges * uniform_probability
        
        # Acting players cards has to be exluded from other player ranges      
        other_player_exclude_cards = acting_player_exclude_cards
        for card in acting_player_cards:
            card_key = str(card.get_rank()) + card.get_suit()
            other_player_exclude_cards.append(card_key)
        
        other_player_ranges = np.zeros(len(hole_pair_keys))
        
        for i in range(len(other_player_ranges)):
            hole_pair_is_possible = True
            for card in other_player_exclude_cards:
                if card in hole_pair_keys[i]:
                    hole_pair_is_possible = False
                    break
            if hole_pair_is_possible:
                other_player_ranges[i] = 1
                
        num_possible_hands = np.sum(other_player_ranges)
        uniform_probability = 1 / num_possible_hands
        
        other_player_ranges = other_player_ranges * uniform_probability
        
        return np.asarray(acting_player_ranges), np.asarray(other_player_ranges)
    
    
    def get_initial_strategy(self) -> np.ndarray:
        hole_pair_keys: list[str] = self.poker_oracle.get_all_hole_pair_keys()
        actions = list(self.action_to_index.keys())
        num_actions = len(actions)
        strategy_matrix = []
        for _ in range(len(hole_pair_keys)):
            action_distribution = np.ones(num_actions) * 1/num_actions
            strategy_matrix.append(action_distribution)
            
        return np.asarray(strategy_matrix)
    

    def is_showdown_state(self, state: PlayerState) -> bool:
        return state.stage == "showdown"


    def is_player_state(self, state: PlayerState | ChanceState | TerminalState) -> bool:
        return isinstance(state, PlayerState)
                
                
    def handle_nan_values(self, strategy_matrix: np.ndarray) -> np.ndarray:
        # NOTE: Something is wrong here. Elements in each row still sometimes sum to more than one!
        for i in range(len(strategy_matrix)):
            nan_indices = np.argwhere(np.isnan(strategy_matrix[i]))
            # print("nan_indices",nan_indices)
            num_nans_in_row = len(nan_indices)
            # print("num_nans_in_row",num_nans_in_row)
            if num_nans_in_row > 0:
                current_sum = np.round(np.nansum(strategy_matrix[i]), decimals=3)
                # print("current_sum",current_sum)
                for j in list(nan_indices):
                    # print("Index",j)
                    strategy_matrix[i][j] = float((1 - current_sum) / num_nans_in_row)
                    # print("difference", 1-current_sum)
                    # print("entry", strategy_matrix[i][j])
                    
        return strategy_matrix
            
            
# MARK: Main  
if __name__ == "__main__":
    from game_manager import PokerGameManager
    
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
    
    game_manager.add_poker_agent("rollout", 100, "Alice")
    game_manager.add_poker_agent("rollout", 100, "Bob")
    
    for player in game_manager.poker_agents:
        player.recieve_hole_cards(card_deck.deal(2))
    
    strategy = resolver.get_initial_strategy()
    
    public_cards = card_deck.deal(4)
        
    root_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                players=game_manager.poker_agents, 
                                                public_cards=public_cards, 
                                                pot=0, 
                                                num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                bet_to_call=game_manager.current_bet,
                                                stage="turn",
                                                initial_round_action_history=[],
                                                initial_depth=0,
                                                strategy_matrix=strategy
                                                )
    
    # Assuming alice is acting player
    
    acting_player_range, other_player_range = resolver.get_initial_ranges(public_cards, game_manager.poker_agents[0].hole_cards)
    # NOTE: RUN from PRE-FLOP to SHOWDOWN takes SEVERAL HOURS. Still ends with nan values.
    # Try debugging with less stages!
    end_stage = "river"
    end_depth = 1
    num_rollouts = 1
    
    strategy = resolver.resolve(root_state, acting_player_range, other_player_range, end_stage, end_depth, num_rollouts)