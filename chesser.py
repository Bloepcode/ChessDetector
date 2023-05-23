import shutil
import collections
from subprocess import DEVNULL, STDOUT, check_call
import chess.svg
import pyperclip
import chess.engine
import math
import chess.pgn
from dataclass import Config
from out import out
from rich import print
import os
import chess
from time import sleep
from reader import Reader


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


USE_XBOARD = True

NUM_TO_LETTER = {
    0: 'a',
    1: 'b',
    2: 'c',
    3: 'd',
    4: 'e',
    5: 'f',
    6: 'g',
    7: 'h'
}


class Chesser:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.board = chess.Board()
        self.engine = chess.engine.SimpleEngine.popen_uci(
            "/opt/homebrew/bin/stockfish")

        self.reader = Reader(config)

        self.player_color = chess.WHITE

        self.game = chess.pgn.Game()
        self.game.headers["White"] = "player"
        self.game.headers["Black"] = "stockfish"
        self.game.setup(self.board)
        self.node = self.game

        if os.path.exists("moves.txt"):
            print("Detected moves...")
            with open("moves.txt", "r") as f:
                lines = f.readlines()
            for line in lines:
                if line == "":
                    continue
                self.node = self.node.add_variation(
                    chess.Move.from_uci(line[:4]))
                self.board.push_uci(line[:4])

    def print_status(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("[green on black]ChessDetector![/green on black]")
        print(
            f"[blue]Het is [cyan]{'jouw' if self.board.turn == self.player_color else 'de computers'}[/cyan] beurt...[/blue]")
        if self.board.turn == self.player_color:
            info = self.engine.analyse(
                self.board, chess.engine.Limit(depth=20))
            size = shutil.get_terminal_size((80, 20))
            try:
                score = sigmoid(info["score"].pov(
                    self.board.turn).score() / 100)
            except:
                print("ERR")
                score = 0
            width = round(size.columns*score)

            print(
                f"[blue]{'#'*width}[/blue][yellow]{'#'*(size.columns-width)}[/yellow]")
            print(score)

            # print("[green]" + "#"*width + "[/green]" + "")

    def convert_move(self, a, b):
        if self.board.color_at(chess.square(
                a[0], 7-a[1])) == self.board.turn:
            return chess.Move(chess.square(
                a[0], 7-a[1]), chess.square(b[0], 7-b[1])).uci()
        else:
            return chess.Move(chess.square(
                b[0], 7-b[1]), chess.square(a[0], 7-a[1])).uci()

        # if self.board.color_at(chess.parse_square(f"{NUM_TO_LETTER[a[0]]}{7-a[1]+1}")) == self.board.turn:
        #     return f"{NUM_TO_LETTER[a[0]]}{7-a[1]+1}{NUM_TO_LETTER[b[0]]}{7-b[1]+1}"
        # else:
        #     return f"{NUM_TO_LETTER[b[0]]}{7-b[1]+1}{NUM_TO_LETTER[a[0]]}{7-a[1]+1}"

    def mainloop(self):
        out("Welkom bij chesser!")

        while True:
            self.print_status()
            if self.board.is_game_over():
                out("Game over...")
                exit()
            if self.board.turn == self.player_color:
                out("\nJij bent aan zet...", wait=False)
                waiting = True
                while waiting:
                    try:
                        move_raw = self.reader.wait_for_move()
                        move_str = self.convert_move(move_raw[0], move_raw[1])
                        break
                    except KeyboardInterrupt:
                        while True:
                            print("Geanuleerd")
                            print("Opties:")
                            print("    1) Herstart")
                            print("    2) Handmatig")
                            print("    3) Export PGN")
                            option = input("Kies: ")

                            if option == "1":
                                out("Geherstart!", wait=False)
                                break
                            elif option == "2":
                                while True:
                                    try:
                                        move_str = input("Zet: ")
                                        chess.Move.from_uci(move_str)
                                        waiting = False
                                        break
                                    except ValueError:
                                        print("Vul een goede UCI zet in...")
                                break
                            elif option == "3":
                                self.export_pgn()
                            else:
                                print("Kies uit 1 tot 3!")

                move = chess.Move.from_uci(move_str)

                if move in self.board.legal_moves:
                    if self.board.is_castling(move):
                        out("Rokeren gedetecteerd, verplaats nu de toren...")
                        try:
                            self.reader.wait_for_move()
                        except KeyboardInterrupt:
                            print("Geanuleerd")
                    self.push_move(move_str)
                    self.board.push(move)
                    self.write_board(move)
                    out(f"Zet {move_str} successvol!")
                else:
                    out(f"Zet {move_str} mag niet!")
                    input("Druk op enter als je het stukje hebt terug gezet...")
            else:
                out("Chesser is aan zet...", wait=True)
                while True:
                    try:
                        result = self.engine.play(
                            self.board, limit=chess.engine.Limit(time=0.1))
                        break
                    except chess.engine.EngineTerminatedError:
                        self.engine = chess.engine.SimpleEngine.popen_uci(
                            "/opt/homebrew/bin/stockfish")
                self.board.push(result.move)
                self.push_move(str(result.move))
                self.write_board(result.move)
                out(f"Chesser kiest zet {str(result.move)}")
                sleep(1.5)
                try:
                    self.reader.wait_for_move()
                except KeyboardInterrupt:
                    print("Geanuleerd")

    def push_move(self, move):
        self.node = self.node.add_variation(move)
        with open("moves.txt", "a") as f:
            f.write(move + "\n")

    def board_to_game(self):
        game = chess.pgn.Game()

        # Undo all moves.
        switchyard = collections.deque()
        while self.board.move_stack:
            switchyard.append(self.board.pop())

        game.setup(self.board)
        node = game

        # Replay all moves.
        while switchyard:
            move = switchyard.pop()
            node = node.add_variation(move)
            self.board.push(move)

        game.headers["Result"] = self.board.result()
        return game

    def export_pgn(self):
        game = self.board_to_game()
        with open("pgn.txt", "w") as f:
            exporter = chess.pgn.FileExporter(f)
            game.accept(exporter)
        pyperclip.copy(str(game))

    def write_board(self, move: chess.Move):
        board = chess.Board()
        board.clear_board()
        board.set_piece_at(move.to_square, self.board.piece_at(move.to_square))

        svg_code = chess.svg.board(
            board,
            size=350,
            lastmove=move
        )

        with open("tmp.svg", "w") as f:
            f.write(svg_code)

        # os.system(
        #     "/Applications/Inkscape.app/Contents/MacOS/inkscape -z -f tmp.svg -w 2048 -j -e board.png")

        check_call(["/Applications/Inkscape.app/Contents/MacOS/inkscape", "tmp.svg", "-o", "board.png"],
                   stdout=DEVNULL, stderr=STDOUT)
        os.remove("tmp.svg")
