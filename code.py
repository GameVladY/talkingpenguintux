import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, Entry, Button, Menu, Label, Frame
import random
import google.generativeai as genai
import os
import datetime
import platform
import sys
import webbrowser
import math
import re # NEW: Import for Regular Expressions (for AI parsing)

# --- Configuration ---
GEMINI_MODEL_NAME = "gemini-2.5-flash"
WEBSITE_URL = "https://sites.google.com/view/verycooltalkinglinuxpenguintux/"

# --- Design ---
BG_COLOR = "#2E2E2E"
FG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#4A4A4A"
BUTTON_HOVER_COLOR = "#5A5A5A"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"

# --- PERMISSION ERROR FIX & FIRST RUN FLAG ---
HOME_DIR = os.path.expanduser('~')
API_KEY_FILE = os.path.join(HOME_DIR, "gemini_api_key.txt")
FIRST_RUN_FLAG_FILE = os.path.join(HOME_DIR, ".tux_pet_first_run_complete")

class PenguinPet:
    def __init__(self, root):
        self.root = root
        self.name = "Tux"
        self.mood = "normal"
        self.api_key = self.load_api_key()
        self.gemini_model = None
        self.chat_session = None
        self.current_bubble = None
        self.ai_controls_window = None
        self.custom_menu = None
        self.ai_settings_menu = None # NEW: Tracks the AI settings submenu

        # --- State Variables ---
        self.body_type = "normal" # "normal" or "skinny"
        self.force_mood = None # "normal", "happy", "sad", "angry", or None for auto
        self.ai_personality = self.get_default_system_instruction()

        # --- NPC Movement State ---
        self.is_moving = False
        self.wander_enabled = True
        self.walk_frame = 0
        self.target_x = None
        self.target_y = None

        # --- Main Window Setup ---
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        if platform.system() == "Windows":
            transparent_color = '#abcdef'
            self.root.config(bg=transparent_color)
            self.root.wm_attributes("-transparentcolor", transparent_color)
            canvas_bg = transparent_color
        else:
            self.root.wm_attributes("-transparent", True)
            self.root.config(bg='systemTransparent')
            canvas_bg = 'systemTransparent'

        self.canvas = tk.Canvas(root, width=150, height=150, bg=canvas_bg, highlightthickness=0)
        self.canvas.pack()
        self.redraw_tux()

        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<Button-3>", self.show_custom_menu)

        # Data for options
        self.stories = ["One day, I waddled to the kernel... but it was compiling. So I took a nap.", "I dreamed I was a tiny text file, full of 'GNU/Linux'. It was a good dream.", "I once tried to 'sudo make me a sandwich'. The computer said 'Permission denied'. Rude."]
        self.bad_jokes = ["Why did the penguin cross the road?\n...To prove he wasn't a chicken.", "What do you call a penguin in the desert?\nLost.", "Why don't penguins fly?\nBecause they're not tall enough to be pilots."]
        self.songs = ["[Verse 1]\nOh, my kernel's compiling,\nMy packages are styling,\nWith a 'sudo apt get',\nThere's no bug I haven't met!", "[Verse 1]\nI waddle to the left,\nI 'grep' to the right,\nI stay in my terminal,\nall through the night!"]

        self.root.geometry("+300+300")

        if not os.path.exists(FIRST_RUN_FLAG_FILE):
            self.show_welcome_screen()

        self.idle_loop()

    def show_welcome_screen(self):
        # ... (Unchanged)
        welcome_win = Toplevel(self.root)
        welcome_win.title("Welcome!")
        welcome_win.geometry("400x250")
        welcome_win.transient(self.root)
        welcome_win.wm_attributes("-topmost", True)
        Label(welcome_win, text="Welcome to Talking Linux Penguin Tux!", font=("Arial", 14, "bold")).pack(pady=15)
        features_text = "You can interact with me by right-clicking on me.\n\nFeatures include:\n• AI Mode: Chat with me using Gemini AI.\n• Play Games: Challenge me to new games.\n• Fun Facts: Learn Linux commands, distro facts, and more!\n• Drag me anywhere on your screen."
        Label(welcome_win, text=features_text, justify="left", wraplength=380).pack(pady=5)
        def close_welcome():
            with open(FIRST_RUN_FLAG_FILE, 'w') as f: f.write("completed")
            welcome_win.destroy()
        Button(welcome_win, text="Ok", command=close_welcome, width=10).pack(pady=20)
        self.root.wait_window(welcome_win)

    def show_custom_menu(self, event):
        self.hide_custom_menu()
        self.custom_menu = Toplevel(self.root)
        self.custom_menu.overrideredirect(True)
        self.custom_menu.wm_attributes("-topmost", True)
        self.custom_menu.config(bg=ACCENT_COLOR)

        menu_frame = Frame(self.custom_menu, bg=BG_COLOR, highlightbackground=ACCENT_COLOR, highlightthickness=1)
        menu_frame.pack(padx=1, pady=1)

        wander_text = "Toggle Wander Mode (On)" if self.wander_enabled else "Toggle Wander Mode (Off)"
        body_text = "Set Body: Skinny" if self.body_type == "normal" else "Set Body: Normal"

        options = [
            (f"Change My Name ({self.name})", self.change_name),
            ("--- Appearance ---", None),
            (body_text, self.toggle_body_type),
            ("Force Mood: Normal", lambda: self.set_force_mood("normal")),
            ("Force Mood: Happy", lambda: self.set_force_mood("happy")),
            ("Force Mood: Sad", lambda: self.set_force_mood("sad")),
            ("Force Mood: Angry", lambda: self.set_force_mood("angry")),
            ("Force Mood: Auto", lambda: self.set_force_mood(None)),
            ("--- AI ---", None),
            ("AI Personality Settings...", self.show_ai_settings_menu), # NEW
            ("AI Mode (Chat)", self.toggle_ai_mode),
            ("--- Actions ---", None),
            ("Tell a story", self.tell_story),
            ("Sing a Song", self.sing_song),
            ("Tell a Bad Joke", self.tell_bad_joke),
            ("Clean My Desktop (Just Kidding!)", self.clean_desktop),
            ("--- Games ---", None),
            ("Play Guess the Number", self.start_guess_game),
            ("Play Rock, Paper, Scissors", self.start_rps_game),
            ("--- System ---", None),
            (wander_text, self.toggle_wander),
            ("Check for Updates...", self.check_for_updates),
            ("Open Website", self.open_website),
            ("Exit", self.root.destroy)
        ]

        for text, command in options:
            if "---" in text:
                Label(menu_frame, text=text, bg=BG_COLOR, fg=ACCENT_COLOR, anchor="w", padx=15, pady=2, font=("Arial", 8, "bold")).pack(fill="x")
            else:
                btn = Button(menu_frame, text=text, bg=BG_COLOR, fg=FG_COLOR, relief="flat", activebackground=BUTTON_HOVER_COLOR, activeforeground=FG_COLOR, anchor="w", padx=15, pady=5, justify="left", command=self.create_menu_command(command))
                btn.pack(fill="x")
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BUTTON_HOVER_COLOR))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG_COLOR))

        self.custom_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.custom_menu.focus_set()
        self.custom_menu.grab_set()

    def hide_custom_menu(self, event=None):
        if self.custom_menu:
            self.custom_menu.grab_release()
            self.custom_menu.destroy()
            self.custom_menu = None
            
    # --- NEW: AI Settings Submenu ---
    def show_ai_settings_menu(self):
        self.ai_settings_menu = Toplevel(self.root)
        self.ai_settings_menu.overrideredirect(True)
        self.ai_settings_menu.wm_attributes("-topmost", True)
        self.ai_settings_menu.config(bg=ACCENT_COLOR)
        
        menu_frame = Frame(self.ai_settings_menu, bg=BG_COLOR, highlightbackground=ACCENT_COLOR, highlightthickness=1)
        menu_frame.pack(padx=1, pady=1)

        options = [
            ("Set Custom Personality...", self.set_ai_personality),
            ("Reset AI to Default", self.reset_ai_personality)
        ]

        for text, command in options:
            # Create a command that closes this new menu, then runs the action
            def create_submenu_command(cmd=command):
                return lambda: [self.hide_ai_settings_menu(), cmd() if cmd else None]
                
            btn = Button(menu_frame, text=text, bg=BG_COLOR, fg=FG_COLOR, relief="flat", activebackground=BUTTON_HOVER_COLOR, activeforeground=FG_COLOR, anchor="w", padx=15, pady=5, justify="left", command=create_submenu_command())
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BUTTON_HOVER_COLOR))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG_COLOR))

        # Position it relative to the main menu (if possible) or root
        x, y = self.root.winfo_x() + 100, self.root.winfo_y() + 100
        self.ai_settings_menu.geometry(f"+{x}+{y}")
        self.ai_settings_menu.focus_set()
        self.ai_settings_menu.grab_set() # Make this submenu modal

    def hide_ai_settings_menu(self, event=None):
        if self.ai_settings_menu:
            self.ai_settings_menu.grab_release()
            self.ai_settings_menu.destroy()
            self.ai_settings_menu = None

    def create_menu_command(self, command):
        return lambda: [self.hide_custom_menu(), command() if command else None]

    # --- Mood, Drawing & Animation ---
    def set_force_mood(self, mood):
        self.force_mood = mood
        if not self.is_moving:
            self.redraw_tux()
            
    def set_mood(self, mood, duration_ms=None):
        if self.force_mood: return
        self.mood = mood
        if not self.is_moving: self.redraw_tux()
        if duration_ms: self.root.after(duration_ms, lambda: self.set_mood("normal"))

    def toggle_body_type(self):
        self.body_type = "skinny" if self.body_type == "normal" else "normal"
        self.redraw_tux()

    def redraw_tux(self):
        # ... (Unchanged)
        self.canvas.delete("tux")
        walk_offset_y = 0
        flipper_angle_left, flipper_angle_right, flipper_extent = 180, 270, 90
        if self.body_type == "normal": body_coords, belly_coords, head_coords = [20, 40, 130, 140], [45, 65, 105, 120], [40, 20, 110, 80]
        else: body_coords, belly_coords, head_coords = [35, 40, 115, 140], [55, 65, 95, 120], [45, 20, 105, 80]
        if self.is_moving:
            frame = self.walk_frame % 4
            if frame == 0: walk_offset_y, flipper_angle_left, flipper_angle_right = -3, 160, 290
            elif frame == 1: walk_offset_y = 0
            elif frame == 2: walk_offset_y, flipper_angle_left, flipper_angle_right = -3, 200, 250
            elif frame == 3: walk_offset_y = 0
        y = walk_offset_y
        self.canvas.create_oval(body_coords[0], body_coords[1]+y, body_coords[2], body_coords[3]+y, fill="black", outline="black", tags="tux")
        self.canvas.create_oval(belly_coords[0], belly_coords[1]+y, belly_coords[2], belly_coords[3]+y, fill="white", outline="white", tags="tux")
        self.canvas.create_oval(head_coords[0], head_coords[1]+y, head_coords[2], head_coords[3]+y, fill="black", outline="black", tags="tux")
        self.canvas.create_polygon(75, 55+y, 65, 65+y, 85, 65+y, fill="orange", outline="orange", tags="tux")
        self.canvas.create_arc(30, 125+y, 70, 145+y, start=270, extent=180, fill="orange", outline="orange", style=tk.PIESLICE, tags="tux")
        self.canvas.create_arc(80, 125+y, 120, 145+y, start=270, extent=180, fill="orange", outline="orange", style=tk.PIESLICE, tags="tux")
        self.canvas.create_arc(10, 60+y, 60, 110+y, start=flipper_angle_left, extent=flipper_extent, fill="black", outline="black", style=tk.PIESLICE, tags="tux")
        self.canvas.create_arc(90, 60+y, 140, 110+y, start=flipper_angle_right, extent=flipper_extent, fill="black", outline="black", style=tk.PIESLICE, tags="tux")
        mood_to_draw = self.force_mood if self.force_mood else self.mood
        if self.is_moving: mood_to_draw = "normal"
        if mood_to_draw == "happy": self.canvas.create_arc(60, 35+y, 75, 50+y, start=180, extent=180, style=tk.ARC, outline="black", width=2, tags="tux"); self.canvas.create_arc(80, 35+y, 95, 50+y, start=180, extent=180, style=tk.ARC, outline="black", width=2, tags="tux")
        elif mood_to_draw == "sad": self.canvas.create_arc(60, 40+y, 75, 55+y, start=0, extent=180, style=tk.ARC, outline="black", width=2, tags="tux"); self.canvas.create_arc(80, 40+y, 95, 55+y, start=0, extent=180, style=tk.ARC, outline="black", width=2, tags="tux")
        elif mood_to_draw == "angry": self.canvas.create_line(60, 38+y, 75, 48+y, fill="black", width=3, tags="tux"); self.canvas.create_line(80, 48+y, 95, 38+y, fill="black", width=3, tags="tux")
        else: self.canvas.create_oval(60, 35+y, 75, 50+y, fill="white", outline="black", width=1, tags="tux"); self.canvas.create_oval(80, 35+y, 95, 50+y, fill="white", outline="black", width=1, tags="tux"); self.canvas.create_oval(65, 40+y, 70, 45+y, fill="black", outline="black", tags="tux"); self.canvas.create_oval(85, 40+y, 90, 45+y, fill="black", outline="black", tags="tux")

    # --- Core Functions ---
    def create_speech_bubble(self, text, duration_ms=4000):
        # ... (Unchanged)
        if self.current_bubble: self.current_bubble.destroy()
        bubble = Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.wm_attributes("-topmost", True)
        bubble.config(bg='black')
        bubble.wm_attributes('-transparentcolor', 'black')
        self.current_bubble = bubble
        bubble_label = Label(bubble, text=text, bg="#FFFFE0", fg="black", padx=10, pady=10, wraplength=200, justify="left", relief="solid", borderwidth=1)
        bubble_label.pack()
        tux_x, tux_y = self.root.winfo_x(), self.root.winfo_y()
        bubble.geometry(f"+{tux_x + 100}+{tux_y - 30}")
        def destroy_bubble(event=None):
            if bubble: bubble.destroy(); self.current_bubble = None
        bubble.after(duration_ms, destroy_bubble)
        bubble.bind("<Button-1>", destroy_bubble)
        bubble_label.bind("<Button-1>", destroy_bubble)

    def start_move(self, event):
        self.hide_custom_menu(); self.is_moving = False
        self._x = event.x; self._y = event.y
    def stop_move(self, event):
        self._x = None; self._y = None; self.idle_loop()
    def on_motion(self, event):
        deltax, deltay = event.x - self._x, event.y - self._y
        x, y = self.root.winfo_x() + deltax, self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        if self.ai_controls_window: self.ai_controls_window.geometry(f"+{x - 75}+{y + 160}")

    def change_name(self):
        new_name = simpledialog.askstring("Change Name", "What would you like to call me?")
        if new_name and new_name.strip():
            self.name = new_name.strip()
            self.create_speech_bubble(f"Great! From now on,\nI'm {self.name}!", 3000)
            self.reset_ai_personality() # Name change forces personality reset
    
    def toggle_wander(self, force_state=None):
        """NEW: Can now be forced by AI."""
        if force_state is not None:
            self.wander_enabled = force_state
        else:
            self.wander_enabled = not self.wander_enabled
            
        status = "On" if self.wander_enabled else "Off"
        if force_state is None: # Only show bubble if user clicked
            self.create_speech_bubble(f"Wander Mode is now {status}!", 2000)
            
        if self.wander_enabled: self.idle_loop()
        else: self.is_moving = False
        
    def sing_song(self): self.create_speech_bubble(random.choice(self.songs), 6000)
    def what_am_i(self): self.create_speech_bubble("I'm a desktop pet written in Python using the Tkinter library! I can talk, play games, and wander around your screen.", 6000)
    def clean_desktop(self):
        self.create_speech_bubble("*swish swish*", 1500)
        broom = self.canvas.create_text(75, 130, text="🧹", font=("Arial", 24), tags="temp")
        self.root.after(1500, lambda: self.canvas.delete(broom))
    def check_for_updates(self): self.create_speech_bubble("Checking for updates...\n...\nYou have the latest version of Tux!", 3000)
    def tell_story(self): self.create_speech_bubble(random.choice(self.stories), 5000)
    def tell_bad_joke(self): self.create_speech_bubble(random.choice(self.bad_jokes), 4000); self.set_mood("sad", 4000)
    def open_website(self): webbrowser.open_new_tab(WEBSITE_URL)

    # --- GAMES ---
    def start_guess_game(self):
        # ... (Unchanged)
        game_window = Toplevel(self.root)
        game_window.title("Guess the Number")
        game_window.geometry("300x250")
        game_window.transient(self.root)
        game_window.wm_attributes("-topmost", True)
        game_window.config(bg="#F0F0F0")
        secret_number = random.randint(1, 100)
        guesses_left = 7
        Label(game_window, text="I'm thinking of a number\nbetween 1 and 100.", font=("Arial", 14), bg="#F0F0F0").pack(pady=10)
        feedback_label = Label(game_window, text=f"You have {guesses_left} guesses.", font=("Arial", 12), bg="#F0F0F0")
        feedback_label.pack(pady=5)
        guess_entry = Entry(game_window, font=("Arial", 12), width=10)
        guess_entry.pack(pady=5)
        guess_entry.focus_set()
        def check_guess():
            nonlocal guesses_left
            try:
                guess = int(guess_entry.get())
                guesses_left -= 1
                if guess == secret_number:
                    feedback_label.config(text=f"You got it! It was {secret_number}!", fg=SUCCESS_COLOR)
                    self.set_mood("happy", 4000); guess_entry.config(state="disabled")
                elif guesses_left == 0:
                    feedback_label.config(text=f"Out of guesses! The number was {secret_number}.", fg=ERROR_COLOR)
                    self.set_mood("normal"); guess_entry.config(state="disabled")
                elif guess < secret_number: feedback_label.config(text=f"Too low! You have {guesses_left} guesses left.")
                else: feedback_label.config(text=f"Too high! You have {guesses_left} guesses left.")
            except ValueError: feedback_label.config(text="That's not a valid number!", fg=ERROR_COLOR)
            guess_entry.delete(0, 'end')
        Button(game_window, text="Guess", command=check_guess).pack(pady=10)
        game_window.bind('<Return>', lambda event: check_guess())

    def start_rps_game(self):
        # ... (Unchanged)
        game_window = Toplevel(self.root)
        game_window.title("Play with Tux!")
        game_window.geometry("300x200")
        game_window.transient(self.root)
        game_window.wm_attributes("-topmost", True)
        Label(game_window, text="Choose your weapon!", font=("Arial", 14)).pack(pady=10)
        button_frame = Frame(game_window)
        button_frame.pack(pady=10)
        result_label = Label(game_window, text="Let's play!", font=("Arial", 12), wraplength=280)
        result_label.pack(pady=10, fill="x", expand=True)
        def play_round(player_choice):
            choices = ["Rock", "Paper", "Scissors"]
            computer_choice = random.choice(choices)
            if player_choice == computer_choice: result_text = f"We both chose {player_choice}. It's a tie!"; self.set_mood("normal")
            elif (player_choice == "Rock" and computer_choice == "Scissors") or (player_choice == "Scissors" and computer_choice == "Paper") or (player_choice == "Paper" and computer_choice == "Rock"): result_text = f"You chose {player_choice}, I chose {computer_choice}. You win!"; self.set_mood("angry", 4000)
            else: result_text = f"You chose {player_choice}, I chose {computer_choice}. I win!"; self.set_mood("happy", 4000)
            result_label.config(text=result_text)
        Button(button_frame, text="Rock", width=10, command=lambda: play_round("Rock")).pack(side="left", padx=5)
        Button(button_frame, text="Paper", width=10, command=lambda: play_round("Paper")).pack(side="left", padx=5)
        Button(button_frame, text="Scissors", width=10, command=lambda: play_round("Scissors")).pack(side="left", padx=5)

    # --- AI Mode Functions ---
    def load_api_key(self):
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, 'r') as f: return f.read().strip()
        return None
    def save_api_key(self, key):
        with open(API_KEY_FILE, 'w') as f: f.write(key)
    
    def get_default_system_instruction(self):
        return (f"You are {self.name}, the Linux penguin. You are friendly, helpful, and love open-source software. Keep your answers concise and playful.")
    
    def get_system_instruction(self):
        """Builds the full system instruction with action rules."""
        base_personality = self.ai_personality
        action_rules = (
            "---"
            "ACTION RULES: You can control your own state by including special tags in your response. The user will not see these tags."
            "To change your mood, end your response with: [ACTION:SET_MOOD:HAPPY], [ACTION:SET_MOOD:SAD], [ACTION:SET_MOOD:ANGRY], or [ACTION:SET_MOOD:NORMAL]."
            "To start or stop wandering, end your response with: [ACTION:SET_WANDER:TRUE] or [ACTION:SET_WANDER:FALSE]."
            "Example: If the user says 'be happy', you should say 'Ok, I'm happy now!' and add the tag [ACTION:SET_MOOD:HAPPY]"
            "Example: If the user says 'stop walking', you should say 'Ok, I'll stop.' and add the tag [ACTION:SET_WANDER:FALSE]"
        )
        return base_personality + "\n\n" + action_rules

    def set_ai_personality(self):
        prompt_text = ("Enter a short personality for Tux:\n"
                       "(e.g., 'You are a grumpy penguin')\n\n"
                       "The AI will also be given rules to control its mood and walking.")
        new_personality = simpledialog.askstring("Set AI Personality", prompt_text, parent=self.root)
        if new_personality and new_personality.strip():
            self.ai_personality = new_personality.strip()
            self.gemini_model = None; self.chat_session = None
            self.create_speech_bubble("My personality is updated! (AI Mode will restart)", 3000)

    def reset_ai_personality(self):
        self.ai_personality = self.get_default_system_instruction()
        self.gemini_model = None; self.chat_session = None
        self.create_speech_bubble("My personality is back to normal! (AI Mode will restart)", 3000)

    def toggle_ai_mode(self):
        self.is_moving = False
        if self.ai_controls_window and self.ai_controls_window.winfo_exists(): self.ai_controls_window.lift(); return
        if not self.api_key:
            key = simpledialog.askstring("Gemini API Key", "Please enter your Google AI Studio API Key:", show='*')
            if key: self.api_key = key; self.save_api_key(key)
            else: messagebox.showwarning("AI Mode", "An API key is required."); return
        if not self.gemini_model:
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction=self.get_system_instruction())
                self.chat_session = self.gemini_model.start_chat()
                self.create_speech_bubble(f"Connected to {GEMINI_MODEL_NAME}!", 3000)
            except Exception as e:
                messagebox.showerror("API Error", f"Could not configure AI model.\nCheck API key, internet, or model name.\n\nError: {e}")
                self.api_key = None; self.gemini_model = None; self.chat_session = None
                if os.path.exists(API_KEY_FILE): os.remove(API_KEY_FILE)
                return
        self.open_ai_controls()

    def open_ai_controls(self):
        # ... (Unchanged)
        self.ai_controls_window = Toplevel(self.root)
        self.ai_controls_window.overrideredirect(True)
        self.ai_controls_window.wm_attributes("-topmost", True)
        self.ai_controls_window.config(bg=ACCENT_COLOR)
        bar_frame = Frame(self.ai_controls_window, bg=BG_COLOR)
        bar_frame.pack(padx=1, pady=1)
        self.chat_input = Entry(bar_frame, font=("Arial", 10), bg=ACCENT_COLOR, fg='grey', insertbackground=FG_COLOR, relief="flat", width=30)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.chat_input.insert(0, "Chat with Tux...")
        self.chat_input.bind("<FocusIn>", self.on_entry_focus_in)
        self.chat_input.bind("<FocusOut>", self.on_entry_focus_out)
        send_btn = Button(bar_frame, text="➤", command=self.send_ai_message, bg=BG_COLOR, fg=FG_COLOR, relief="flat", activebackground=BUTTON_HOVER_COLOR, activeforeground=FG_COLOR)
        send_btn.pack(side="left", padx=5, pady=5)
        exit_btn = Button(bar_frame, text="✖", command=self.exit_ai_mode, bg=BG_COLOR, fg=ERROR_COLOR, relief="flat", activebackground=BUTTON_HOVER_COLOR, activeforeground=FG_COLOR)
        exit_btn.pack(side="left", padx=(0, 5), pady=5)
        tux_x, tux_y = self.root.winfo_x(), self.root.winfo_y()
        self.ai_controls_window.geometry(f"+{tux_x - 75}+{tux_y + 160}")
        self.chat_input.bind("<Return>", self.send_ai_message)
        self.set_force_mood("happy")

    def on_entry_focus_in(self, event):
        if self.chat_input.get() == "Chat with Tux...": self.chat_input.delete(0, 'end'); self.chat_input.config(fg=FG_COLOR)
    def on_entry_focus_out(self, event):
        if not self.chat_input.get(): self.chat_input.config(fg='grey'); self.chat_input.insert(0, "Chat with Tux...")

    def exit_ai_mode(self):
        if self.ai_controls_window: self.ai_controls_window.destroy(); self.ai_controls_window = None
        self.set_force_mood(None); self.idle_loop()

    # --- UPDATED: AI Message Sending & Parsing ---
    def send_ai_message(self, event=None):
        if not (self.ai_controls_window and self.ai_controls_window.winfo_exists()): return
        prompt = self.chat_input.get()
        if not prompt.strip() or prompt == "Chat with Tux...": return
        self.chat_input.delete(0, 'end')
        self.set_force_mood("happy")
        self.root.update_idletasks()
        try:
            response = self.chat_session.send_message(prompt)
            # NEW: Parse the text for actions *before* displaying
            clean_text = self.parse_ai_actions(response.text)
            self.create_speech_bubble(clean_text, 8000)
            
            # Don't override if the AI set a specific mood
            if not self.force_mood:
                self.set_mood("happy", 2000)
                
        except Exception as e:
            self.create_speech_bubble(f"Sorry, I had a problem:\n{e}", 5000)
            self.set_mood("sad", 4000)
            
    def parse_ai_actions(self, text):
        """NEW: Parses AI text for action tags and executes them."""
        action_pattern = re.compile(r"\[ACTION:([\w_]+):([\w_]+)\]")
        clean_text = text
        
        for match in action_pattern.finditer(text):
            action = match.group(1).upper()
            value = match.group(2).upper()
            
            if action == "SET_MOOD":
                mood_val = value.lower()
                if mood_val == "normal" or mood_val == "auto":
                    self.set_force_mood(None)
                elif mood_val in ["happy", "sad", "angry"]:
                    self.set_force_mood(mood_val)
                    
            elif action == "SET_WANDER":
                if value == "TRUE":
                    self.toggle_wander(force_state=True)
                elif value == "FALSE":
                    self.toggle_wander(force_state=False)
            
            # Remove the tag from the text that will be displayed
            clean_text = clean_text.replace(match.group(0), "")
            
        return clean_text.strip()

    # --- NPC MOVEMENT LOOP ---
    def idle_loop(self):
        if not self.is_moving and self.wander_enabled:
            delay = random.randint(5000, 15000)
            self.root.after(delay, self.start_wandering)

    def start_wandering(self):
        if not self.wander_enabled or self.is_moving: return
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.target_x = random.randint(0, screen_width - 150)
        self.target_y = random.randint(0, screen_height - 150)
        self.is_moving = True
        self.move_loop()

    def move_loop(self):
        if not self.is_moving or not self.wander_enabled:
            self.is_moving = False; self.redraw_tux(); self.idle_loop(); return
        x, y = self.root.winfo_x(), self.root.winfo_y()
        dx, dy = self.target_x - x, self.target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        if distance < 5:
            self.is_moving = False; self.root.geometry(f"+{self.target_x}+{self.target_y}"); self.redraw_tux(); self.idle_loop(); return
        step = 3
        angle = math.atan2(dy, dx)
        move_x = int(x + step * math.cos(angle))
        move_y = int(y + step * math.sin(angle))
        self.root.geometry(f"+{move_x}+{move_y}")
        self.walk_frame += 1; self.redraw_tux()
        self.root.after(50, self.move_loop)

if __name__ == "__main__":
    main_root = tk.Tk()
    app = PenguinPet(main_root)
    main_root.mainloop()