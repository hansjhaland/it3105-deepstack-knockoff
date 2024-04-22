import numpy as np
from state_manager import PokerStateManager, PlayerState, ChanceState, TerminalState
from poker_oracle import PokerOracle
from game_manager import PokerGameManager
from card_deck import Card, CardDeck
import copy

class Resolver:
    # Resolving:
    # - Produce subtree, either fully or incrementally
    # - Rollout. Does not need to fully explore the subtree. May want to stop when the stage changes.
    # - For chance nodes: Each visit can invoke different events (public cards)
    # - Each player node (or state) houses a strategy matrix, with one row for each possible hole pair and one column for each possible action. 
    # - Range vectors are sent down to each node, and evaluation vectors are returned upward. 
    # #TODO: NEED TO ADD PARENT POINTERS TO STATES
    # - Range of active player is modified as it passes down.

    def __init__(self, state_manager: PokerStateManager, poker_oracle: PokerOracle):
        self.state_manager = state_manager
        self.poker_oracle = poker_oracle
        
        self.action_to_index = {"fold": 0, "call": 1, "raise": 2}


    def generate_initial_subtree(self, state, end_stage, end_depth):
        self.state_manager.generate_subtree_to_given_stage_and_depth(state, end_stage, end_depth)
        return state


    def is_showdown_state(self, state):
        return state.stage == "showdown"


    def is_player_state(self,state):
        return isinstance(state, PlayerState)


    def get_utility_matrix_from_state(self, state: PlayerState):
        utility_matrix, _ = poker_oracle.utility_matrix_generator(state.public_cards)
        return utility_matrix


    def run_neural_network(self, stage, state, acting_player_range, other_player_range):
        
        # if stage == "flop":
        #     pass
        # if stage == "turn":
        #     pass
        # if stage == "river":
        #     pass
        
        acting_eval = np.random.uniform(size=len(self.get_all_hole_pairs()))
        other_eval = np.random.uniform(size=len(self.get_all_hole_pairs()))
        return acting_eval, other_eval # TODO: TEMPORARY VALUES


    def get_all_hole_pairs(self):
        return self.poker_oracle.get_all_hole_pair_keys()

    
    def get_initial_ranges(self, public_cards: list[Card], acting_player_cards: list[Card]):    
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
    
    
    def get_initial_strategy(self):
        hole_pair_keys: list[str] = self.poker_oracle.get_all_hole_pair_keys()
        actions = list(self.action_to_index.keys())
        num_actions = len(actions)
        strategy_matrix = []
        for _ in range(len(hole_pair_keys)):
            action_distribution = np.ones(num_actions) * 1/num_actions
            strategy_matrix.append(action_distribution)
            
        return np.asarray(strategy_matrix)
    

    def subtree_traversal_rollout(self, state: PlayerState|ChanceState, acting_player_range, other_player_range, end_stage, end_depth):
        stage_dict = {"pre-flop": 0,
                "flop": 1,
                "turn": 2,
                "river": 3,
                "showdown": 4}
        
        if self.is_showdown_state(state):
            utility_matrix = self.get_utility_matrix_from_state(state)
            # acting_player_evaluation = utility_matrix * np.transpose(other_player_range)
            acting_player_evaluation = np.squeeze(np.matmul(utility_matrix, np.atleast_2d(other_player_range).T))
            other_player_evaluation = -1 * np.matmul(acting_player_range, utility_matrix)
            print(utility_matrix.shape)
            print(np.transpose(other_player_range).shape)
            print(acting_player_range.shape)
            print(acting_player_evaluation.shape)
            print(other_player_evaluation.shape)
            # print("SHOWDOWN:", acting_player_evaluation, other_player_evaluation)
            print("SHOWDOWN:", state.stage, state.depth)
            
        elif stage_dict[state.stage] >= stage_dict[end_stage] and state.depth >= end_depth:
            # NOTE: The way i understand it:
            # - We can begin traversal from any stage
            # - The depth refers to the moves made within one stage
            # - Therefore should only stop when we reach the end depth of the end stage
            acting_player_evaluation, other_player_evaluation = self.run_neural_network(state.stage, state, acting_player_range, other_player_range)
            # print("NEURAL NET:", acting_player_evaluation, other_player_evaluation)
            print("NEURAL NET:", state.stage, state.depth)
            
        elif stage_dict[state.stage] > stage_dict[end_stage]:
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            
        elif isinstance(state, TerminalState):
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
          
        # NOTE: Never enters SHOWDOWN or NEURAL NET 
        # Only player state and last  
        elif self.is_player_state(state):
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            for action in state.actions_to_children: 
                acting_player_range_current_action = acting_player_range
                acting_player_range_current_action = self.bayesian_range_update(acting_player_range_current_action, action, state.get_strategy_matrix())
                other_player_range_current_action = other_player_range
                state_after_action = PokerStateManager.get_child_state_by_action(state, action) # NOTE: This only gets other player states
                # print(f"Stage {state_after_action.stage}, Depth {state_after_action.depth}, Player {isinstance(state_after_action, PlayerState)}, Chance {isinstance(state_after_action, ChanceState)}, Terminal {isinstance(state_after_action, TerminalState)}")
                acting_player_evaluation_current_action, other_player_evaluation_current_action = self.subtree_traversal_rollout(state_after_action, acting_player_range_current_action, other_player_range_current_action, end_stage, end_depth)
                # acting_player_evaluation_current_action, other_player_evaluation_current_action = self.subtree_traversal_rollout(state_after_action, other_player_range_current_action, acting_player_range_current_action, end_stage, end_depth)
                for h in range(len(self.get_all_hole_pairs())): # NOTE: Scaled update of evaluations
                    a = self.action_to_index[action]
                    acting_player_evaluation[h] += state.get_strategy_matrix()[h][a] * acting_player_evaluation_current_action[h]
                    other_player_evaluation[h] += state.get_strategy_matrix()[h][a] * other_player_evaluation_current_action[h]
            # print("PLAYER STATE:", acting_player_evaluation, other_player_evaluation)
            for child in state.children:
                if isinstance(child, ChanceState): # NOTE: IF it is a chance state, then it has not yet been visited
                    acting_player_evaluation_current_action, other_player_evaluation_current_action = self.subtree_traversal_rollout(child, acting_player_range, other_player_range, end_stage, end_depth)
                    for h in range(len(self.get_all_hole_pairs())): # NOTE: Scaled update of evaluations
                        a = self.action_to_index["call"] # NOTE: QUICK FIX: ASSUMING CHANCE STATE IS ALWAYS THE RESULT OF A CALL
                        acting_player_evaluation[h] += state.get_strategy_matrix()[h][a] * acting_player_evaluation_current_action[h]
                        other_player_evaluation[h] += state.get_strategy_matrix()[h][a] * other_player_evaluation_current_action[h]
            print("PLAYER STATE:", state.stage, state.depth)    
        else:
            # NOTE: Assumes that the state is a chance node
            acting_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            other_player_evaluation = np.zeros(len(self.get_all_hole_pairs()))
            if not isinstance(state, TerminalState): # Assuming a zero evaluation is bad
                for event in state.child_events:
                    state_after_event = PokerStateManager.get_player_state_after_event(state, event)
                    acting_player_evaluation_current_event, other_player_evaluation_current_event = self.subtree_traversal_rollout(state_after_event, acting_player_range, other_player_range, end_stage, end_depth)
                    # acting_player_evaluation_current_event, other_player_evaluation_current_event = self.subtree_traversal_rollout(state_after_event, other_player_range, acting_player_range, end_stage, end_depth)
                    for h in range(len(self.get_all_hole_pairs())): # NOTE: Scaled update of evaluations
                        acting_player_evaluation[h] += acting_player_evaluation_current_event[h] / len(state.child_events)
                        other_player_evaluation[h] += other_player_evaluation_current_event[h] / len(state.child_events)
                # print("CHANCE STATE:", acting_player_evaluation, other_player_evaluation)
                print("CHANCE STATE:", state.stage)
        state.acting_player_evaluation = acting_player_evaluation
        state.other_player_evaluation = other_player_evaluation
        return acting_player_evaluation, other_player_evaluation
                
                
    def update_strategy(self, state: PlayerState):
        for child in state.children:
            if self.is_player_state(child):
                self.update_strategy(child)
        if self.is_player_state(state):
            cumulative_regret = state.cumulative_regret 
            positive_regret = state.positive_regret 
            # print("REGRET:", cumulative_regret, positive_regret)
            for h in range(len(self.get_all_hole_pairs())):
                for action in state.actions_to_children:
                    a = self.action_to_index[action]
                    state_after_action: PlayerState = PokerStateManager.get_child_state_by_action(state, state.actions_to_children[a])
                    # NOTE: Should maybe use acting player in current state and other player in next state?
                    cumulative_regret[h][a] += state_after_action.acting_player_evaluation[h] - state.acting_player_evaluation[h]
                    # cumulative_regret[h][a] += state_after_action.other_player_evaluation[h] - state.acting_player_evaluation[h]
                    positive_regret[h][a] = np.maximum(cumulative_regret[h][a], 0) 
            state.cumulative_regret = cumulative_regret
            state.positive_regret = positive_regret
            
            strategy_matrix = state.get_strategy_matrix()
            for h in range(len(self.get_all_hole_pairs())):
                for action in state.actions_to_children:
                    if not action == "chance":
                        a = self.action_to_index[action]
                        strategy_matrix[h][a] = state.positive_regret[h][a] / np.sum(state.positive_regret[h]) # NOTE: Pay attetntion to the axis when summing
                        # print(strategy_matrix[h][a], state.positive_regret[h][a], np.sum(state.positive_regret[h]))
                        # print("YEY" ,cumulative_regret[h], positive_regret[h], strategy_matrix[h])
            
            state.set_strategy_matrix(strategy_matrix)
            
        return strategy_matrix
            
    def get_action_from_strategy_matrix(self, average_strategy_matrix):
        # TODO: How to sample one action from the strategy
        
        return "call"

    # NOTE Based on slides page 63
    def bayesian_range_update(self, acting_player_range, action, strategy_matrix):
        prob_action_given_pair = strategy_matrix[:, self.action_to_index[action]]
        # print("Column:", np.sum(prob_action_given_pair), "Entire array:", np.sum(strategy_matrix))
        prob_action = np.sum(prob_action_given_pair) / np.sum(strategy_matrix)
        
        return acting_player_range * (prob_action_given_pair/prob_action)


    def resolve(self, state: PlayerState, acting_player_range, other_player_range, end_stage, end_depth, num_rollouts):
        # TODO: How to determine end before resolving?
        # init_a_p_r = copy.deepcopy(acting_player_range)
        
        initial_strategy = self.get_initial_strategy()
        state.set_strategy_matrix(initial_strategy)
        root_node = self.generate_initial_subtree(state, end_stage, end_depth)
                
        strategy_matrices = []
        for _ in range(num_rollouts):
            # NOTE: Think evaluations has some relation to root_node, but not sure exactly how they relate
            acting_player_evaluation, other_player_evaluation = self.subtree_traversal_rollout(state, acting_player_range, other_player_range, end_stage, end_depth)
            # print(acting_player_evaluation, other_player_evaluation)
            
            # print(acting_player_evaluation, other_player_evaluation)
            root_node.acting_player_evaluation = acting_player_evaluation
            root_node.other_player_evaluation = other_player_evaluation
            strategy_matrix = self.update_strategy(root_node)
            # print(root_node.acting_player_evaluation == acting_player_evaluation, root_node.other_player_evaluation == other_player_evaluation)
            # print(strategy_matrix)
            strategy_matrices.append(strategy_matrix)
            # print(strategy_matrix)
            # NOTE Check if different strategies are generated. Seems like this is happening.
            # if len(strategy_matrices) > 1:
            #     print(strategy_matrices[-1] == strategy_matrices[-2])
        
        # print("Matrices:", np.asarray(strategy_matrices).shape)
        average_strategy_matrix = np.mean(np.asarray(strategy_matrices), axis=0)
        # print("Avg:", average_strategy_matrix.shape)
        
        action = self.get_action_from_strategy_matrix(average_strategy_matrix)
        
        # print("Avg matrix:", average_strategy_matrix)
        # print("Before final update:", acting_player_range)
        
        # TODO: Range is updated to nan if action is call or fold, not changed if action is raise.
        # Seems like the strategy matrix gets 1 in raise column and 0 in the other columns
        
        # acting_player_range_copy = copy.deepcopy(acting_player_range)
        acting_player_range = self.bayesian_range_update(acting_player_range, action, average_strategy_matrix)
        # print(init_a_p_r == acting_player_range_copy)
        
        return action, acting_player_range # NOTE: Pseudocode additionally return the state resulting from action and the other player's range (even though it's not updated here)
    
    
if __name__ == "__main__":
    
    use_limited_deck = True
    
    poker_oracle = PokerOracle(use_limited_deck)
    game_manager = PokerGameManager(use_limited_deck)
    state_manager = PokerStateManager(game_manager)
    resolver = Resolver(state_manager, poker_oracle)
    
    card_deck = CardDeck(use_limited_deck)
    card_deck.shuffle()
    
    # public_cards = card_deck.deal(5)
    
    # acting_player_hole_cards = card_deck.deal(2)
    
    # acting_player_ranges, other_player_ranges = resolver.get_initial_ranges(public_cards,
    #                                                                         acting_player_hole_cards)
    # print(acting_player_ranges)
    # print()
    # print(other_player_ranges)
    
    # strategy_matrix = resolver.get_initial_strategy()
    
    # print(strategy_matrix)
    
    
    # a = np.asarray([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    # b = np.asarray([[9, 8, 7], [6, 5, 4], [3, 2, 1]])
    # matrices = np.asarray([a, b])    
    
    # print("None:", np.mean(matrices))
    # print("Axis 0:", np.mean(matrices, axis=0)) # NOTE: This is what I want for strategy matrices
    # print("Axis 1:", np.mean(matrices, axis=1))
    # print("Axis 2:", np.mean(matrices, axis=2))
    # print("Axis 0,1:", np.mean(matrices, axis=(0,1)))
    
    game_manager.add_poker_agent("rollout", 100, "Alice")
    game_manager.add_poker_agent("rollout", 100, "Bob")
    
    for player in game_manager.poker_agents:
        player.recieve_hole_cards(card_deck.deal(2))
    
    strategy = resolver.get_initial_strategy()
    
    root_state = state_manager.generate_root_state(acting_player=game_manager.poker_agents[0], 
                                                players=game_manager.poker_agents, 
                                                public_cards=[], 
                                                pot=0, 
                                                num_raises_left=game_manager.legal_num_raises_per_stage, 
                                                bet_to_call=game_manager.current_bet,
                                                stage="pre-flop",
                                                initial_round_action_history=[],
                                                initial_depth=0,
                                                strategy_matrix=strategy
                                                )
    
    # Assuming alice is acting player
    
    # NOTE: Hver state er koblet til en STRATEGI og en RANGE og EVALUATION for HVER SPILLER.
    
    acting_player_range, other_player_range = resolver.get_initial_ranges([], game_manager.poker_agents[0].hole_cards)
    # NOTE: RUN from PRE-FLOP to SHOWDOWN takes SEVERAL HOURS. Still ends with nan values.
    # Try debugging with less stages!
    end_stage = "showdown"
    end_depth = 3
    num_rollouts = 10
    
    action, acting_player_range = resolver.resolve(root_state, acting_player_range, other_player_range, end_stage, end_depth, num_rollouts)
    
    # print("Action:", action)
    print("Modified range:", acting_player_range)
    