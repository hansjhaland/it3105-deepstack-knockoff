from card_deck import CardDeck, Card
from poker_oracle import PokerOracle
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data.dataloader import DataLoader

import time

# MARK: MODEL
class NeuralNetwork(nn.Module):
    
    def __init__(self, input_size: int, output_size: int):
        super().__init__()
        
        self.fully_connected = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        self.p1_values = nn.Linear(128, output_size)
        self.p2_values = nn.Linear(128, output_size)
        
    def forward(self, x, is_limited):
        p1_range_indices = (0, 275) if is_limited else (0, 1325)
        p2_range_indices = (302, 577) if is_limited else (1380, 2705)
        
        p1_ranges = x[:, p1_range_indices[0]:p1_range_indices[1]]
        p2_ranges = x[:, p2_range_indices[0]:p2_range_indices[1]]
        
        x = self.fully_connected(x)
        
        p1_values = self.p1_values(x)
        p2_values = self.p2_values(x)
        
        # print(p1_ranges.shape, p1_values.shape)
        
        p1_dot = torch.tensordot(p1_ranges, p1_values, dims=2)
        p2_dot = torch.tensordot(p2_ranges, p2_values, dims=2)
        
        zero_sums = p1_dot - p2_dot
        
        return p1_values, p2_values, zero_sums
        

# MARK: TRAINING

class CustomLossFunction(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, p1_values, p2_values, zero_sums, p1_targets, p2_targets):
        p1_errors = (p1_values - p1_targets)**2
        p2_errors = (p2_values - p2_targets)**2
        zero_sums_error = (zero_sums)**2
        
        total_loss: torch.Tensor = p1_errors + p2_errors + zero_sums_error
        
        return total_loss.mean()


def train_model(model: nn.Module, inputs: np.ndarray, p1_targets: np.ndarray, p2_targets: np.ndarray, num_epochs: int, learning_rate: float, is_limited: bool): 

    inputs = torch.Tensor(inputs)
    p1_targets = torch.Tensor(p1_targets)
    p2_targets = torch.Tensor(p2_targets)

    optimizer = optim.Adam(model.parameters(), lr = learning_rate)
    custom_loss = CustomLossFunction()
    
    loss_list = []
    
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        p1_values, p2_values, zero_sums = model(inputs, is_limited)
        loss = custom_loss(p1_values, p2_values, zero_sums, p1_targets, p2_targets)
        loss.backward()
        optimizer.step()
        
        loss_list.append(loss.item())
        print(f"Epoch [{epoch+1}/{num_epochs}]: {loss.item()} ")        

    return model, np.asarray(loss_list)


def save_model_to_file(model: nn.Module, file_name: str):
    path = "./models/" + file_name + ".pt"
    torch.save(model, path)
    print(f"Model saved to {path}")


def load_model_from_file(file_name: str) -> nn.Module:
    path = "./models/" + file_name + ".pt"
    model: nn.Module = torch.load(path)
    model.eval()
    return model


def save_loss_plot(loss_list: np.ndarray, file_name: str):
    plt.plot(loss_list)
    path = "./loss/" + file_name
    plt.savefig(path)
    plt.close()
    print(f"Plot saved to {path}")


# MARK: DATA SET GENERATION

def generate_random_ranges(public_cards: list[Card], poker_oracle: PokerOracle):
    exclude_cards: list[str] = []
    for card in public_cards:
        card_key = str(card.get_rank()) + card.get_suit()
        exclude_cards.append(card_key)
        
    hole_pair_keys: list[str] = poker_oracle.get_all_hole_pair_keys()
    num_hole_pairs = len(hole_pair_keys)
    player1_range = np.zeros(num_hole_pairs)
    player2_range = np.zeros(num_hole_pairs)
    
    num_non_zero_probabilities = num_hole_pairs - len(public_cards)
    player1_random_probabilities = np.random.rand(num_non_zero_probabilities)
    player1_random_probabilities = player1_random_probabilities / np.sum(player1_random_probabilities)
    player2_random_probabilities = np.random.rand(num_non_zero_probabilities)
    player2_random_probabilities = player2_random_probabilities / np.sum(player2_random_probabilities)
    
    prob_index_1, prob_index_2 = 0, 0
    for i in range(num_hole_pairs):
        hole_pair_is_possible = True
        for card in exclude_cards:
            if card in hole_pair_keys[i]:
                hole_pair_is_possible = False
                break
        if hole_pair_is_possible:
            player1_range[i] = player1_random_probabilities[prob_index_1]
            player2_range[i] = player2_random_probabilities[prob_index_2]
            prob_index_1 += 1
            prob_index_2 += 1
            
    return player1_range, player2_range
    

def encode_public_cards(public_cards: list[Card], use_limited_deck: bool):       
    public_cards_strings: list[str] = [str(card) for card in public_cards]
    
    card_deck = CardDeck(use_limited_deck)
    num_cards = len(card_deck.cards)
    
    encoding = np.zeros(num_cards)
    for i, card in enumerate(card_deck.cards):
        if str(card) in public_cards_strings:
            encoding[i] = 1
            
    return encoding
    
    
# NOTE: Based on "Cheap method" from slides
def generate_training_data_for_stage(stage: str, num_cases: int, use_limited_deck: bool, save_to_file: bool):
    stage_to_num_public_cards = {
        "flop": 3,
        "turn": 4,
        "river": 5
    }

    # NOTE: Just picked some values that seemed reasonable:
    stage_max_pot = {
        "flop": 40,
        "turn": 60,
        "river": 80
    }
    
    num_public_cards = stage_to_num_public_cards[stage]
    
    poker_oracle = PokerOracle(use_limited_deck)
    
    training_data = []
    for _ in range(num_cases):
        card_deck = CardDeck(use_limited_deck)
        card_deck.shuffle()
        public_cards = card_deck.deal(num_public_cards)
        
        encoded_public_cards = encode_public_cards(public_cards, use_limited_deck)
        # print("Public cards", len(encoded_public_cards))
        
        p1_range, p2_range = generate_random_ranges(public_cards, poker_oracle)
        # print("Ranges",len(p1_range))
        
        utility_matrix, _ = poker_oracle.utility_matrix_generator(public_cards)
        
        p1_evaluation = np.squeeze(np.matmul(utility_matrix, np.atleast_2d(p2_range).T))
        p2_evaluation = -1 * np.matmul(p1_range, utility_matrix)
        
        # print("Evaluations",len(p1_evaluation))
        
        max_pot = stage_max_pot[stage]
        min_pot = max_pot // 4 # NOTE: Arbitrary scaling of max pot to reflect the fact that the minimum pot is different for each stage
        pot = np.random.randint(min_pot, max_pot, size=1)[0]
        relative_pot = [pot/max_pot]
        
        #NOTE: Length of ranges, evaluations, and public card encodings vary with the deck size
        # Deck size:            52   or 24
        # Encoded public cards: 52   or 24
        # Ranges:               1326 or 276
        # Evaluations:          1326 or 276
        # Total case length:    5357 or 1129
        training_case = [*p1_range, *encoded_public_cards, *relative_pot, *p2_range, *p1_evaluation, *p2_evaluation]
        training_data.append(training_case)
        # print(len(training_case))
    
    training_data = np.asarray(training_data)
    
    if save_to_file:
        if use_limited_deck:
            save_path = f"./training_data/limited_{stage}_{num_cases}"
        else:    
            save_path = f"./training_data/{stage}_{num_cases}"    
        np.save(save_path, training_data) 
        print(f"Saved to file {save_path}")
        
    return training_data


def load_data_set_from_file(file_name: str):
    training_data = np.load(f"./training_data/{file_name}.npy")
    
    is_limited = False
    if file_name.split("_")[0] == "limited":
        is_limited = True
    
    if not is_limited:
        # NOTE: Index ranges in each data case for REGULAR deck
        # p1_range:             0    - 1325
        # encoded_public_cards: 1326 - 1377
        # relative_pot:         1378 - 1379
        # p2_range:             1380 - 2705
        # p1_evaluation:        2706 - 4031
        # p2_evaluation:        4032 - 5356
        
        # Input indices:        0    - 2705
        # P1 target:            2706 - 4031
        # P2 target:            4032 - 5356
        input_indices = {
            "input": (0, 2705),
            "p1_target": (2706, 4031),
            "input": (4032, 5356)
        }
    else:
        # NOTE: Index ranges in each data case for LIMITED deck
        # p1_range:             0   - 275
        # encoded_public_cards: 276 - 299
        # relative_pot:         300 - 301
        # p2_range:             302 - 577
        # p1_evaluation:        578 - 853
        # p2_evaluation:        854 - 1129
        
        # Input indices:        0   - 577
        # P1 target:            578 - 853
        # P2 target:            854 - 1129
        input_indices = {
            "input": (0, 577),
            "p1_target": (578, 853),
            "p2_target": (854, 1129)
        }       
    
    inputs = training_data[:, input_indices["input"][0]:input_indices["input"][1]]
    p1_targets = training_data[:, input_indices["p1_target"][0]:input_indices["p1_target"][1]]
    p2_targets = training_data[:, input_indices["p2_target"][0]:input_indices["p2_target"][1]]
    
    # print(inputs.shape, p1_targets.shape, p2_targets.shape)
    
    return inputs, p1_targets, p2_targets

# MARK: MAIN
if __name__ == "__main__":
    
# ================ TRAIN MODELS ================
    train_models = False
    if train_models:
        # Get data sets
        flop_inputs, flop_p1_tragets, flop_p2_targets = load_data_set_from_file("limited_flop_10000")
        turn_inputs, turn_p1_tragets, turn_p2_targets = load_data_set_from_file("limited_turn_10000")
        river_inputs, river_p1_tragets, river_p2_targets = load_data_set_from_file("limited_river_1000")
        
        print("Flop:", flop_inputs.shape, flop_p1_tragets.shape, flop_p2_targets.shape)
        print("turn:", turn_inputs.shape, turn_p1_tragets.shape, turn_p2_targets.shape)
        print("River:", river_inputs.shape, river_p1_tragets.shape, river_p2_targets.shape)
        print()
        
        # Get model instances
        flop_network = NeuralNetwork(flop_inputs.shape[1], flop_p1_tragets.shape[1])
        turn_network = NeuralNetwork(turn_inputs.shape[1], turn_p1_tragets.shape[1])
        river_network = NeuralNetwork(river_inputs.shape[1], river_p1_tragets.shape[1])
        
        # Train and save networks. Save plots of training loss.
        num_epochs = 100 # NOTE: Seems to converge around 100 epochs.
        learning_rate = 0.001
        is_limited = True 
        
        print("Training flop network")
        flop_network, flop_training_loss = train_model(flop_network, flop_inputs, flop_p1_tragets, flop_p2_targets, num_epochs, learning_rate, is_limited)
        file_name = "flop_"
        file_name += "limited_" if is_limited else ""
        file_name += f"{num_epochs}epochs"
        save_loss_plot(flop_training_loss, file_name)
        save_model_to_file(flop_network, file_name)
        print()
        
        print("Training turn network")
        turn_network, turn_training_loss = train_model(turn_network, turn_inputs, turn_p1_tragets, turn_p2_targets, num_epochs, learning_rate, is_limited)
        file_name = "turn_"
        file_name += "limited_" if is_limited else ""
        file_name += f"{num_epochs}epochs"
        save_loss_plot(turn_training_loss, file_name)
        save_model_to_file(turn_network, file_name)
        print()
        
        print("Training river network")
        river_network, river_training_loss = train_model(river_network, river_inputs, river_p1_tragets, river_p2_targets, num_epochs, learning_rate, is_limited)
        file_name = "river_"
        file_name += "limited_" if is_limited else ""
        file_name += f"{num_epochs}epochs"
        save_loss_plot(river_training_loss, file_name)
        save_model_to_file(river_network, file_name)
        print()
    
    
# ================ GENERATE DATA ================
    generate_data = False
    if generate_data:
        is_limited_list = [True] # [True, False]
        stage_list = ["river"] # ["flop", "turn", "river"]
        num_cases =  1000 
        # NOTE: Generating one case takes about 1.5 seconds for the flop stage with a LIMITED deck. 
        # Will only generate data sets for limited decks, 10 000 for fop and turn. This takes almost 4 hours per stage.
        # Generating one case for RIVER stage takes about 6 seconds. I have therefore reduced the number of cases for river stage to 1000. 
        save_to_file = True

        for is_limited in is_limited_list:
            for stage in stage_list:
                start = time.time()
                if is_limited:
                    print(f"Generating {num_cases} cases for {stage} stage with limited deck")
                else:
                    print(f"Generating {num_cases} cases for {stage} stage with regular deck")
                generate_training_data_for_stage(stage, num_cases, is_limited, save_to_file)
                print(f"Finished in {time.time() - start:.2f} seconds.")

