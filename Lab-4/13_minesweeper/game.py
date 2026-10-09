from board import Board


class Minesweeper:
    DIFFICULTIES = {
        "easy": (6, 6, 6),
        "medium": (10, 10, 15),
        "hard": (16, 16, 40),
    }

    def __init__(self):
        self.board = Board()

    def display(self, reveal_mines=False):
        b = self.board
        row_width = len(str(b.rows))
        col_width = len(str(b.cols))
        print(
            "\n"
            + " " * (row_width + 1)
            + " ".join(f"{c + 1:>{col_width}}" for c in range(b.cols))
        )
        for r in range(b.rows):
            cells = []
            for c in range(b.cols):
                pos = (r, c)
                if reveal_mines and pos in b.mines:
                    ch = "*"
                elif pos in b.flags:
                    ch = "F"
                elif pos not in b.revealed:
                    ch = "#"
                elif pos in b.mines:
                    ch = "*"
                else:
                    ch = str(b.adjacent_mines(r, c))
                cells.append(f"{ch:>{col_width}}")
            print(f"{r + 1:>{row_width}} " + " ".join(cells))

    def run(self):
        print("Minesweeper")
        while True:
            difficulty = input("Choose difficulty (easy/medium/hard): ").strip().lower()
            if difficulty in self.DIFFICULTIES:
                self.board = Board(*self.DIFFICULTIES[difficulty])
                break
            print("Choose easy, medium, or hard.")
        print("Commands: r row col | f row col | q")
        while True:
            self.display()
            raw = input("> ").strip().lower()
            if raw == "q":
                return
            parts = raw.split()
            if len(parts) != 3 or parts[0] not in {"r", "f"}:
                print("Use r row col or f row col.")
                continue
            try:
                r, c = int(parts[1]) - 1, int(parts[2]) - 1
            except ValueError:
                print("Coordinates must be numbers.")
                continue
            if not self.board.in_bounds(r, c):
                print("Outside the board.")
                continue

            if parts[0] == "f":
                if not self.board.toggle_flag((r, c)):
                    print("Cannot flag a revealed cell.")
                elif (r, c) in self.board.flags:
                    print(f"Flagged row {r + 1}, column {c + 1}.")
                else:
                    print(f"Unflagged row {r + 1}, column {c + 1}.")
                continue

            if (r, c) in self.board.flags:
                print("Cell is flagged. Unflag it before revealing.")
                continue

            hit_mine = self.board.reveal((r, c))
            if hit_mine:
                print(f"BOOM! Reveal at row {r + 1}, column {c + 1} hit a mine.")
                self.display(reveal_mines=True)
                return
            print(f"Revealed row {r + 1}, column {c + 1}.")
            if self.board.won():
                self.display()
                print("You cleared the board!")
                return
