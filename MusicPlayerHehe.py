import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pygame
from collections import deque
import os
import threading
import time
import math
from PIL import Image, ImageTk, ImageSequence   # for GIF support


class MusicPlayerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("My Music Playlist")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        
        self.animation_speed = 50
        self.hover_animations = {}
        self.pulse_phase = 0
        self.loading_angle = 0

        self.audio_available = True
        try:
            pygame.mixer.init()
        except Exception as e:
            self.audio_available = False
            print("Warning: pygame.mixer.init() failed:", e)

        self.music_queue = deque()
        self.current_song = None
        self.is_playing = False
        self.is_paused = False

        # for GIF
        self.spinner_frames = []
        self.spinner_index = 0

        self.setup_ui()
        self.load_spinner_gif("nailong.gif")  # load your gif
        self.start_animations()
        self.check_playback_status()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#1a1a2e', relief=tk.FLAT, bd=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=(0, 20))

        self.title_label = tk.Label(title_frame, text="🎵 MY MUSIC PLAYER", 
                                   font=('Arial', 20, 'bold'), fg='#00ff88', bg='#1a1a2e')
        self.title_label.pack()

        self.add_music_btn = self.create_animated_button(main_frame, "ADD SONGS", 
                                                        self.add_music_files, '#ff6b6b', '#ff5252')
        self.add_music_btn.pack(pady=10)

        current_frame = tk.Frame(main_frame, bg='#16213e', relief=tk.RAISED, bd=2)
        current_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(current_frame, text="♪ NOW PLAYING ♪", 
                font=('Arial', 12, 'bold'), fg='#00ff88', bg='#16213e').pack(pady=(10, 5))

        # Big GIF in the middle like Spotify
        self.spinner_label = tk.Label(current_frame, bg='#16213e')
        self.spinner_label.pack(pady=20)

        self.current_song_label = tk.Label(current_frame, text="No song selected", 
                                          font=('Arial', 11), fg='#ffffff', bg='#16213e',
                                          wraplength=400)
        self.current_song_label.pack(pady=(0, 10))

        control_frame = tk.Frame(main_frame, bg='#1a1a2e')
        control_frame.pack(pady=20)
        
        self.play_btn = self.create_animated_button(control_frame, "▶️ PLAY", 
                                                   self.play_pause_music, '#4CAF50', '#45a049')
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = self.create_animated_button(control_frame, "⏹️ STOP", 
                                                   self.stop_music, '#f44336', '#da190b')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = self.create_animated_button(control_frame, "⏭️ NEXT", 
                                                   self.next_song, '#FF9800', '#F57C00')
        self.next_btn.pack(side=tk.LEFT, padx=5)

        volume_frame = tk.Frame(main_frame, bg='#1a1a2e')
        volume_frame.pack(pady=10)
        
        tk.Label(volume_frame, text="🔊 VOLUME", font=('Arial', 10, 'bold'), 
                fg='#ffffff', bg='#1a1a2e').pack(side=tk.LEFT, padx=(0, 10))
        
        self.volume_var = tk.DoubleVar(value=70)
        self.volume_scale = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                    variable=self.volume_var, command=self.change_volume,
                                    bg='#2d2d2d', fg='#ffffff', highlightthickness=0,
                                    troughcolor='#404040', activebackground='#00ff88')
        self.volume_scale.pack(side=tk.LEFT)

        queue_frame = tk.Frame(main_frame, bg='#16213e', relief=tk.RAISED, bd=2)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        queue_header = tk.Frame(queue_frame, bg='#16213e')
        queue_header.pack(fill=tk.X, pady=10)
        
        tk.Label(queue_header, text="🎼 QUEUE", font=('Arial', 12, 'bold'), 
                fg='#00ff88', bg='#16213e').pack(side=tk.LEFT, padx=20)
        
        self.queue_count_label = tk.Label(queue_header, text="(0 songs)", 
                                         font=('Arial', 10), fg='#cccccc', bg='#16213e')
        self.queue_count_label.pack(side=tk.LEFT, padx=10)

        queue_list_frame = tk.Frame(queue_frame, bg='#16213e')
        queue_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.queue_listbox = tk.Listbox(queue_list_frame, bg='#2d2d2d', fg='#ffffff',
                                       selectbackground='#00ff88', selectforeground='#000000',
                                       font=('Arial', 10), relief=tk.FLAT, bd=0,
                                       highlightthickness=0, activestyle='none')
        
        queue_scrollbar = tk.Scrollbar(queue_list_frame, orient=tk.VERTICAL, 
                                      bg='#2d2d2d', troughcolor='#1a1a1a')
        
        self.queue_listbox.config(yscrollcommand=queue_scrollbar.set)
        queue_scrollbar.config(command=self.queue_listbox.yview)
        
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        queue_btn_frame = tk.Frame(queue_frame, bg='#16213e')
        queue_btn_frame.pack(pady=(0, 15))
        
        self.remove_btn = self.create_animated_button(queue_btn_frame, "REMOVE", 
                                                     self.remove_selected, '#e74c3c', '#c0392b')
        self.remove_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = self.create_animated_button(queue_btn_frame, "CLEAR ALL", 
                                                    self.clear_queue, '#95a5a6', '#7f8c8d')
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.peek_btn = self.create_animated_button(queue_btn_frame, "PEEK QUEUE", 
                                                   self.peek_queue, '#3498db', '#2980b9')
        self.peek_btn.pack(side=tk.LEFT, padx=5)

        self.loading_frame = tk.Frame(main_frame, bg='#1a1a2e')
        self.loading_label = tk.Label(self.loading_frame, text="⟳ Loading...", 
                                     font=('Arial', 12), fg='#00ff88', bg='#1a1a2e')
        self.loading_label.pack()
        
        if not self.audio_available:
            self.play_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
    
    def create_animated_button(self, parent, text, command, color1, color2):
        btn = tk.Button(parent, text=text, command=command,
                       bg=color1, fg='white', font=('Arial', 10, 'bold'),
                       relief=tk.FLAT, padx=20, pady=8, cursor='hand2',
                       borderwidth=0, highlightthickness=0)
        btn.original_color = color1
        btn.hover_color = color2
        btn.current_color = color1
        btn.bind("<Enter>", lambda e: self.start_hover_animation(btn, True))
        btn.bind("<Leave>", lambda e: self.start_hover_animation(btn, False))
        return btn
    
    def start_hover_animation(self, button, entering):
        target_color = button.hover_color if entering else button.original_color
        button.current_color = target_color
        button.config(bg=target_color)
    
    def start_animations(self):
        self.animate_title()
        self.animate_spinner()
        self.animate_loading()
    
    def animate_title(self):
        self.pulse_phase += 0.1
        intensity = int(128 + 127 * math.sin(self.pulse_phase))
        color = f"#{intensity:02x}ff88"
        self.title_label.config(fg=color)
        self.root.after(100, self.animate_title)

    # -------------------- GIF spinner --------------------
    def load_spinner_gif(self, nailong_gif):
        try:
            gif = Image.open(nailong_gif)
            frames = []
            for frame in ImageSequence.Iterator(gif):
                f = frame.convert("RGBA").copy()
                f = f.resize((120, 120), Image.Resampling.LANCZOS)  # Spotify-like big GIF
                frames.append(ImageTk.PhotoImage(f))
            if frames:
                self.spinner_frames = frames
                self.spinner_index = 0
            else:
                self.spinner_frames = []
        except Exception as e:
            print("Could not load GIF:", e)
            self.spinner_frames = []

    def animate_spinner(self):
        if self.spinner_frames and self.is_playing and not self.is_paused:
            frame = self.spinner_frames[self.spinner_index]
            self.spinner_label.config(image=frame, text="")
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            delay = 80
            self.root.after(delay, self.animate_spinner)
            return
        else:
            icon = "⏸️" if self.is_paused else "⏹️"
            self.spinner_label.config(image="", text=icon, font=('Arial', 30), fg='#cccccc')
        self.root.after(150, self.animate_spinner)
    # -----------------------------------------------------

    def animate_loading(self):
        self.loading_angle += 30
        if self.loading_angle >= 360:
            self.loading_angle = 0
        rotation_chars = ['⟳', '⟲', '⟳', '⟲']
        char_index = (self.loading_angle // 90) % len(rotation_chars)
        self.loading_label.config(text=f"{rotation_chars[char_index]} Loading...")
        self.root.after(200, self.animate_loading)
    
    def show_loading(self, show=True):
        if show:
            self.loading_frame.pack(pady=10)
        else:
            self.loading_frame.pack_forget()
    
    def add_music_files(self):
        self.show_loading(True)
        
        def load_files():
            file_types = [
                ("Audio Files", "*.mp3 *.wav *.ogg *.m4a"),
                ("All Files", "*.*")
            ]
            files = filedialog.askopenfilenames(title="Select Music", filetypes=file_types)
            if files:
                for file in files:
                    self.music_queue.append(file)
                time.sleep(0.5)
                self.root.after(0, lambda: [
                    self.update_queue_display(),
                    self.show_loading(False),
                    messagebox.showinfo("Success", f"Added {len(files)} music file(s) to queue!")
                ])
            else:
                self.root.after(0, lambda: self.show_loading(False))
        threading.Thread(target=load_files, daemon=True).start()
    
    def update_queue_display(self):
        self.queue_listbox.delete(0, tk.END)
        for i, song in enumerate(self.music_queue, 1):
            song_name = os.path.basename(song)
            display_text = f"{i:02d}. {song_name}"
            self.queue_listbox.insert(tk.END, display_text)
        count = len(self.music_queue)
        self.queue_count_label.config(text=f"({count} song{'s' if count != 1 else ''})")
        self.queue_count_label.config(fg='#00ff88' if count > 0 else '#cccccc')
    
    def change_volume(self, value):
        if self.audio_available:
            volume = float(value) / 100
            pygame.mixer.music.set_volume(volume)
    
    def peek_queue(self):
        if not self.music_queue:
            messagebox.showinfo("No Songs", "The queue is empty!")
            return
        peek_window = tk.Toplevel(self.root)
        peek_window.title("🔍 Peek Queue")
        peek_window.geometry("500x400")
        peek_window.configure(bg='#1a1a2e')
        peek_window.transient(self.root)
        peek_window.grab_set()
        peek_window.attributes('-alpha', 0.0)
        self.fade_in_window(peek_window)
        header_frame = tk.Frame(peek_window, bg="#252b3d", height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🎼 QUEUE BROWSER", 
                font=('Arial', 14, 'bold'), fg='#00ff88', bg='#16213e').pack(pady=15)
        listbox_frame = tk.Frame(peek_window, bg='#1a1a2e')
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        listbox = tk.Listbox(listbox_frame, bg='#2d2d2d', fg='#ffffff',
                            selectbackground='#00ff88', selectforeground='#000000',
                            font=('Arial', 11), relief=tk.FLAT, bd=0,
                            highlightthickness=0, activestyle='none')
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL,
                                bg='#2d2d2d', troughcolor='#1a1a1a')
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for i, song in enumerate(self.music_queue, 1):
            song_name = os.path.basename(song)
            display_text = f"{i:02d}. ♪ {song_name}"
            listbox.insert(tk.END, display_text)
        instruction_frame = tk.Frame(peek_window, bg='#16213e')
        instruction_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Label(instruction_frame, text="💡 Double-click a song to play it directly", 
                font=('Arial', 10), fg='#cccccc', bg='#16213e').pack(pady=10)
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                self.play_selected_from_queue(index)
                self.fade_out_window(peek_window)
        listbox.bind("<Double-Button-1>", on_double_click)
    
    def fade_in_window(self, window, alpha=0.0):
        alpha += 0.1
        window.attributes('-alpha', alpha)
        if alpha < 1.0:
            self.root.after(50, lambda: self.fade_in_window(window, alpha))
    
    def fade_out_window(self, window, alpha=1.0):
        alpha -= 0.1
        window.attributes('-alpha', alpha)
        if alpha > 0.0:
            self.root.after(50, lambda: self.fade_out_window(window, alpha))
        else:
            window.destroy()
    
    def play_selected_from_queue(self, index):
        if index < 0 or index >= len(self.music_queue):
            return
        queue_list = list(self.music_queue)
        selected_song = queue_list.pop(index)
        self.music_queue = deque(queue_list)
        self.stop_music()
        try:
            pygame.mixer.music.load(selected_song)
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            self.play_btn.config(text="⏸️ PAUSE")
            song_name = os.path.basename(selected_song)
            self.current_song_label.config(text=song_name, fg='#00ff88')
            self.current_song = selected_song
            self.update_queue_display()
            self.pulse_current_song()
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play file:\n{selected_song}\n\n{str(e)}")
    
    def pulse_current_song(self):
        if self.is_playing:
            current_fg = self.current_song_label.cget('fg')
            self.current_song_label.config(fg='#ffffff' if current_fg == '#00ff88' else '#00ff88')
            self.root.after(1000, self.pulse_current_song)
    
    def play_pause_music(self):
        if not self.audio_available:
            messagebox.showwarning("Audio Unavailable", "Audio device not initialized. Playback disabled.")
            return
        if not self.music_queue and not self.current_song:
            messagebox.showwarning("No Music", "Please add music to the queue first!")
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            self.play_btn.config(text="⏸️ PAUSE")
            self.pulse_current_song()
        elif self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.play_btn.config(text="▶️ PLAY")
        else:
            self.play_next_song()
    
    def play_next_song(self):
        if self.music_queue:
            self.current_song = self.music_queue.popleft()
            self.update_queue_display()
            try:
                pygame.mixer.music.load(self.current_song)
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused = False
                self.play_btn.config(text="⏸️ PAUSE")
                song_name = os.path.basename(self.current_song)
                self.current_song_label.config(text=song_name, fg='#00ff88')
                self.pulse_current_song()
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play file:\n{self.current_song}\n\n{str(e)}")
                self.current_song = None
                self.is_playing = False
                self.play_btn.config(text="▶️ PLAY")
                if self.music_queue:
                    self.play_next_song()
        else:
            messagebox.showinfo("Queue Empty", "No more songs in queue!")
    
    def stop_music(self):
        if self.audio_available:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_song = None
        self.play_btn.config(text="▶️ PLAY")
        self.current_song_label.config(text="No song selected", fg='#cccccc')
    
    def next_song(self):
        if self.music_queue:
            self.stop_music()
            self.root.after(100, self.play_next_song)
        else:
            messagebox.showinfo("Queue Empty", "No more songs in queue!")
    
    def remove_selected(self):
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
            removed_song = list(self.music_queue)[index]
            queue_list = list(self.music_queue)
            queue_list.pop(index)
            self.music_queue = deque(queue_list)
            self.update_queue_display()
            song_name = os.path.basename(removed_song)
            messagebox.showinfo("Removed", f"♪ Removed: {song_name}")
        else:
            messagebox.showwarning("No Selection", "Please select a song to remove!")
    
    def clear_queue(self):
        if self.music_queue:
            if messagebox.askyesno("Clear Queue", "🗑️ Are you sure you want to clear the entire queue?"):
                self.music_queue.clear()
                self.update_queue_display()
                messagebox.showinfo("Cleared", "✨ Queue cleared!")
        else:
            messagebox.showinfo("Empty Queue", "Queue is already empty!")
    
    def check_playback_status(self):
        if self.is_playing and self.audio_available and not pygame.mixer.music.get_busy() and not self.is_paused:
            if self.music_queue:
                self.play_next_song()
            else:
                self.stop_music()
        self.root.after(1000, self.check_playback_status)


def main():
    root = tk.Tk()
    root.resizable(True, True)
    root.minsize(600, 500)
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (800 // 2)
    y = (root.winfo_screenheight() // 2) - (600 // 2)
    root.geometry(f"800x600+{x}+{y}")
    app = MusicPlayerGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
    finally:
        if app.audio_available:
            pygame.mixer.quit()


if __name__ == "__main__":
    main()
