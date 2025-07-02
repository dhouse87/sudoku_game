import tkinter as tk
import pandas as pd
import random
import time
import os
import pygame

SIZE = 9
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 700
CELL_WIDTH = 2
FONT_SIZE = 24

SOUND_DIR = r"C:\Users\david\OneDrive\Desktop\David\Programming\sudoku_game\sounds"

SOUNDS = {
    "start": os.path.join(SOUND_DIR, "puzzlestart.mp3"),
    "wrong": os.path.join(SOUND_DIR, "puzzlewrong.mp3"),
    "win": os.path.join(SOUND_DIR, "puzzlewin.mp3"),
    "lose": os.path.join(SOUND_DIR, "puzzlelose.mp3"),
    "right": os.path.join(SOUND_DIR, "puzzleright.mp3")
}

DIFFICULTY_SETTINGS = {
    "very easy": {"file": "very_easy.csv", "clues": (58, 66), "color": "pink"},
    "easy": {"file": "easy.csv", "clues": (50, 54), "color": "light green"},
    "medium": {"file": "medium.csv", "clues": (36, 49), "color": "light blue"},
    "hard": {"file": "hard.csv", "clues": (30, 35), "color": "orange"},
    "nightmare": {"file": "nightmare.csv", "clues": (17, 29), "color": "red"}
}

DIFFICULTY_DIR = r"C:\Users\david\OneDrive\Desktop\David\Programming\sudoku_game\difficulty"

pygame.mixer.init()

class SudokuGUI:
    def __init__(self, master):
        self.master = master
        master.title("PySudoku")
        master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        master.resizable(False, False)

        self.mistakes = 0
        self.max_mistakes = 3
        self.start_time = None
        self.solution = None
        self.puzzle = None
        self.initial_puzzle = None
        self.cells = {}
        self.overlay_frame = None
        self.completed_numbers = set()

        self.show_title_screen()

    def play_sound(self, sound_key):
        try:
            pygame.mixer.music.load(SOUNDS[sound_key])
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Sound error ({sound_key}): {e}")

    def show_title_screen(self):
        self.clear_frame()
        frame = tk.Frame(self.master, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        frame.pack(fill='both', expand=True)

        label = tk.Label(frame, text="PySudoku", font=('Arial', 48))
        label.pack(expand=True)

        self.master.after(3000, self.show_difficulty_selection)

    def clear_frame(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def show_difficulty_selection(self):
        self.clear_frame()
        frame = tk.Frame(self.master, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        frame.pack(fill='both', expand=True)

        label = tk.Label(frame, text="Select Difficulty", font=('Arial', 24))
        label.pack(pady=20)

        for level in DIFFICULTY_SETTINGS.keys():
            button = tk.Button(frame, text=level.capitalize(), font=('Arial', 16), width=20,
                               command=lambda lvl=level: self.start_game(lvl))
            button.pack(pady=5)

    def start_game(self, difficulty, from_restart=False):
        self.difficulty = difficulty
        self.mistakes = 0
        self.start_time = time.time()
        self.completed_numbers = set()

        self.clear_frame()
        bg = DIFFICULTY_SETTINGS[difficulty]["color"]
        self.current_frame = tk.Frame(self.master, bg=bg)
        self.current_frame.pack(fill='both', expand=True)

        self.top_frame = tk.Frame(self.current_frame, bg=bg)
        self.top_frame.pack(fill='x')

        self.info_label = tk.Label(self.top_frame, text=self.get_info_text(), font=('Arial', 14), bg=bg)
        self.info_label.pack()

        self.timer_label = tk.Label(self.top_frame, text="Time: 0s", font=('Arial', 14), bg=bg)
        self.timer_label.pack()

        self.button_frame = tk.Frame(self.current_frame, bg=bg)
        self.button_frame.pack(pady=5)

        back_btn = tk.Button(self.button_frame, text="Back", font=('Arial', 10), width=8, command=self.back_prompt)
        back_btn.pack(side='left', padx=5)

        restart_btn = tk.Button(self.button_frame, text="Restart", font=('Arial', 10), width=8, command=self.restart_prompt)
        restart_btn.pack(side='left', padx=5)

        self.grid_frame = tk.Frame(self.current_frame, bg=bg)
        self.grid_frame.pack(pady=20)

        if from_restart and self.initial_puzzle:
            self.puzzle = [row.copy() for row in self.initial_puzzle]
            self.draw_grid()
        else:
            self.load_random_puzzle()

        self.play_sound("start")
        self.update_timer()

    def show_overlay(self, text, buttons):
        if self.overlay_frame:
            self.overlay_frame.destroy()
        self.overlay_frame = tk.Frame(self.current_frame, bg="white", bd=2, relief='ridge')
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor='center')

        label = tk.Label(self.overlay_frame, text=text, font=('Arial', 14), bg="white")
        label.pack(pady=10, padx=10)

        btn_frame = tk.Frame(self.overlay_frame, bg="white")
        btn_frame.pack(pady=5)

        for btn_text, btn_cmd in buttons:
            btn = tk.Button(btn_frame, text=btn_text, width=8, command=lambda cmd=btn_cmd: self.close_overlay(cmd))
            btn.pack(side='left', padx=5)

    def close_overlay(self, action):
        if self.overlay_frame:
            self.overlay_frame.destroy()
            self.overlay_frame = None
        action()

    def back_prompt(self):
        self.show_overlay("Back to difficulty selection?", [
            ("Yes", self.show_difficulty_selection),
            ("No", lambda: None)
        ])

    def restart_prompt(self):
        self.show_overlay("Restart game?", [
            ("Yes", lambda: self.start_game(self.difficulty, from_restart=True)),
            ("No", lambda: None)
        ])

    def show_info_overlay(self, text, next_action):
        self.show_overlay(text, [
            ("OK", next_action)
        ])

    def get_info_text(self):
        return f"Difficulty: {self.difficulty.capitalize()}   Mistakes: {self.mistakes}/{self.max_mistakes}"

    def update_timer(self):
        if not self.start_time:
            return
        if not self.timer_label.winfo_exists():
            return
        elapsed = int(time.time() - self.start_time)
        self.timer_label.config(text=f"Time: {elapsed}s")
        self.master.after(1000, self.update_timer)

    def load_random_puzzle(self):
        setting = DIFFICULTY_SETTINGS[self.difficulty]
        file_path = os.path.join(DIFFICULTY_DIR, setting["file"])
        clues_range = setting["clues"]

        try:
            df = pd.read_csv(file_path, header=None)
            solutions = df[0].astype(str).tolist()
        except Exception:
            self.show_info_overlay(f"Error loading {setting['file']}", self.show_difficulty_selection)
            return

        solution_str = random.choice(solutions)
        clues = random.randint(*clues_range)

        positions = list(range(81))
        random.shuffle(positions)
        reveal_pos = set(positions[:clues])

        puzzle_str = ''.join(
            solution_str[i] if i in reveal_pos else '0'
            for i in range(81)
        )

        self.solution = [[int(solution_str[i * SIZE + j]) for j in range(SIZE)] for i in range(SIZE)]
        self.puzzle = [[int(puzzle_str[i * SIZE + j]) for j in range(SIZE)] for i in range(SIZE)]
        self.initial_puzzle = [row.copy() for row in self.puzzle]

        self.draw_grid()

    def draw_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.cells.clear()

        for r in range(SIZE):
            for c in range(SIZE):
                cell = tk.Entry(self.grid_frame, width=CELL_WIDTH, font=('Arial', FONT_SIZE),
                                justify='center', relief='solid', bd=1)

                top = 3 if r % 3 == 0 else 1
                left = 3 if c % 3 == 0 else 1
                bottom = 3 if r == SIZE - 1 else 1
                right = 3 if c == SIZE - 1 else 1

                cell.grid(row=r, column=c, ipadx=10, ipady=10,
                          padx=(left, right), pady=(top, bottom))

                if self.puzzle[r][c] != 0:
                    cell.insert(0, str(self.puzzle[r][c]))
                    cell.config(state='disabled', disabledforeground='black')
                else:
                    cell.bind("<KeyRelease>", lambda e, row=r, col=c: self.validate_input(row, col))

                self.cells[(r, c)] = cell

    def validate_input(self, row, col):
        val = self.cells[(row, col)].get()
        if not val.isdigit() or not (1 <= int(val) <= 9):
            self.cells[(row, col)].delete(0, tk.END)
            return
        if int(val) in self.completed_numbers:
            self.cells[(row, col)].delete(0, tk.END)
            return
        if int(val) == self.solution[row][col]:
            self.cells[(row, col)].config(fg='blue')
            self.check_and_mark_completed_numbers()
        else:
            self.mistakes += 1
            self.info_label.config(text=self.get_info_text())
            self.flash_red_then_clear(self.cells[(row, col)])
            self.play_sound("wrong")
            if self.mistakes >= self.max_mistakes:
                self.play_sound("lose")
                self.show_info_overlay("Three strikes and you're out! You lose.",
                                       lambda: self.start_game(self.difficulty))
                return

        if self.check_win():
            self.play_sound("win")
            self.show_info_overlay("You completed the puzzle! Great job!",
                                   lambda: self.start_game(self.difficulty))

    def check_and_mark_completed_numbers(self):
        for num in range(1, 10):
            if num in self.completed_numbers:
                continue
            needed = sum(row.count(num) for row in self.solution)
            placed = sum(
                1 for (r, c), cell in self.cells.items()
                if cell.get().isdigit() and int(cell.get()) == num
            )
            if placed == needed:
                self.completed_numbers.add(num)
                for (r, c), cell in self.cells.items():
                    if cell.get().isdigit() and int(cell.get()) == num:
                        cell.config(fg='green')
                self.play_sound("right")

    def flash_red_then_clear(self, cell):
        cell.config(fg='red')
        cell.after(300, lambda: (cell.delete(0, tk.END), cell.config(fg='black')))

    def check_win(self):
        for r in range(SIZE):
            for c in range(SIZE):
                val = self.cells[(r, c)].get()
                if val == "" or int(val) != self.solution[r][c]:
                    return False
        return True

if __name__ == "__main__":
    root = tk.Tk()
    game = SudokuGUI(root)
    root.mainloop()
