from game import Minesweeper
from board import Board


def test_neighbors_corner_are_valid():
    b = Board(rows=3, cols=3, mines=0)
    assert set(b.neighbors(0, 0)) == {(0, 1), (1, 0), (1, 1)}


def test_neighbors_edge_are_valid():
    b = Board(rows=3, cols=3, mines=0)
    assert set(b.neighbors(0, 1)) == {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}


def test_neighbors_center_are_valid():
    b = Board(rows=3, cols=3, mines=0)
    expected = {
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 2),
    }
    assert set(b.neighbors(1, 1)) == expected


def test_reveal_flagged_cell_does_not_change_state():
    b = Board(rows=2, cols=2, mines=0)
    b.flags.add((0, 0))
    assert b.reveal((0, 0)) is False
    assert b.revealed == set()
    assert (0, 0) in b.flags


def test_reveal_out_of_bounds_does_not_change_state():
    b = Board(rows=2, cols=2, mines=0)
    assert b.reveal((-1, 0)) is False
    assert b.revealed == set()


def test_toggle_flag_invalid_coords_no_state_change():
    b = Board(rows=2, cols=2, mines=0)
    before_flags = set(b.flags)
    before_revealed = set(b.revealed)
    assert b.toggle_flag((5, 5)) is False
    assert b.flags == before_flags
    assert b.revealed == before_revealed


def test_won_requires_all_non_mine_cells_revealed():
    b = Board(rows=2, cols=2, mines=1)
    b.mines = {(0, 0)}
    for pos in {(0, 1), (1, 0), (1, 1)}:
        b.revealed.add(pos)
    assert b.won() is True

    b.revealed.remove((1, 1))
    assert b.won() is False


def test_game_reports_flagged_reveal_attempt(monkeypatch, capsys):
    game = Minesweeper()
    inputs = iter(["easy", "f 1 1", "r 1 1", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    game.run()

    captured = capsys.readouterr().out
    assert "Cell is flagged. Unflag it before revealing." in captured
    assert (0, 0) in game.board.flags
    assert (0, 0) not in game.board.revealed


def test_flag_commands_print_one_feedback_line_each(monkeypatch, capsys):
    game = Minesweeper()
    inputs = iter(["easy", "f 1 1", "f 1 1", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    game.run()

    output = capsys.readouterr().out
    assert output.count("Flagged row 1, column 1.") == 1
    assert output.count("Unflagged row 1, column 1.") == 1


def test_flood_fill_prints_only_one_reveal_feedback_line(monkeypatch, capsys):
    import game as game_module

    board = Board(rows=3, cols=3, mines=0)
    monkeypatch.setattr(game_module, "Board", lambda *args: board)
    inputs = iter(["easy", "r 1 1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    minesweeper = Minesweeper()

    minesweeper.run()

    output = capsys.readouterr().out
    assert output.count("Revealed row 1, column 1.") == 1
    assert len(board.revealed) == 9
    assert "You cleared the board!" in output


def test_mine_reveal_prints_one_feedback_line(monkeypatch, capsys):
    import game as game_module

    board = Board(rows=2, cols=2, mines=1)
    board.mines = {(0, 0)}
    monkeypatch.setattr(game_module, "Board", lambda *args: board)
    inputs = iter(["easy", "r 1 1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    minesweeper = Minesweeper()

    minesweeper.run()

    output = capsys.readouterr().out
    assert output.count("BOOM! Reveal at row 1, column 1 hit a mine.") == 1


def test_difficulty_selection_sets_board_size_and_mine_count(monkeypatch):
    for difficulty, expected in Minesweeper.DIFFICULTIES.items():
        game = Minesweeper()
        inputs = iter([difficulty, "q"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        game.run()

        assert (game.board.rows, game.board.cols, game.board.mine_total) == expected
        assert len(game.board.mines) == expected[2]


def test_invalid_difficulty_reprompts_without_changing_commands(monkeypatch, capsys):
    game = Minesweeper()
    inputs = iter(["impossible", "medium", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    game.run()

    output = capsys.readouterr().out
    assert "Choose easy, medium, or hard." in output
    assert "Commands: r row col | f row col | q" in output
    assert (game.board.rows, game.board.cols, game.board.mine_total) == (10, 10, 15)


def test_display_aligns_columns_for_boards_wider_than_nine(capsys):
    game = Minesweeper()
    game.board = Board(rows=12, cols=12, mines=0)

    game.display()

    lines = capsys.readouterr().out.splitlines()
    header = lines[1]
    first_row = lines[2]
    assert len(header) == len(first_row)
    assert first_row[header.index("10") + 1] == "#"
