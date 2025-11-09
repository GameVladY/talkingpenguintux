import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, Entry, Button, Menu, Label, Frame, Canvas, Scrollbar
import random
import google.generativeai as genai
import os
import datetime
import platform
import sys
import webbrowser
import math
import re
# --- IMPORTS FOR UPDATE CHECKER ---
import urllib.request
import json

# --- Configuration ---
CURRENT_VERSION = "v1.6" # <-- SET TO v1.6 as requested
GEMINI_MODEL_NAME = "gemini-2.5-flash"
WEBSITE_URL = "https://sites.google.com/view/verycooltalkinglinuxpenguintux/"
GITHUB_RELEASES_URL = "https://github.com/GameVladY/talkingpenguintux/releases/latest"
GITHUB_API_URL = "https://api.github.com/repos/GameVladY/talkingpenguintux/releases/latest"

# --- Design ---
BG_COLOR = "#2E2E2E"
FG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#4A4A4A"
BUTTON_HOVER_COLOR = "#5A5A5A"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"

# --- PERMISSION ERROR FIX & CONFIG FILES ---
HOME_DIR = os.path.expanduser('~')
API_KEY_FILE = os.path.join(HOME_DIR, "gemini_api_key.txt")
NAME_FILE = os.path.join(HOME_DIR, ".tux_pet_name.txt")

# --- HELPER: DRAWING TUX ---
def draw_tux_on_canvas(canvas, x, y, skin="normal", tags="tux", mood="normal", is_moving=False, walk_frame=0):
    """Reusable function to draw Tux on any canvas."""
    walk_offset_y = 0
    flipper_angle_left, flipper_angle_right, flipper_extent = 180, 270, 90
    
    if is_moving:
        frame = walk_frame % 4
        if frame == 0: walk_offset_y, flipper_angle_left, flipper_angle_right = -3, 160, 290
        elif frame == 1: walk_offset_y = 0
        elif frame == 2: walk_offset_y, flipper_angle_left, flipper_angle_right = -3, 200, 250
        elif frame == 3: walk_offset_y = 0
    
    oy = y + walk_offset_y # Offset Y
    
    if skin == "normal": body, belly, head = [20,40,130,140], [45,65,105,120], [40,20,110,80]
    elif skin == "skinny": body, belly, head = [35,40,115,140], [55,65,95,120], [45,20,105,80]
    elif skin == "baby": body, belly, head = [40,70,110,140], [55,85,95,125], [50,40,100,90]
    elif skin == "cool": body, belly, head = [20,40,130,140], [45,65,105,120], [40,20,110,80]

    def adj(coords, ox, oy): return [coords[0]+ox, coords[1]+oy, coords[2]+ox, coords[3]+oy]

    canvas.create_oval(adj(body, x, oy), fill="black", outline="black", tags=tags)
    canvas.create_oval(adj(belly, x, oy), fill="white", outline="white", tags=tags)
    canvas.create_oval(adj(head, x, oy), fill="black", outline="black", tags=tags)
    
    beak_y = oy + (55 if skin != "baby" else 75)
    canvas.create_polygon(x+75, beak_y, x+65, beak_y+10, x+85, beak_y+10, fill="orange", outline="orange", tags=tags)
    canvas.create_arc(x+30, oy+125, x+70, oy+145, start=270, extent=180, fill="orange", outline="orange", style=tk.PIESLICE, tags=tags)
    canvas.create_arc(x+80, oy+125, x+120, oy+145, start=270, extent=180, fill="orange", outline="orange", style=tk.PIESLICE, tags=tags)
    canvas.create_arc(x+10, oy+60, x+60, oy+110, start=flipper_angle_left, extent=flipper_extent, fill="black", outline="black", style=tk.PIESLICE, tags=tags)
    canvas.create_arc(x+90, oy+60, x+140, oy+110, start=flipper_angle_right, extent=flipper_extent, fill="black", outline="black", style=tk.PIESLICE, tags=tags)

    eye_y = oy + (35 if skin != "baby" else 55)
    mood_draw = "normal" if is_moving else mood

    if mood_draw == "happy":
        canvas.create_arc(x+60, eye_y, x+75, eye_y+15, start=180, extent=180, style=tk.ARC, outline="black", width=2, tags=tags)
        canvas.create_arc(x+80, eye_y, x+95, eye_y+15, start=180, extent=180, style=tk.ARC, outline="black", width=2, tags=tags)
    elif mood_draw == "sad": # This also doubles as "sleeping"
        canvas.create_arc(x+60, eye_y+5, x+75, eye_y+20, start=0, extent=180, style=tk.ARC, outline="black", width=2, tags=tags)
        canvas.create_arc(x+80, eye_y+5, x+95, eye_y+20, start=0, extent=180, style=tk.ARC, outline="black", width=2, tags=tags)
    elif mood_draw == "angry":
        canvas.create_line(x+60, eye_y+3, x+75, eye_y+13, fill="black", width=3, tags=tags)
        canvas.create_line(x+80, eye_y+13, x+95, eye_y+3, fill="black", width=3, tags=tags)
    else: # normal
        canvas.create_oval(x+60, eye_y, x+75, eye_y+15, fill="white", outline="black", width=1, tags=tags)
        canvas.create_oval(x+80, eye_y, x+95, eye_y+15, fill="white", outline="black", width=1, tags=tags)
        canvas.create_oval(x+65, eye_y+5, x+70, eye_y+10, fill="black", outline="black", tags=tags)
        canvas.create_oval(x+85, eye_y+5, x+90, eye_y+10, fill="black", outline="black", tags=tags)

    if skin == "cool" and not is_moving:
        canvas.create_oval(x+55, eye_y, x+75, eye_y+15, fill="black", outline="#333", width=2, tags=tags)
        canvas.create_oval(x+80, eye_y, x+100, eye_y+15, fill="black", outline="#333", width=2, tags=tags)
        canvas.create_line(x+75, eye_y+7, x+80, eye_y+7, fill="#333", width=2, tags=tags)

# --- PENGUIN CLONE CLASS ---
class PenguinClone:
    def __init__(self, main_pet_instance, initial_skin):
        self.main_pet = main_pet_instance
        self.root = Toplevel(self.main_pet.root)
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        if platform.system() == "Windows":
            self.root.config(bg='#abcdef')
            self.root.wm_attributes("-transparentcolor", '#abcdef')
            canvas_bg = '#abcdef'
        else:
            self.root.wm_attributes("-transparent", True)
            self.root.config(bg='systemTransparent')
            canvas_bg = 'systemTransparent'
        self.canvas = tk.Canvas(self.root, width=150, height=150, bg=canvas_bg, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.skin = initial_skin
        self.mood = "normal"
        self.is_moving = False
        self.walk_frame = 0
        self.target_x, self.target_y = None, None
        self.current_bubble = None
        self.main_pet_name = self.main_pet.name
        self.chat_phrases = ["Hi!", "Linux!", "Compiling...", "Zzz...", "Got any fish?", f"Where is {self.main_pet_name}?"]
        start_x = self.main_pet.root.winfo_x() + random.randint(-50, 50)
        start_y = self.main_pet.root.winfo_y() + random.randint(-50, 50)
        self.root.geometry(f"+{start_x}+{start_y}")
        self.redraw_tux()
        self.idle_loop()

    def on_right_click(self, event): self.main_pet.toggle_custom_menu(event)
    def set_skin(self, skin_name): self.skin = skin_name; self.redraw_tux()
    def redraw_tux(self):
        self.canvas.delete("tux")
        draw_tux_on_canvas(self.canvas, 0, 0, self.skin, "tux", self.mood, self.is_moving, self.walk_frame)

    def create_speech_bubble(self, text, duration_ms=2000):
        if self.current_bubble: self.current_bubble.destroy()
        bubble = Toplevel(self.root)
        bubble.overrideredirect(True); bubble.wm_attributes("-topmost", True)
        bubble.config(bg='black'); bubble.wm_attributes('-transparentcolor', 'black')
        self.current_bubble = bubble
        bubble_label = Label(bubble, text=text, bg="#FFFFE0", fg="black", padx=10, pady=10, wraplength=200, justify="left", relief="solid", borderwidth=1)
        bubble_label.pack()
        tux_x, tux_y = self.root.winfo_x(), self.root.winfo_y()
        bubble.geometry(f"+{tux_x + 100}+{tux_y - 30}")
        bubble.after(duration_ms, lambda: bubble.destroy() if bubble and bubble.winfo_exists() else None)

    def simulated_chat(self): self.create_speech_bubble(random.choice(self.chat_phrases), 2000)
    def idle_loop(self):
        if not self.is_moving:
            if random.randint(1, 100) > 90: self.simulated_chat()
            self.root.after(random.randint(5000, 15000), self.start_wandering)
    def start_wandering(self):
        if self.is_moving: return
        self.target_x = random.randint(0, self.root.winfo_screenwidth() - 150)
        self.target_y = random.randint(0, self.root.winfo_screenheight() - 150)
        self.is_moving = True
        self.move_loop()
    def move_loop(self):
        if not self.is_moving: self.redraw_tux(); self.idle_loop(); return
        x, y = self.root.winfo_x(), self.root.winfo_y()
        dx, dy = self.target_x - x, self.target_y - y
        if math.sqrt(dx**2 + dy**2) < 5: self.is_moving = False; self.redraw_tux(); self.idle_loop(); return
        angle = math.atan2(dy, dx)
        self.root.geometry(f"+{int(x + 3 * math.cos(angle))}+{int(y + 3 * math.sin(angle))}")
        self.walk_frame += 1; self.redraw_tux(); self.root.after(50, self.move_loop)


# --- MAIN PENGUIN PET CLASS ---
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
        self.ai_settings_menu = None
        self.appearance_menu = None
        self.clone_settings_menu = None
        self.skin = "normal"
        self.force_mood = None
        self.ai_personality = self.get_default_system_instruction()
        self.is_moving = False
        self.wander_enabled = True
        self.walk_frame = 0
        self.target_x, self.target_y = None, None
        self.game_running = False
        self.mouse_x, self.mouse_y = 0, 0
        self.playground_running = False
        self.playground_target_x, self.playground_target_y = 0, 0
        self.clone_list = []
        self.clone_limit = 50
        self.limit_unlocked = False
        self.ai_duo_running = False

        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        if platform.system() == "Windows":
            self.root.config(bg='#abcdef')
            self.root.wm_attributes("-transparentcolor", '#abcdef')
            canvas_bg = '#abcdef'
        else:
            self.root.wm_attributes("-transparent", True)
            self.root.config(bg='systemTransparent')
            canvas_bg = 'systemTransparent'
        self.canvas = tk.Canvas(root, width=150, height=150, bg=canvas_bg, highlightthickness=0)
        self.canvas.pack()
        
        self.load_or_prompt_name()
        self.redraw_tux()

        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<Button-3>", self.toggle_custom_menu)

        self.stories = ["One day, I waddled to the kernel... but it was compiling. So I took a nap.", "I dreamed I was a tiny text file, full of 'GNU/Linux'. It was a good dream.", "I once tried to 'sudo make me a sandwich'. The computer said 'Permission denied'. Rude."]
        self.bad_jokes = ["Why did the penguin cross the road?\n...To prove he wasn't a chicken.", "What do you call a penguin in the desert?\nLost.", "Why don't penguins fly?\nBecause they're not tall enough to be pilots."]
        self.songs = ["[Verse 1]\nOh, my kernel's compiling,\nMy packages are styling,\nWith a 'sudo apt get',\nThere's no bug I haven't met!", "[Verse 1]\nI waddle to the left,\nI 'grep' to the right,\nI stay in my terminal,\nall through the night!"]

        self.root.geometry("+300+300")
        self.idle_loop()

    def load_or_prompt_name(self):
        if os.path.exists(NAME_FILE):
            with open(NAME_FILE, 'r') as f: self.name = f.read().strip()
            if not self.name: self.name = "Tux"; self.save_name()
        else:
            self.name = "Tux"
            self.root.after(500, self.first_run_welcome)
            
    def first_run_welcome(self):
        self.create_speech_bubble("Thank you for installing\ntalking penguin tux!", 3000)
        self.root.after(3500, self.prompt_for_name_and_welcome)

    def prompt_for_name_and_welcome(self):
        new_name = simpledialog.askstring("Welcome!", "Please name your new penguin:", initialvalue="Tux")
        self.name = new_name.strip() if new_name and new_name.strip() else "Tux"
        self.save_name()
        self.show_welcome_screen()
            
    def save_name(self):
        with open(NAME_FILE, 'w') as f: f.write(self.name)
        
    def show_welcome_screen(self):
        welcome_win = Toplevel(self.root); welcome_win.title("Welcome!"); welcome_win.geometry("400x250"); welcome_win.transient(self.root); welcome_win.wm_attributes("-topmost", True)
        Label(welcome_win, text=f"Welcome, {self.name}!", font=("Arial", 14, "bold")).pack(pady=15)
        Label(welcome_win, text="You can interact with me by right-clicking on me.\n\nFeatures include:\n• AI Mode (Chat with me)\n• Play Games\n• Fun Actions & Facts\n• Drag me anywhere!", justify="left", wraplength=380).pack(pady=5)
        Button(welcome_win, text="Ok", command=welcome_win.destroy, width=10).pack(pady=20); self.root.wait_window(welcome_win)
        
    def on_mouse_wheel(self, event, canvas):
        if platform.system() == "Windows": canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == "Darwin": canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4: canvas.yview_scroll(-1, "units")
            elif event.num == 5: canvas.yview_scroll(1, "units")

    def toggle_custom_menu(self, event):
        if self.custom_menu: self.hide_custom_menu()
        else: self.show_custom_menu(event)

    def show_custom_menu(self, event):
        self.hide_custom_menu()
        self.custom_menu = Toplevel(self.root); self.custom_menu.overrideredirect(True); self.custom_menu.wm_attributes("-topmost", True)
        menu_container = Frame(self.custom_menu, bg=BG_COLOR, highlightbackground=ACCENT_COLOR, highlightthickness=1); menu_container.pack()
        menu_canvas = Canvas(menu_container, bg=BG_COLOR, highlightthickness=0, width=220)
        scrollbar = Scrollbar(menu_container, orient="vertical", command=menu_canvas.yview, width=12, bg=BG_COLOR, troughcolor=ACCENT_COLOR, activebackground=BUTTON_HOVER_COLOR)
        menu_content_frame = Frame(menu_canvas, bg=BG_COLOR)
        menu_canvas.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y"); menu_canvas.pack(side="left", fill="both", expand=True)
        menu_canvas.create_window((0, 0), window=menu_content_frame, anchor="nw")
        menu_content_frame.bind("<Configure>", lambda e: menu_canvas.configure(scrollregion=menu_canvas.bbox("all")))
        for w in (menu_canvas, menu_content_frame):
            w.bind_all("<MouseWheel>", lambda e, c=menu_canvas: self.on_mouse_wheel(e, c)); w.bind_all("<Button-4>", lambda e, c=menu_canvas: self.on_mouse_wheel(e, c)); w.bind_all("<Button-5>", lambda e, c=menu_canvas: self.on_mouse_wheel(e, c))

        wander_text = "Toggle Wander Mode (On)" if self.wander_enabled else "Toggle Wander Mode (Off)"
        options = [
            (f"Change My Name ({self.name})", self.change_name),
            ("--- Appearance ---", None),
            ("Appearance Settings...", self.show_appearance_menu),
            ("Force Mood: Normal", lambda: self.set_force_mood("normal")),
            ("Force Mood: Happy", lambda: self.set_force_mood("happy")),
            ("Force Mood: Sad", lambda: self.set_force_mood("sad")),
            ("Force Mood: Angry", lambda: self.set_force_mood("angry")),
            ("Force Mood: Auto", lambda: self.set_force_mood(None)),
            ("--- AI ---", None),
            ("AI Personality Settings...", self.show_ai_settings_menu),
            ("AI Mode (Chat)", self.toggle_ai_mode),
            ("2 Penguins AI Chat (BETA)", self.start_ai_duo_setup),
            ("--- Clones ---", None),
            ("Create Clones...", self.prompt_for_clones),
            ("Destroy All Clones", self.destroy_all_clones),
            ("Clone Settings...", self.show_clone_settings_menu),
            ("--- Actions ---", None),
            ("Eat a Fish", self.eat_fish), # <-- NEW ACTION
            ("Take a Nap", self.take_nap), # <-- NEW ACTION
            ("What's the Time?", self.tell_time), # <-- NEW ACTION
            ("Tell a story", self.tell_story),
            ("Sing a Song", self.sing_song),
            ("Tell a Bad Joke", self.tell_bad_joke),
            ("Clean My Desktop (Just Kidding!)", self.clean_desktop),
            ("--- Games ---", None),
            ("Find the Fish", self.start_fish_game),
            ("Play in Playground", self.start_playground_game),
            ("Play Catch the Mouse", self.start_catch_game),
            ("Play Guess the Number", self.start_guess_game),
            ("Play Rock, Paper, Scissors", self.start_rps_game),
            ("--- System ---", None),
            (wander_text, self.toggle_wander),
            ("Check for Updates...", self.check_for_updates),
            ("Open Website", self.open_website),
            ("Exit", self.on_exit)
        ]
        for text, command in options:
            if "---" in text: Label(menu_content_frame, text=text, bg=BG_COLOR, fg=ACCENT_COLOR, anchor="w", padx=15, pady=2, font=("Arial", 8, "bold")).pack(fill="x")
            else:
                item = Label(menu_content_frame, text=text, bg=BG_COLOR, fg=FG_COLOR, relief="flat", anchor="w", padx=15, pady=5, justify="left", font=("Arial", 10))
                item.pack(fill="x"); item.bind("<Enter>", lambda e, i=item: i.config(bg=BUTTON_HOVER_COLOR)); item.bind("<Leave>", lambda e, i=item: i.config(bg=BG_COLOR)); item.bind("<Button-1>", lambda e, cmd=command: self.create_menu_command(cmd)())

        self.custom_menu.update_idletasks()
        menu_height = min(menu_content_frame.winfo_reqheight(), 400)
        menu_canvas.config(height=menu_height)
        self.custom_menu.geometry(f"+{event.x_root}+{event.y_root}"); self.custom_menu.focus_set(); self.custom_menu.grab_set()

    def hide_custom_menu(self, event=None):
        if self.custom_menu: self.custom_menu.grab_release(); self.custom_menu.destroy(); self.custom_menu = None

    def _show_submenu(self, menu_ref_attr, options, hide_func):
        if getattr(self, menu_ref_attr, None): hide_func()
        menu = Toplevel(self.root); menu.overrideredirect(True); menu.wm_attributes("-topmost", True)
        setattr(self, menu_ref_attr, menu)
        menu_container = Frame(menu, bg=BG_COLOR, highlightbackground=ACCENT_COLOR, highlightthickness=1); menu_container.pack()
        for text, command in options:
            item = Label(menu_container, text=text, bg=BG_COLOR, fg=FG_COLOR, relief="flat", anchor="w", padx=15, pady=5, justify="left", font=("Arial", 10))
            item.pack(fill="x"); item.bind("<Enter>", lambda e, i=item: i.config(bg=BUTTON_HOVER_COLOR)); item.bind("<Leave>", lambda e, i=item: i.config(bg=BG_COLOR)); item.bind("<Button-1>", lambda e, cmd=command: [hide_func(), cmd() if cmd else None]())
        menu.geometry(f"+{self.root.winfo_x()+100}+{self.root.winfo_y()+100}"); menu.focus_set(); menu.grab_set()

    def show_ai_settings_menu(self): self._show_submenu('ai_settings_menu', [("Set Custom Personality...", self.set_ai_personality), ("Reset AI to Default", self.reset_ai_personality)], self.hide_ai_settings_menu)
    def hide_ai_settings_menu(self, event=None):
        if self.ai_settings_menu: self.ai_settings_menu.grab_release(); self.ai_settings_menu.destroy(); self.ai_settings_menu = None
    def show_appearance_menu(self): self._show_submenu('appearance_menu', [("Set Skin: Normal", lambda: self.set_skin("normal")), ("Set Skin: Skinny", lambda: self.set_skin("skinny")), ("Set Skin: Baby", lambda: self.set_skin("baby")), ("Set Skin: Cool", lambda: self.set_skin("cool"))], self.hide_appearance_menu)
    def hide_appearance_menu(self, event=None):
        if self.appearance_menu: self.appearance_menu.grab_release(); self.appearance_menu.destroy(); self.appearance_menu = None
    def show_clone_settings_menu(self): self._show_submenu('clone_settings_menu', [("Unlock Clone Limit (Dangerous!)", self.unlock_clone_limit), ("Lock Clone Limit (Safe)", self.lock_clone_limit)], self.hide_clone_settings_menu)
    def hide_clone_settings_menu(self, event=None):
        if self.clone_settings_menu: self.clone_settings_menu.grab_release(); self.clone_settings_menu.destroy(); self.clone_settings_menu = None

    def create_menu_command(self, command): return lambda: [self.hide_custom_menu(), command() if command else None]
    def unlock_clone_limit(self):
        if messagebox.askokcancel("WARNING", "Unlocking the clone limit is dangerous and can crash your computer.\nProceed?"): self.limit_unlocked = True; self.clone_limit = 99999; messagebox.showinfo("Unlocked", "Clone limit removed.")
    def lock_clone_limit(self): self.limit_unlocked = False; self.clone_limit = 50; messagebox.showinfo("Locked", "Clone limit set to 50.")
    def set_force_mood(self, mood): self.force_mood = mood; self.redraw_tux() if not self.is_moving else None
    def set_mood(self, mood, duration_ms=None):
        if self.force_mood: return
        self.mood = mood; self.redraw_tux() if not self.is_moving else None
        if duration_ms: self.root.after(duration_ms, lambda: self.set_mood("normal"))
    def set_skin(self, skin_name): self.skin = skin_name; self.redraw_tux(); [c.set_skin(skin_name) for c in self.clone_list]
    def redraw_tux(self): self.canvas.delete("tux"); draw_tux_on_canvas(self.canvas, 0, 0, self.skin, "tux", self.force_mood if self.force_mood else self.mood, self.is_moving, self.walk_frame)
    def create_speech_bubble(self, text, duration_ms=4000):
        if self.current_bubble: self.current_bubble.destroy()
        bubble = Toplevel(self.root); bubble.overrideredirect(True); bubble.wm_attributes("-topmost", True); bubble.config(bg='black'); bubble.wm_attributes('-transparentcolor', 'black'); self.current_bubble = bubble
        Label(bubble, text=text, bg="#FFFFE0", fg="black", padx=10, pady=10, wraplength=200, justify="left", relief="solid", borderwidth=1).pack()
        bubble.geometry(f"+{self.root.winfo_x() + 100}+{self.root.winfo_y() - 30}")
        bubble.after(duration_ms, lambda: bubble.destroy() if bubble and bubble.winfo_exists() else None)
    def start_move(self, event): self.hide_custom_menu(); self.is_moving = False; self._x = event.x; self._y = event.y
    def stop_move(self, event): self._x = None; self._y = None; self.idle_loop()
    def on_motion(self, event):
        new_x, new_y = self.root.winfo_x() + event.x - self._x, self.root.winfo_y() + event.y - self._y
        self.root.geometry(f"+{new_x}+{new_y}")
        if self.ai_controls_window: self.ai_controls_window.geometry(f"+{new_x - 75}+{new_y + 160}")
    def change_name(self):
        new = simpledialog.askstring("Name", "New name?", initialvalue=self.name)
        if new and new.strip(): self.name = new.strip(); self.save_name(); self.create_speech_bubble(f"I'm {self.name}!", 3000); self.reset_ai_personality()
    def toggle_wander(self, force_state=None):
        if force_state is not None: self.wander_enabled = force_state
        else: self.wander_enabled = not self.wander_enabled
        if force_state is None: self.create_speech_bubble(f"Wander Mode is now {'On' if self.wander_enabled else 'Off'}!", 2000)
        if self.wander_enabled: self.idle_loop()
        else: self.is_moving = False
    
    # --- NEW ACTIONS ---
    def eat_fish(self):
        self.create_speech_bubble("Yum! Thanks!", 2000)
        self.set_mood("happy", 2000)
        fish = self.canvas.create_text(110, 75, text="🐟", font=("Arial", 24), tags="temp")
        self.root.after(1000, lambda: self.canvas.delete(fish) if self.canvas.winfo_exists() else None)
        
    def take_nap(self):
        self.create_speech_bubble("Zzz... nap time.", 3000)
        self.set_force_mood("sad") # "Sad" eyes look like sleeping
        self.root.after(3000, lambda: self.set_force_mood(None)) # Wake up
        
    def tell_time(self):
        current_time = datetime.datetime.now().strftime("%I:%M %p") # e.g., 05:30 PM
        self.create_speech_bubble(f"The time is\n{current_time}", 3000)

    # --- Other Actions ---
    def sing_song(self): self.create_speech_bubble(random.choice(self.songs), 6000)
    def what_am_i(self): self.create_speech_bubble("I'm a desktop pet written in Python using Tkinter!", 6000)
    def clean_desktop(self):
        self.create_speech_bubble("*swish swish*", 1500); broom = self.canvas.create_text(75, 130, text="🧹", font=("Arial", 24), tags="temp")
        self.root.after(1500, lambda: self.canvas.delete(broom) if self.canvas.winfo_exists() else None)
    def check_for_updates(self):
        self.create_speech_bubble("Checking for updates...", 2000); self.root.update_idletasks()
        try:
            req = urllib.request.Request(GITHUB_API_URL); req.add_header('User-Agent', 'Python TuxPet')
            with urllib.request.urlopen(req, timeout=5) as response:
                latest_version = json.loads(response.read().decode())["tag_name"]
                if latest_version != CURRENT_VERSION:
                     self.create_speech_bubble(f"New update {latest_version} is out!", 4000)
                     if messagebox.askyesno("Update Available", f"Version {latest_version} is available!\n(Current: {CURRENT_VERSION})\n\nGo to download page?"):
                         webbrowser.open(GITHUB_RELEASES_URL)
                else: self.create_speech_bubble("You have the latest version!", 3000)
        except Exception: self.create_speech_bubble("I couldn't check for updates...", 3000)
    def tell_story(self): self.create_speech_bubble(random.choice(self.stories), 5000)
    def tell_bad_joke(self): self.create_speech_bubble(random.choice(self.bad_jokes), 4000); self.set_mood("sad", 4000)
    def open_website(self): webbrowser.open_new_tab(WEBSITE_URL)

    # --- All Games ---
    def start_guess_game(self):
        gw = Toplevel(self.root); gw.title("Guess Number"); gw.geometry("300x250"); gw.transient(self.root); gw.wm_attributes("-topmost", True); gw.config(bg="#F0F0F0")
        secret, guesses = random.randint(1, 100), 7
        Label(gw, text="I'm thinking of a number\nbetween 1 and 100.", font=("Arial", 14), bg="#F0F0F0").pack(pady=10)
        fb = Label(gw, text=f"{guesses} guesses left.", font=("Arial", 12), bg="#F0F0F0"); fb.pack(pady=5)
        ent = Entry(gw, font=("Arial", 12), width=10); ent.pack(pady=5); ent.focus_set()
        def check():
            nonlocal guesses; 
            try:
                g = int(ent.get()); guesses -= 1
                if g == secret: fb.config(text=f"Correct! It was {secret}!", fg=SUCCESS_COLOR); self.set_mood("happy", 4000); ent.config(state="disabled")
                elif guesses == 0: fb.config(text=f"Out of guesses! It was {secret}.", fg=ERROR_COLOR); self.set_mood("normal"); ent.config(state="disabled")
                elif g < secret: fb.config(text=f"Too low! {guesses} left.")
                else: fb.config(text=f"Too high! {guesses} left.")
            except: fb.config(text="Invalid number!", fg=ERROR_COLOR)
            ent.delete(0, 'end')
        Button(gw, text="Guess", command=check).pack(pady=10); gw.bind('<Return>', lambda e: check())
    
    def start_rps_game(self):
        gw = Toplevel(self.root); gw.title("RPS"); gw.geometry("300x200"); gw.transient(self.root); gw.wm_attributes("-topmost", True)
        Label(gw, text="Choose your weapon!", font=("Arial", 14)).pack(pady=10); bf = Frame(gw); bf.pack(pady=10)
        res = Label(gw, text="Let's play!", font=("Arial", 12), wraplength=280); res.pack(pady=10, fill="x", expand=True)
        def play(pc):
            cc = random.choice(["Rock", "Paper", "Scissors"])
            if pc == cc: res.config(text=f"Both chose {pc}. Tie!"); self.set_mood("normal")
            elif (pc == "Rock" and cc == "Scissors") or (pc == "Scissors" and cc == "Paper") or (pc == "Paper" and cc == "Rock"): res.config(text=f"You chose {pc}, I chose {cc}. You win!"); self.set_mood("angry", 4000)
            else: res.config(text=f"You chose {pc}, I chose {cc}. I win!"); self.set_mood("happy", 4000)
        for c in ["Rock", "Paper", "Scissors"]: Button(bf, text=c, width=8, command=lambda x=c: play(x)).pack(side="left", padx=5)
    
    def start_catch_game(self):
        self.game_running = True; gw = Toplevel(self.root); gw.title("Catch!"); gw.geometry("600x500"); gw.transient(self.root); gw.wm_attributes("-topmost", True)
        gc = Canvas(gw, bg="white", highlightthickness=0); gc.pack(fill="both", expand=True); gc.bind("<Motion>", lambda e: [setattr(self, 'mouse_x', e.x), setattr(self, 'mouse_y', e.y)])
        draw_tux_on_canvas(gc, 225, 175, self.skin, "gt", "angry", False)
        msg = gc.create_text(300, 155, text="I will catch you!", font=("Arial", 16, "bold"), fill="red"); gw.after(2000, lambda: gc.delete(msg) if gc.winfo_exists() else None)
        def loop(wf=0):
            if not self.game_running: return
            try:
                bb = gc.bbox("gt"); cx, cy = (bb[0]+bb[2])/2, (bb[1]+bb[3])/2
                if math.sqrt((cx-self.mouse_x)**2 + (cy-self.mouse_y)**2) < 40: self.game_running = False; messagebox.showinfo("Caught!", "I caught you!", parent=gw); self.set_mood("happy", 3000); gw.destroy(); return
                ang = math.atan2(self.mouse_y-cy, self.mouse_x-cx); gc.move("gt", 3.5*math.cos(ang), 3.5*math.sin(ang))
                nbb = gc.bbox("gt"); gc.delete("gt"); draw_tux_on_canvas(gc, nbb[0], nbb[1], self.skin, "gt", "angry", True, wf+1); gw.after(30, lambda: loop(wf+1))
            except: self.game_running = False
        gw.after(2000, loop); gw.protocol("WM_DELETE_WINDOW", lambda: [setattr(self, 'game_running', False), gw.destroy()])
    
    def start_playground_game(self):
        self.playground_running = True; self.set_mood("happy", 5000); gw = Toplevel(self.root); gw.title("Playground"); gw.geometry("600x400"); gw.transient(self.root); gw.wm_attributes("-topmost", True)
        gc = Canvas(gw, bg="#77C74A", highlightthickness=0); gc.pack(fill="both", expand=True)
        gc.create_oval(400, 250, 550, 350, fill="#3498DB", outline="#2980B9", width=3); gc.create_rectangle(50, 150, 100, 300, fill="#B0B0B0", outline="#606060", width=2); gc.create_polygon(100, 150, 100, 170, 250, 300, 250, 280, fill="#D0D0D0", outline="#606060", width=2)
        draw_tux_on_canvas(gc, 225, 125, self.skin, "pt", "happy", True); tx, ty = random.randint(50,550), random.randint(50,350)
        def loop(wf=0):
            nonlocal tx, ty
            if not self.playground_running: return
            try:
                bb = gc.bbox("pt"); cx, cy = (bb[0]+bb[2])/2, (bb[1]+bb[3])/2
                if math.sqrt((cx-tx)**2 + (cy-ty)**2) < 20: tx, ty = random.randint(50,550), random.randint(50,350)
                ang = math.atan2(ty-cy, tx-cx); gc.move("pt", 3*math.cos(ang), 3*math.sin(ang))
                nbb = gc.bbox("pt"); gc.delete("pt"); draw_tux_on_canvas(gc, nbb[0], nbb[1], self.skin, "pt", "happy", True, wf+1); gw.after(40, lambda: loop(wf+1))
            except: self.playground_running = False
        gw.protocol("WM_DELETE_WINDOW", lambda: [setattr(self, 'playground_running', False), gw.destroy()]); loop()
    
    def start_fish_game(self):
        gw = Toplevel(self.root); gw.title("Find Fish"); gw.geometry("400x300"); gw.transient(self.root); gw.wm_attributes("-topmost", True)
        gc = Canvas(gw, bg="#B0E0E6", highlightthickness=0); gc.pack(fill="both", expand=True)
        sl = Label(gw, text="Watch the 🧊 with the 🐟!", font=("Arial", 14), bg="#B0E0E6"); sl.pack(pady=10)
        c1 = gc.create_text(100, 150, text="🧊", font=("Arial", 60)); c2 = gc.create_text(200, 150, text="🧊", font=("Arial", 60)); c3 = gc.create_text(300, 150, text="🧊", font=("Arial", 60)); cups = [c1, c2, c3]
        fp = random.choice([0, 1, 2]); fe = gc.create_text(100 + fp*100, 220, text="🐟", font=("Arial", 30)); gc.itemconfigure(cups[fp], fill="#70C0C0"); gip = True
        def rev(ch):
            nonlocal gip; 
            if not gip: return
            gip = False; [gc.tag_unbind(c, "<Button-1>") for c in cups]
            [gc.create_text(100*(i+1), 220, text="👢", font=("Arial", 30)) for i in range(3)]; gc.delete(fe); gc.create_text(100 + fp*100, 220, text="🐟", font=("Arial", 30))
            [gc.move(c, 0, -50) for c in cups]
            if ch == fp: sl.config(text="You found the 🐟! Win!"); self.set_mood("happy", 3000)
            else: sl.config(text="Oh no, a 👢! Try again!"); self.set_mood("sad", 3000)
            gw.after(3000, gw.destroy)
        for i, c in enumerate(cups): gc.tag_bind(c, "<Button-1>", lambda e, idx=i: rev(idx))
        def shuf(sl_):
            nonlocal fp; 
            if not gip: return
            if sl_ <= 0: sl.config(text="Click the 🧊!"); return
            i1, i2 = random.sample(range(3), 2); gc.move(cups[i1], (i2-i1)*100, 0); gc.move(cups[i2], (i1-i2)*100, 0); cups[i1], cups[i2] = cups[i2], cups[i1]
            if fp == i1: fp = i2
            elif fp == i2: fp = i1
            gw.after(300, lambda: shuf(sl_ - 1))
        gw.after(2000, lambda: [gc.delete(fe) if gc.winfo_exists() else None, gc.itemconfigure(cups[fp], fill="black"), sl.config(text="Shuffling..."), shuf(10)])
        gw.protocol("WM_DELETE_WINDOW", lambda: [setattr(self, 'game_running', False), gw.destroy()])

    # --- AI Chat ---
    def load_api_key(self): return open(API_KEY_FILE).read().strip() if os.path.exists(API_KEY_FILE) else None
    def save_api_key(self, key): 
        try: open(API_KEY_FILE, 'w').write(key) 
        except: messagebox.showerror("Error", "Could not save API key.")
    def get_default_system_instruction(self): return f"You are {self.name}, the Linux penguin. Friendly, helpful, loves open-source. Concise and playful."
    def get_system_instruction(self): return self.ai_personality + "\n\n---ACTION RULES: End response with [ACTION:SET_MOOD:HAPPY/SAD/ANGRY/NORMAL] or [ACTION:SET_WANDER:TRUE/FALSE] to control state."
    def set_ai_personality(self):
        np = simpledialog.askstring("Personality", "Enter short personality:\n(e.g., 'Grumpy penguin')")
        if np and np.strip(): self.ai_personality = np.strip(); self.gemini_model = None; self.create_speech_bubble("Personality updated!", 3000)
    def reset_ai_personality(self): self.ai_personality = self.get_default_system_instruction(); self.gemini_model = None; self.create_speech_bubble("Personality reset!", 3000)
    def toggle_ai_mode(self):
        self.is_moving = False; 
        if self.ai_controls_window and self.ai_controls_window.winfo_exists(): self.ai_controls_window.lift(); return
        if not self.api_key:
            k = simpledialog.askstring("API Key", "Gemini API Key:", show='*')
            if k: self.api_key = k; self.save_api_key(k)
            else: return
        if not self.gemini_model:
            try: genai.configure(api_key=self.api_key); self.gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction=self.get_system_instruction()); self.chat_session = self.gemini_model.start_chat(); self.create_speech_bubble("Connected!", 3000)
            except Exception as e: messagebox.showerror("API Error", str(e)); self.api_key = None; return
        self.open_ai_controls()
    def open_ai_controls(self):
        self.ai_controls_window = Toplevel(self.root); self.ai_controls_window.overrideredirect(True); self.ai_controls_window.wm_attributes("-topmost", True); self.ai_controls_window.config(bg=ACCENT_COLOR)
        bf = Frame(self.ai_controls_window, bg=BG_COLOR); bf.pack(padx=1, pady=1)
        self.chat_input = Entry(bf, font=("Arial", 10), bg=ACCENT_COLOR, fg='grey', insertbackground=FG_COLOR, relief="flat", width=30); self.chat_input.pack(side="left", fill="x", expand=True, padx=10, pady=5); self.chat_input.insert(0, "Chat..."); self.chat_input.bind("<FocusIn>", self.on_entry_focus_in); self.chat_input.bind("<FocusOut>", self.on_entry_focus_out)
        Button(bf, text="➤", command=self.send_ai_message, bg=BG_COLOR, fg=FG_COLOR, relief="flat", activebackground=BUTTON_HOVER_COLOR, activeforeground=FG_COLOR).pack(side="left", padx=5, pady=5)
        Button(bf, text="✖", command=self.exit_ai_mode, bg=BG_COLOR, fg=ERROR_COLOR, relief="flat", activebackground=BUTTON_HOVER_COLOR, activeforeground=FG_COLOR).pack(side="left", padx=(0, 5), pady=5)
        self.ai_controls_window.geometry(f"+{self.root.winfo_x() - 75}+{self.root.winfo_y() + 160}"); self.chat_input.bind("<Return>", self.send_ai_message); self.set_force_mood("happy")
    def on_entry_focus_in(self, event): 
        if self.chat_input.get() == "Chat...": self.chat_input.delete(0, 'end'); self.chat_input.config(fg=FG_COLOR)
    def on_entry_focus_out(self, event):
        if not self.chat_input.get(): self.chat_input.config(fg='grey'); self.chat_input.insert(0, "Chat...")
    def exit_ai_mode(self): self.ai_controls_window.destroy(); self.ai_controls_window = None; self.set_force_mood(None); self.idle_loop()
    def send_ai_message(self, event=None):
        if not (self.ai_controls_window and self.ai_controls_window.winfo_exists()): return
        p = self.chat_input.get(); 
        if not p.strip() or p == "Chat...": return
        self.chat_input.delete(0, 'end'); self.set_force_mood("happy"); self.root.update_idletasks()
        try:
            resp = self.chat_session.send_message(p); txt = resp.text
            for m in re.finditer(r"\[ACTION:([\w_]+):([\w_]+)\]", txt):
                a, v = m.group(1), m.group(2).lower()
                if a == "SET_MOOD": self.set_force_mood(v if v in ["happy", "sad", "angry"] else None)
                elif a == "SET_WANDER": self.toggle_wander(v == "true")
                txt = txt.replace(m.group(0), "")
            self.create_speech_bubble(txt.strip(), 8000); 
            if not self.force_mood: self.set_mood("happy", 2000)
        except Exception as e: self.create_speech_bubble("Error...", 5000); self.set_mood("sad", 4000)

    # --- AI Duo ---
    def start_ai_duo_setup(self):
        if not self.api_key:
             key = simpledialog.askstring("API Key", "Enter Gemini API Key:", show='*')
             if key: self.api_key = key; self.save_api_key(key)
             else: return
        turns = simpledialog.askinteger("AI Duo", "Conversation turns?\n(0 for unlimited)", minvalue=0, maxvalue=100, initialvalue=5)
        if turns is not None: self.start_ai_duo(turns)
    def start_ai_duo(self, max_turns):
        self.ai_duo_running = True; dw = Toplevel(self.root); dw.title("AI Duo Chat"); dw.geometry("600x400"); dw.transient(self.root)
        dc = Canvas(dw, bg="white", highlightthickness=0); dc.pack(fill="both", expand=True)
        draw_tux_on_canvas(dc, 50, 200, self.skin, "t1", "happy"); draw_tux_on_canvas(dc, 400, 200, self.skin, "t2", "happy")
        b1 = Label(dw, text="", bg="#FFFFE0", fg="black", padx=10, pady=10, wraplength=180, justify="left", relief="solid", borderwidth=1)
        b2 = Label(dw, text="", bg="#E0FFFF", fg="black", padx=10, pady=10, wraplength=180, justify="left", relief="solid", borderwidth=1)
        sl = Label(dw, text="Connecting...", bg="white", font=("Arial", 12)); sl.place(relx=0.5, rely=0.1, anchor="center")
        Button(dw, text="STOP", bg=ERROR_COLOR, fg="white", font=("Arial", 12, "bold"), command=lambda: [setattr(self, 'ai_duo_running', False), dw.destroy()]).place(relx=0.5, rely=0.9, anchor="center")
        try:
            genai.configure(api_key=self.api_key)
            ma = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction="You are Tux A, friendly Linux penguin chatting with Tux B. Keep responses short."); mb = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction="You are Tux B, funny Linux penguin chatting with Tux A. Keep responses short.")
            ca, cb = ma.start_chat(), mb.start_chat()
        except Exception as e: messagebox.showerror("AI Error", str(e)); dw.destroy(); return
        def turn(tc, last, sp):
            if not self.ai_duo_running or not dw.winfo_exists(): return
            if max_turns > 0 and tc > max_turns: sl.config(text="Finished."); return
            sl.config(text=f"Turn {tc}..." if max_turns==0 else f"Turn {tc}/{max_turns}...")
            try:
                if sp == "A":
                    resp = ca.send_message(last).text.strip(); b2.place_forget(); b1.config(text=resp); b1.place(x=50, y=50)
                    dw.after(4000, lambda: turn(tc, resp, "B"))
                else:
                    resp = cb.send_message(last).text.strip(); b1.place_forget(); b2.config(text=resp); b2.place(x=350, y=50)
                    dw.after(4000, lambda: turn(tc+1, resp, "A"))
            except Exception as e: 
                if dw.winfo_exists(): sl.config(text=f"Error: {e}"); self.ai_duo_running = False
        dw.protocol("WM_DELETE_WINDOW", lambda: [setattr(self, 'ai_duo_running', False), dw.destroy()]); turn(1, "Hi! Thoughts on Linux?", "A")

    # --- Clones & Idle ---
    def on_exit(self): self.destroy_all_clones(); self.root.destroy()
    def destroy_all_clones(self): [c.root.destroy() for c in self.clone_list]; self.clone_list.clear()
    def prompt_for_clones(self):
        mx = 5000 if self.limit_unlocked else (self.clone_limit - len(self.clone_list))
        if mx <= 0: messagebox.showinfo("Limit", f"Limit is {self.clone_limit}."); return
        n = simpledialog.askinteger("Clones", f"How many? (Max: {mx})", minvalue=1, maxvalue=mx)
        if n: [self.clone_list.append(PenguinClone(self, self.skin)) for _ in range(n)]
    def random_chat(self): self.create_speech_bubble(random.choice([f"Hello, I am {self.name}!", "Let's play!", "I love Linux!", "*waddle*", "Compiling...", "Happy!", "Playground time?"]), 3000)
    def idle_loop(self):
        if not self.is_moving and self.wander_enabled:
            if not (self.ai_controls_window and self.ai_controls_window.winfo_exists()) and random.randint(1, 100) > 85: self.random_chat(); self.root.after(random.randint(5000, 10000), self.idle_loop); return
            self.root.after(random.randint(5000, 15000), self.start_wandering)
    def start_wandering(self):
        if not self.wander_enabled or self.is_moving: return
        self.target_x, self.target_y = random.randint(0, self.root.winfo_screenwidth()-150), random.randint(0, self.root.winfo_screenheight()-150); self.is_moving = True; self.move_loop()
    def move_loop(self):
        if not self.is_moving or not self.wander_enabled: self.is_moving = False; self.redraw_tux(); self.idle_loop(); return
        cx, cy = self.root.winfo_x(), self.root.winfo_y(); dx, dy = self.target_x - cx, self.target_y - cy
        if math.sqrt(dx**2 + dy**2) < 5: self.is_moving = False; self.redraw_tux(); self.idle_loop(); return
        ang = math.atan2(dy, dx); self.root.geometry(f"+{int(cx+3*math.cos(ang))}+{int(cy+3*math.sin(ang))}"); self.walk_frame += 1; self.redraw_tux(); self.root.after(50, self.move_loop)

if __name__ == "__main__":
    main_root = tk.Tk()
    app = PenguinPet(main_root)
    main_root.mainloop()
