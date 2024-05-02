from card_deck import Card
from poker_oracle import PokerOracle

# MARK: Hand classification

#==== ROYAL FLUSH ====
royal_flush = [
    Card('D',14),
    Card('D',13),
    Card('D',12),
    Card('D',11),
    Card('D',10)
]

#==== STRAIGHT FLUSH ====
straight_flush_1 = [
    Card('C',8),
    Card('C',7),
    Card('C',6),
    Card('C',5),
    Card('C',4)
]

straight_flush_2 = [
    Card('C',7),
    Card('C',6),
    Card('C',5),
    Card('C',4),
    Card('C',3)
]

#==== FOUR OF A KIND ====
four_of_a_kind_1 = [
    Card('H',11),
    Card('D',11),
    Card('S',11),
    Card('C',11),
    Card('D',7),
]

four_of_a_kind_2 = [
    Card('H',2),
    Card('D',2),
    Card('S',2),
    Card('C',2),
    Card('D',12),
]

#==== FULL HOUSE ====
full_house_1 = [
    Card('H', 10),
    Card('D', 10),
    Card('S', 10),
    Card('C', 9),
    Card('D', 9)
]

full_house_2 = [
    Card('H', 11),
    Card('D', 11),
    Card('S', 11),
    Card('C', 9),
    Card('D', 9)
]

full_house_3 = [
    Card('H', 10),
    Card('D', 10),
    Card('S', 10),
    Card('C', 11),
    Card('D', 11)
]

#==== FLUSH ====
flush_1 = [
    Card('S', 4),
    Card('S', 11),
    Card('S', 8),
    Card('S', 2),
    Card('S', 9)
]

flush_2 = [
    Card('S', 4),
    Card('S', 11),
    Card('S', 8),
    Card('S', 3),
    Card('S', 14)
]

#==== STRAIGHT ====
straight_1 = [
    Card('C',8),
    Card('D',7),
    Card('S',6),
    Card('C',5),
    Card('H',4)
]

straight_2 = [
    Card('D',7),
    Card('D',6),
    Card('C',5),
    Card('S',4),
    Card('H',3)
]

#==== THREE OF A KIND ====
three_of_a_kind_1 = [
    Card('C',7),
    Card('D',7),
    Card('S',7),
    Card('C',13),
    Card('D',3),
]

#==== TWO PAIR ====
two_pair_1 = [
    Card('C',4),
    Card('S',4),
    Card('C',3),
    Card('D',3),
    Card('C',12)
]

#==== PAIR ====
pair_1 = [
    Card('H',14),
    Card('D',14),
    Card('C',8),
    Card('S',4),
    Card('H',7)
]

#==== HIGH CARD ====
high_card = [
    Card('D',3),
    Card('S',11),
    Card('S',8),
    Card('H',4),
    Card('S',2),
]

po = PokerOracle()

print(po.hand_classifier(royal_flush)[0], "royal_flush")  
print(po.hand_classifier(straight_flush_1)[0], "straight_flush")  
print(po.hand_classifier(four_of_a_kind_1)[0], "four_of_a_kind")
print(po.hand_classifier(full_house_1)[0], "full_house")
print(po.hand_classifier(flush_1)[0], "flush")
print(po.hand_classifier(straight_1)[0], "straight") 
print(po.hand_classifier(three_of_a_kind_1)[0], "three_of_a_kind" )
print(po.hand_classifier(two_pair_1)[0], "two_pair") 
print(po.hand_classifier(pair_1)[0], "pair") 
print(po.hand_classifier(high_card)[0], "high_card")
print()


# MARK: Showdown evaluation

# Check both players same hand ranking 
public_cards = [
    Card('D', 7),
    Card('S', 6),
    Card('C', 5),
    Card('C', 2),
    Card('H', 10)
]

p1_hole_cards = [
    Card('S', 8),
    Card('H', 4)
]

p2_hole_cards = [
    Card('S', 4),
    Card('H', 3)
]

# P1 should win
print("Evaluation, same hand ranking:", po.evaluate_showdown(public_cards, p1_hole_cards, p2_hole_cards), "Target:", 1)

# Check both players different hand ranking
public_cards = [
    Card('D', 4),
    Card('S', 4),
    Card('C', 3),
    Card('C', 2),
    Card('H', 10)
]

p1_hole_cards = [
    Card('S', 3),
    Card('H', 8)
]

p2_hole_cards = [
    Card('S', 4),
    Card('H', 3)
]

# P2 should win
print("Evaluation, different hand ranking", po.evaluate_showdown(public_cards, p1_hole_cards, p2_hole_cards), "Target:", -1)

# p2 shuld win
print("Evaluation, different hand ranking, 3 public cards", po.evaluate_showdown(public_cards[:-2], p1_hole_cards, p2_hole_cards), "Target:", -1)
print()


# MARK: Rollout evaluation

# Test rollout evaluation
public_cards = [
    Card('D', 11),
    Card('S', 12),
    Card('C', 13),
    Card('C', 2),
    Card('H', 4)
]

hole_pair = [
    Card('S', 14),
    Card('H', 10)
]

num_opponents = 4
num_rollouts = 100

print("Rollout hole pair evaluator:", po.rollout_hole_pair_evaluator(hole_pair, public_cards, num_opponents, num_rollouts))



# utility_matrix, hole_pair_keys = po.utility_matrix_generator(public_cards)

# for key in list(utility_matrix.keys()):
#     print(key, utility_matrix[key])

# cheat_sheet = po.poker_cheat_sheet_generator(3, 100)
# for key in list(cheat_sheet.keys()):
#     print(key, cheat_sheet[key])
    
# print(po.get_cheat_sheet_hole_pair_probabilitiy(hole_pair, 2, cheat_sheet))
