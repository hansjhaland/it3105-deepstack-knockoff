from poker_oracle import PokerOracle
from card_deck import Card

use_limited = True

poker_oracle = PokerOracle(use_limited)

max_num_opponents = 4 
num_rollouts = 10

cheat_sheet = poker_oracle.generate_and_save_cheat_sheet(max_num_opponents, num_rollouts)

[print(row) for row in cheat_sheet]

# NOTE: First row in cheat sheet
hole_pair1 = [
    Card("S", 9),
    Card("S", 10)
]

# NOTE: Third row in cheat sheet
hole_pair2 = [
    Card("S", 9),
    Card("S", 12)
]

print(poker_oracle.get_cheat_sheet_hole_pair_probabilitiy(hole_pair1, 1, cheat_sheet))
print(poker_oracle.get_cheat_sheet_hole_pair_probabilitiy(hole_pair2, 2, cheat_sheet))
print(poker_oracle.get_cheat_sheet_hole_pair_probabilitiy(hole_pair2, 3, cheat_sheet))