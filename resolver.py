import numpy as np
from state_manager import PokerStateManager

class Resolver:
    # Resolving:
    # - Produce subtree, either fully or incrementally
    # - Rollout. Does not need to fully explore the subtree. May want to stop when the stage changes.
    # - For chance nodes: Each visit can invoke different events (public cards)
    # - Each player node (or state) houses a strategy matrix, with one row for each possible hole pair and one column for each possible action. 
    # - Range vectors are sent down to each node, and evaluation vectors are returned upward. #TODO: NEED TO ADD PARENT POINTERS TO STATES
    # - Range of active player is modified as it passes down.

    def generate_initial_subtree(self, state, acting_player_range, other_player_range, end_stage, end_depth):
        pass


    def is_showdown_state(self,state):
        # NOTE: Should probably come from StateManager
        pass


    def is_player_state(self,state):
        # NOTE: Should probably come from StateManager
        pass


    def get_utility_matrix_from_state(self, state):
        # NOTE: Should use the PokerOracle
        pass


    def run_neural_network(self, stage, state, acting_player_range, other_player_range):
        pass


    def get_all_hole_pairs():
        # NOTE: Should probably use poker oracle
        pass


    def subtree_traversal_rollout(self, state, acting_player_range, other_player_range, end_stage, end_depth):
        # NOTE: Pseudocode assumes that state objects contain its STAGE and DEPTH
        if self.is_showdown_state(state):
            utility_matrix = self.get_utility_matrix_from_state(state)
            acting_player_evaluation = utility_matrix * np.transpose(other_player_range)
            other_player_evaluation = -1 * acting_player_range * utility_matrix
            
        elif state.stage == end_stage and state.depth == end_depth:
            # NOTE: The way i understand it:
            # - We can begin traversal from any stage
            # - The depth refers to the moves made within one stage
            # - Therefore should only stop when we reach the end depth of the end stage
            acting_player_evaluation, other_player_evaluation = self.run_neural_network(state.stage, state, acting_player_range, other_player_range)
            
        elif self.is_player_state(state):
            acting_player_evaluation = 0
            other_player_evaluation = 0
            for action in state.get_actions(): # TODO: State should "know" which actions are available for traversal
                acting_player_range = self.bayesian_range_update(acting_player_range, action, state.strategy_matrix)
                other_player_range = other_player_range
                state_after_action = PokerStateManager.get_child_state_by_action(state, action) 
                # NOTE: Pseudocode uses different notations for the ranges in the two lines above, and the ranges in the function call below
                # The former is called r_P(a) and r_O(a), and the latter is called r_1(a) and r_2(a). 
                # TODO: Not sure how to handle this difference. Need to ask
                acting_player_evaluation_current_action, other_player_evaluation_current_action = self.subtree_traversal_rollout(state_after_action, acting_player_range, other_player_range, end_stage, end_depth)
                for h in range(len(self.get_all_hole_pairs())): # NOTE: Scaled update of evaluations
                    # NOTE: h and action should be indices
                    acting_player_evaluation[h] += state.strategy_matrix[h][action] * acting_player_evaluation_current_action[h]
                    other_player_evaluation[h] += state.strategy_matrix[h][action] * other_player_evaluation_current_action[h]
                    
        else:
            # NOTE: Assumes that the state is a chance node
            acting_player_evaluation = 0
            other_player_evaluation = 0
            for event in state.get_events():
                state_after_event = PokerStateManager.get_child_state_by_event(state, event) #TODO: MAY NEED SOMETHING LIKE THIS
                acting_player_evaluation_current_event, other_player_evaluation_current_event = self.subtree_traversal_rollout(state_after_event, acting_player_range, other_player_range, end_stage, end_depth)
                for h in range(len(self.get_all_hole_pairs())): # NOTE: Scaled update of evaluations
                    acting_player_evaluation[h] += acting_player_evaluation_current_event[h] / len(state.get_events())
                    other_player_evaluation[h] += other_player_evaluation_current_event[h] / len(state.get_events())
        
        return acting_player_evaluation, other_player_evaluation
                
                
    def update_strategy(self, node):
        state = node.state # ???
        for child in state.children:
            self.update_strategy(child)
        if self.is_player_state(state):
            cumulative_regret = state.cumulative_regret # TODO: State should store cummulative regret?
            positive_regret = state.positive_regret # TODO: State should store positive regret?
            for h in range(len(self.get_all_hole_pairs())):
                for a in range(len(state.get_actions())):
                    active_player_evaluation_for_next_state = None # What to do
                    active_player_evaluation_for_current_state = None # What to do
                    cumulative_regret[h][a] += active_player_evaluation_for_next_state[h] - active_player_evaluation_for_current_state[h]
                    positive_regret[h][a] = np.maximum(cumulative_regret[h][a], 0) 
            state.cumulative_regret = cumulative_regret
            state.positive_regret = positive_regret
            
            for h in range(len(self.get_all_hole_pairs())):
                for a in range(len(state.get_actions())):
                    state.strategy_matrix[h][a] = positive_regret[h][a] / np.sum(positive_regret[h]) # NOTE: Pay attetntion to the axis when summing
                    
        return state.strategy_matrix
            
    def get_action_from_strategy_matrix(self, average_strategy_matrix):
        pass


    def bayesian_range_update(self, acting_player_range, action, average_strategy_matrix):
        # TODO: PSEUDOCODE NOT PROVIDED
        pass


    def resolve(self, state, acting_player_range, other_player_range, end_stage, end_depth, num_rollouts):
        # TODO: How to generate ranges for each player?
        # TODO: How to determine end before resolving?
        # TODO: Need to fix the state manager to be able to generate proper subtrees
        
        root_node = self.generate_initial_subtree(state, acting_player_range, other_player_range, end_stage, end_depth)
        
        acting_player_evaluations = []
        other_player_evaluations = []
        strategy_matrices = []
        for _ in range(num_rollouts):
            # NOTE: Think evaluations has some relation to root_node, but not sure exactly how they relate
            acting_player_evaluation, other_player_evaluation = self.subtree_traversal_rollout(state, acting_player_range, other_player_range, end_stage, end_depth)
            strategy_matrix = self.update_strategy(root_node)
            
            acting_player_evaluations.append(acting_player_evaluation)
            other_player_evaluations.append(other_player_evaluation)
            strategy_matrices.append(strategy_matrix)
        
        average_strategy_matrix = np.mean(strategy_matrices, axis=0) # Want to get ONE MATRIX (not value or vector)
        
        action = self.get_action_from_strategy_matrix(average_strategy_matrix)
        
        acting_player_range = self.bayesian_range_update(acting_player_range, action, average_strategy_matrix)
        
        return action, acting_player_range # NOTE: Pseudocode additionally return the state resulting from action and the other player's range (even though it's not updated here)