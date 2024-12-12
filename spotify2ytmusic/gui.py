#!/usr/bin/env python3

import os
import subprocess
import sys
import threading
import json
import tkinter as tk
from tkinter import ttk

from . import cli
from . import backend
from . import spotify_backup
from typing import Callable


def create_label(parent: tk.Frame, text: str, **kwargs) -> tk.Label:
    """Simply creates a label with the given text and the given parent.

    Args:
        parent (tk.Frame): The parent of the label.
        text (str): The text of the label.

    Returns:
        tk.Label: The label created.
    """
    return tk.Label(
        parent,
        text=text,
        font=("Helvetica", 14),
        background="#26242f",
        foreground="white",
        **kwargs,
    )


def create_button(parent: tk.Frame, text: str, **kwargs) -> tk.Button:
    """Simply creates a button with the given text and the given parent.

    Args:
        parent (tk.Frame): The parent of the button.
        text (str): The text of the button.

    Returns:
        tk.Button: The button created.
    """
    return tk.Button(
        parent,
        text=text,
        font=("Helvetica", 14),
        background="#696969",
        foreground="white",
        border=1,
        **kwargs,
    )


class Window:
    """The main window of the application. It contains the tabs and the logs."""

    def __init__(self) -> None:
        """Initializes the main window of the application. It contains the tabs and the logs."""
        self.root = tk.Tk()
        self.root.title("Spotify to YT Music")
        self.root.geometry("1280x720")
        self.root.config(background="#26242f")

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TNotebook.Tab", background="#121212", foreground="white"
        )  # Set the background color to #121212 when not selected
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#26242f")],
            foreground=[("selected", "#ffffff")],
        )  # Set the background color to #26242f and text color to white when selected
        style.configure("TFrame", background="#26242f")
        style.configure("TNotebook", background="#121212")

        # Redirect stdout to GUI
        sys.stdout.write = self.redirector

        self.root.after(1, lambda: self.yt_login(auto=True))
        self.root.after(1, lambda: self.load_write_settings(0))

        # Create a PanedWindow with vertical orientation
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Create a Frame for the tabs
        self.tab_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tab_frame, weight=2)

        # Create the TabControl (notebook)
        self.tabControl = ttk.Notebook(self.tab_frame)
        self.tabControl.pack(fill=tk.BOTH, expand=1)

        # Create the tabs
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        # self.tab2 = ttk.Frame(self.tabControl)
        self.tab3 = ttk.Frame(self.tabControl)
        self.tab4 = ttk.Frame(self.tabControl)
        self.tab5 = ttk.Frame(self.tabControl)
        self.tab6 = ttk.Frame(self.tabControl)
        self.tab7 = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab1, text="Login to YT Music")
        self.tabControl.add(self.tab2, text="Spotify backup")

        # self.tabControl.add(self.tab2, text='Reverse playlist')
        self.tabControl.add(self.tab3, text="Load liked songs")
        self.tabControl.add(self.tab4, text="List playlists")
        self.tabControl.add(self.tab5, text="Copy all playlists")
        self.tabControl.add(self.tab6, text="Copy a specific playlist")
        self.tabControl.add(self.tab7, text="Settings")

        # Create a Frame for the logs
        self.log_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.log_frame, weight=1)

        # Create the Text widget for the logs
        self.logs = tk.Text(self.log_frame, font=("Helvetica", 14))
        self.logs.pack(fill=tk.BOTH, expand=1)
        self.logs.config(background="#26242f", foreground="white")

        # tab1
        create_label(
            self.tab1,
            text="Welcome to Spotify to YT Music!\nTo start, you need to login to YT Music.",
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(self.tab1, text="Login", command=self.yt_login).pack(
            anchor=tk.CENTER, expand=True
        )

        # tab2

        create_label(
            self.tab2, text="First, you need to backup your spotify playlists"
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab2,
            text="Backup",
            command=lambda: self.call_func(
                func=spotify_backup.main, args=(), next_tab=self.tab3
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # tab3
        create_label(self.tab3, text="Now, you can load your liked songs.").pack(
            anchor=tk.CENTER, expand=True
        )
        create_button(
            self.tab3,
            text="Load",
            command=lambda: self.call_func(
                func=backend.copier,
                args=(
                    backend.iter_spotify_playlist(),
                    None,
                    False,
                    0.1,
                    self.var_algo.get(),
                ),
                next_tab=self.tab4,
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # tab4
        create_label(
            self.tab4, text="Here, you can get a list of your playlists, with their ID."
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab4,
            text="List",
            command=lambda: self.call_func(
                func=cli.list_playlists, args=(), next_tab=self.tab5
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # tab5
        create_label(
            self.tab5,
            text="Here, you can copy all your playlists from Spotify to YT Music. Please note that this step "
            "can take a long time since songs are added one by one.",
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab5,
            text="Copy",
            command=lambda: self.call_func(
                func=backend.copy_all_playlists,
                args=(0.1, False, "utf-8", self.var_algo.get()),
                next_tab=self.tab6,
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # tab6
        create_label(
            self.tab6,
            text="Here, you can copy a specific playlist from Spotify to YT Music.",
        ).pack(anchor=tk.CENTER, expand=True)
        create_label(self.tab6, text="Spotify playlist ID:").pack(
            anchor=tk.CENTER, expand=True
        )
        self.spotify_playlist_id = tk.Entry(self.tab6)
        self.spotify_playlist_id.pack(anchor=tk.CENTER, expand=True)
        create_label(self.tab6, text="YT Music playlist ID:").pack(
            anchor=tk.CENTER, expand=True
        )
        self.yt_playlist_id = tk.Entry(self.tab6)
        self.yt_playlist_id.pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab6,
            text="Copy",
            command=lambda: self.call_func(
                func=backend.copy_playlist,
                args=(
                    self.spotify_playlist_id.get().strip(),
                    self.yt_playlist_id.get(),
                    "utf-8",
                    False,
                    0.1,
                    self.var_algo.get(),
                ),
                next_tab=self.tab6,
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # tab7
        self.var_scroll = tk.BooleanVar()

        auto_scroll = tk.Checkbutton(
            self.tab7,
            text="Auto scroll",
            variable=self.var_scroll,
            command=lambda: self.load_write_settings(1),
            background="#696969",
            foreground="#ffffff",
            selectcolor="#26242f",
            border=1,
        )
        auto_scroll.pack(anchor=tk.CENTER, expand=True)
        auto_scroll.select()

        self.var_algo = tk.IntVar()
        self.var_algo.set(0)

        self.algo_label = create_label(self.tab7, text=f"Algorithm: ")
        self.algo_label.pack(anchor=tk.CENTER, expand=True)

        menu_algo = tk.OptionMenu(
            self.tab7,
            self.var_algo,
            0,
            *[1, 2],
            command=lambda x: self.load_write_settings(1),
        )
        menu_algo.pack(anchor=tk.CENTER, expand=True)
        menu_algo.config(background="#696969", foreground="#ffffff", border=1)

    def redirector(self, input_str="") -> None:
        """
        Inserts the input string into the logs widget and disables editing.

        Args:
            self: The instance of the class.
            input_str (str): The string to be inserted into the logs' widget.
        """
        self.logs.config(state=tk.NORMAL)
        self.logs.insert(tk.END, input_str)
        self.logs.config(state=tk.DISABLED)
        if self.var_scroll.get():
            self.logs.see(tk.END)

    def call_func(self, func: Callable, args: tuple, next_tab: ttk.Frame) -> None:
        """Calls the given function in a separate thread and switches to the next tab when the function is done.

        Args:
            func (Callable): The function to be called.
            args (tuple): The arguments to be passed to the function. If no arguments are needed, pass an empty tuple.
            next_tab (ttk.Frame): The tab to switch to when the function is done. If no switch needed, pass the current one.
        """
        th = threading.Thread(target=func, args=args)
        th.start()
        while th.is_alive():
            self.root.update()
        self.tabControl.select(next_tab)
        print()

    def yt_login(self, auto=False) -> None:
        """Logs in to YT Music. If the browser.json file is not found, it opens a new console window to run the 'ytmusicapi browser' command.

        Args:
            auto (bool, optional): Weather to automatically login using the oauth.json file. Defaults to False.
        """

        def run_in_thread():
            if os.path.exists("browser.json"):
                print("File detected, auto login")
            elif auto:
                print("No file detected. Manual login required")
                return
            else:
                print("File not detected, login required")

                # Open a new console window to run the command
                if os.name == "nt":  # If the OS is Windows
                    try:
                        process = subprocess.Popen(
                            ["ytmusicapi", "browser"],
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                        )
                    except FileNotFoundError as e:
                        print(
                            f"ERROR: Unable to run 'ytmusicapi browser'.  Is ytmusicapi installed?  Perhaps try running 'pip install ytmusicapi' Exception: {e}"
                        )
                        sys.exit(1)
                    process.communicate()
                else:  # For Unix and Linux
                    try:
                        subprocess.call(
                            "x-terminal-emulator -e ytmusicapi browser",
                            shell=True,
                            stdout=subprocess.PIPE,
                        )
                    except:
                        subprocess.call(
                            "xterm -e ytmusicapi browser",
                            shell=True,
                            stdout=subprocess.PIPE,
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")


            self.tabControl.select(self.tab2)
            print()

        # Run the function in a separate thread
        th = threading.Thread(target=run_in_thread)
        th.start()

    def load_write_settings(self, action: int) -> None:
        """Loads or writes the settings to the settings.json file.

        Args:
            action (int): 0 to load the settings, 1 to write the settings.
        """
        texts = {0: "Exact match", 1: "Fuzzy match", 2: "Fuzzy match with videos"}

        exist = True
        if action == 0:
            with open("settings.json", "a+"):
                pass
            with open("settings.json", "r+") as f:
                value = f.read()
                if value == "":
                    exist = False
            if exist:
                with open("settings.json", "r+") as f:
                    settings = json.load(f)
                    self.var_scroll.set(settings["auto_scroll"])
                    self.var_algo.set(settings["algo_number"])
        else:
            with open("settings.json", "w+") as f:
                settings = {
                    "auto_scroll": self.var_scroll.get(),
                    "algo_number": self.var_algo.get(),
                }
                json.dump(settings, f)

        self.algo_label.config(text=f"Algorithm: {texts[self.var_algo.get()]}")
        self.root.update()


def main() -> None:
    ui = Window()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
