import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt

# Define card strengths (3 is lowest, 2 is highest)
CARD_VALUES = {'3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6, '9': 7,
               '10': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12, '2': 13}
SUITS = ['♠', '♥', '♦', '♣']


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = CARD_VALUES[rank]

    def __repr__(self):
        return f"{self.rank}{self.suit}"


class TycoonGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Persona 5 Royal: Tycoon (PyQt5)")
        self.setGeometry(100, 100, 900, 600)

        # Game State
        self.deck = [Card(r, s) for r in CARD_VALUES for s in SUITS]
        random.shuffle(self.deck)

        # 4 Players: Player 0 (Human), Player 1-3 (AI)
        self.hands = [[] for _ in range(4)]
        self.deal_cards()

        self.current_trick = []  # Cards currently on the table
        self.trick_rank_value = 0  # Value of the card(s) to beat
        self.trick_card_count = 0  # Number of cards required to play (e.g., pairs, triples)
        self.turn = 0  # Start with Player 0 for simplicity
        self.pass_count = 0
        self.selected_cards = []

        self.init_ui()
        self.update_ui()

    def deal_cards(self):
        # Deal whole deck evenly (13 cards each)
        for i in range(52):
            self.hands[i % 4].append(self.deck[i])
        # Sort human hand by value
        self.hands[0].sort(key=lambda c: c.value)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Top: AI Status
        # Top: AI Status
        self.ai_layout = QHBoxLayout()
        self.ai_labels = []  # This list exists...
        for i in range(1, 4):
            lbl = QLabel(f"AI {i}: {len(self.hands[i])} cards")
            lbl.setStyleSheet(
                "font-size: 14px; border: 1px solid gray; padding: 10px; background-color: #2b2b2b; color: white;")
            self.ai_layout.addWidget(lbl)
            self.ai_labels.append(lbl)  # <-- FIX: Add this line to populate the list!

        main_layout.addLayout(self.ai_layout)

        # Middle: Table / Arena
        self.table_label = QLabel("Table: Empty")
        self.table_label.setAlignment(Qt.AlignCenter)
        self.table_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; min-height: 100px; background-color: #1a4a1a; color: white; border-radius: 8px;")
        main_layout.addWidget(self.table_label)

        # Log History
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(120)
        main_layout.addWidget(self.log_box)

        # Bottom: Player Hand & Controls
        self.hand_layout = QHBoxLayout()
        main_layout.addLayout(self.hand_layout)

        control_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play Selected")
        self.play_btn.clicked.connect(self.player_play)
        self.pass_btn = QPushButton("Pass")
        self.pass_btn.clicked.connect(self.player_pass)

        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.pass_btn)
        main_layout.addLayout(control_layout)

    def update_ui(self):
        # Update AI Card Counts
        for i in range(1, 4):
            self.ai_labels[i - 1].setText(f"AI {i}: {len(self.hands[i])} cards")

        # Update Table
        if self.current_trick:
            cards_str = ", ".join([str(c) for c in self.current_trick])
            self.table_label.setText(f"Table to Beat: {cards_str}")
        else:
            self.table_label.setText("Table: Free Play (Any card/pair)")

        # Clear and redraw Player Hand
        for i in reversed(range(self.hand_layout.count())):
            self.hand_layout.itemAt(i).widget().setParent(None)

        self.selected_cards.clear()
        for card in self.hands[0]:
            btn = QPushButton(str(card))
            btn.setCheckable(True)
            btn.setFixedSize(50, 80)
            btn.setStyleSheet("background-color: white; color: black; font-size: 16px; font-weight: bold;")
            # Style when checked (Phantom Thief Red!)
            btn.toggled.connect(lambda checked, c=card: self.card_toggled(checked, c))
            self.hand_layout.addWidget(btn)

    def card_toggled(self, checked, card):
        if checked:
            self.selected_cards.append(card)
        else:
            if card in self.selected_cards:
                self.selected_cards.remove(card)

    def log(self, text):
        self.log_box.append(text)

    def verify_move(self, cards):
        if not cards:
            return False
        # All selected cards must have the same rank (single, pair, triple, etc.)
        rank = cards[0].rank
        if not all(c.rank == rank for c in cards):
            return False

        card_val = cards[0].value

        # If it's a free play
        if self.trick_card_count == 0:
            return True

        # Must match the amount of cards on the table and be higher value
        if len(cards) == self.trick_card_count and card_val > self.trick_rank_value:
            return True

        return False

    def player_play(self):
        if self.turn != 0:
            return

        if self.verify_move(self.selected_cards):
            self.current_trick = list(self.selected_cards)
            self.trick_rank_value = self.selected_cards[0].value
            self.trick_card_count = len(self.selected_cards)

            for c in self.selected_cards:
                self.hands[0].remove(c)

            self.log(f"You played: {', '.join([str(x) for x in self.current_trick])}")
            self.pass_count = 0
            self.check_win_condition(0)
            self.next_turn()
        else:
            QMessageBox.warning(self, "Invalid Move", "You must play matching ranks higher than the current table.")

    def player_pass(self):
        if self.turn != 0:
            return
        self.log("You passed.")
        self.pass_count += 1
        self.next_turn()

    def next_turn(self):
        if self.pass_count >= 3:
            self.current_trick = []
            self.trick_rank_value = 0
            self.trick_card_count = 0
            self.pass_count = 0
            self.log("--- Everyone passed! Table Cleared. ---")

        self.turn = (self.turn + 1) % 4
        self.update_ui()

        if self.turn != 0:
            self.ai_turn()

    def ai_turn(self):
        ai_hand = self.hands[self.turn]
        if not ai_hand:  # AI already out
            self.pass_count += 1
            self.next_turn()
            return

        # Simple AI Strategy: Group hand by ranks
        groups = {}
        for card in ai_hand:
            groups.setdefault(card.rank, []).append(card)

        played = False
        # Try to find a valid move
        for rank, cards in groups.items():
            # If free play, AI plays its lowest single card
            if self.trick_card_count == 0:
                play_cards = [cards[0]]
                self.execute_ai_move(play_cards, ai_hand)
                played = True
                break
            # Matching trick count and higher value
            elif len(cards) >= self.trick_card_count and cards[0].value > self.trick_rank_value:
                play_cards = cards[:self.trick_card_count]
                self.execute_ai_move(play_cards, ai_hand)
                played = True
                break

        if not played:
            self.log(f"AI {self.turn} passed.")
            self.pass_count += 1
            self.next_turn()

    def execute_ai_move(self, play_cards, ai_hand):
        self.current_trick = play_cards
        self.trick_rank_value = play_cards[0].value
        self.trick_card_count = len(play_cards)

        for c in play_cards:
            ai_hand.remove(c)

        self.log(f"AI {self.turn} played: {', '.join([str(x) for x in play_cards])}")
        self.pass_count = 0
        self.check_win_condition(self.turn)
        self.next_turn()

    def check_win_condition(self, player_idx):
        if len(self.hands[player_idx]) == 0:
            role = "Tycoon" if player_idx == 0 else f"AI {player_idx}"
            QMessageBox.information(self, "Round Over", f"{role} has shed all cards!")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = TycoonGame()
    game.show()
    sys.exit(app.exec_initiate if hasattr(sys.argv, 'exec_initiate') else app.exec_())