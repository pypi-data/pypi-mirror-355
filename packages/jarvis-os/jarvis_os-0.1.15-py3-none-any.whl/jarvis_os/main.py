# Copyright 2025 Arvin Adeli
# Licensed under the Apache License, Version 2.0
# http://www.apache.org/licenses/LICENSE-2.0

import os
import sys

current_directory = os.getcwd()

def main():
    os.environ["VOSK_LOG_LEVEL"] = "0"

    import vosk
    import pyaudio
    import json
    import subprocess
    from collections import deque
    import requests
    from jarvis_os.yapper.core import Yapper, PiperSpeaker
    from jarvis_os.yapper.enhancer import GroqEnhancer
    from jarvis_os.yapper.speaker import BaseSpeaker
    from jarvis_os.yapper.speaker import PiperVoiceUS
    import threading
    import queue
    import urllib.request
    import zipfile
    import pygame
    import re
    import textwrap
    import pygetwindow as gw
    import psutil
    import shutil 
    from rich.console import Console
    console = Console(force_terminal=True, color_system="truecolor")

    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    import time
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.progress import SpinnerColumn
    import itertools
    import contextlib
    from rich.status import Status
    import time
    from datetime import datetime
    from google import genai
    from google.genai import types
    from fuzzywuzzy import process


    state = {
        "awaiting_shutdown" : False,
        "is_speaking" : False,
        "is_stopped" : False

    }
    app_processes = {}

    local = False
    chat_history = [{"role": "system", "content": "You are Jarvis, a helpful and concise AI assistant."}]
    screen_queue = queue.Queue()
    llm_stop_event = threading.Event()
    system_commands = {
            "settings": "start ms-settings:",
            "file explorer": "explorer",
            "copilot": "start ms-copilot:"
            # Add more here as needed
        }

    

    def ensure_vosk_model():
        base_dir = os.path.expanduser("~/.jarvis-os/models")
        model_name = "vosk-model-en-us-0.42-gigaspeech"
        model_path = os.path.join(base_dir, model_name)

        if os.path.isdir(model_path) and os.listdir(model_path):
            return model_path

        with console.status("[bold cyan]Vosk model not found. Downloading now...[/bold cyan]", spinner="dots") as status_vosk:
            os.makedirs(base_dir, exist_ok=True)
            zip_path = os.path.join(base_dir, f"{model_name}.zip")
            url = f"https://alphacephei.com/vosk/models/{model_name}.zip"

            try:
                urllib.request.urlretrieve(url, zip_path)
            except Exception as e:
                console.print(f"[red]Failed to download Vosk model: {e}[/red]")
                raise

            status_vosk.update("[bold cyan]Extracting model...[/bold cyan]")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(base_dir)

            os.remove(zip_path)
            status_vosk.update("[bold green]Model setup complete.[/bold green]")

        return model_path


    def glowing_boot_animation():
        ascii_jarvis = [
                "    _   _    ______     _____ ____         ___  ____  ",
                "     | | / \  |  _ \ \   / /_ _/ ___|       / _ \/ ___| ",
                "  _  | |/ _ \ | |_) \ \ / / | |\___ \ _____| | | \___ \ ",
                " | |_| / ___ \|  _ < \ V /  | | ___) |_____| |_| |___) |",
                "  \___/_/   \_\_| \_\ \_/  |___|____/       \___/|____/ ",
            ]

        width = shutil.get_terminal_size((80, 20)).columns

        with Live(console=console, refresh_per_second=5) as live:
            for i in range(1, len(ascii_jarvis) + 1):
                styled_text = Text(justify="center", no_wrap=True)
                for line in ascii_jarvis[:i]:
                    styled_text.append(line + "\n", style="bold bright_magenta")
                panel = Panel(styled_text, border_style="bold magenta", padding=(1, 4), width=width)
                live.update(panel)
                time.sleep(0.4)

            # Final glow
            time.sleep(0.3)
            final_text = Text(justify="center", no_wrap=True)
            for line in ascii_jarvis:
                final_text.append(line + "\n", style="bold cyan")
            panel = Panel(final_text, border_style="bold blue", padding=(1, 4), width=width)
            live.update(panel)
            time.sleep(1.2)


    @contextlib.contextmanager
    def suppress_stderr(log_path = "~/.jarvis-os/logs/jarvis.log"):
        log_path = os.path.expanduser(log_path)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, 'w') as log_file:
            stderr_fileno = sys.stderr.fileno()
            with os.fdopen(os.dup(stderr_fileno), 'w') as old_stderr:
                os.dup2(log_file.fileno(), stderr_fileno)
                try:
                    yield
                finally:
                    os.dup2(old_stderr.fileno(), stderr_fileno)

    def load_vosk_model_with_spinner():

        model_path = ensure_vosk_model()
        #spinner_cycle = itertools.cycle(["|  |  |  |  |  |", "J  A  R  V  I  S", "|  |  |  |  |  |", "/  /  /  /  /  /", "-  -  -  -  -  -", "\\  \\  \\  \\  \\  \\"])
        spinner_cycle = itertools.cycle([
                                            "|  |  |  |  |  |",       # classic spinner
                                            "/  /  /  /  /  /",
                                            "-  -  -  -  -  -",
                                            "\\  \\  \\  \\  \\  \\",

                                            "J  |  |  |  |  |",       # morph begins
                                            "J  A  |  |  |  |",
                                            "J  A  R  |  |  |",
                                            "J  A  R  V  |  |",
                                            "J  A  R  V  I  |",
                                            "J  A  R  V  I  S",       # full reveal
                                            "J  A  R  V  I  S",
                                            "J  A  R  V  I  |",       # morph out
                                            "J  A  R  V  |  |",
                                            "J  A  R  |  |  |",
                                            "J  A  |  |  |  |",
                                            "J  |  |  |  |  |",
                                            "|  |  |  |  |  |",       # back to spinner
                                        ])
        loading_text = "Loading Speech Recognition Model:  "

        with Live(console=console, refresh_per_second=10) as live:
            start_time = time.time()
            done = threading.Event()

            def animate_spinner():
                while not done.is_set():
                    spinner = next(spinner_cycle)
                    text = Text(f"{loading_text} {spinner}", style="bold bright_magenta")
                    live.update(Panel(text, border_style="bright_magenta"))
                    time.sleep(0.1)

            spinner_thread = threading.Thread(target=animate_spinner, daemon=True)
            spinner_thread.start()

            # Load model (this part blocks the main thread)
            with suppress_stderr("~/.jarvis-os/logs/jarvis.log"):
                model = vosk.Model(model_path)

            done.set()  # stop spinner
            spinner_thread.join()

            # Show success panel
            elapsed = time.time() - start_time
            success = Text(f"✓ Model loaded in {elapsed:.1f} seconds", style="bold cyan")
            live.update(Panel(success, border_style="cyan"))
            time.sleep(1)

        return model



    glowing_boot_animation()

    model = load_vosk_model_with_spinner()

    #model = vosk.Model(r"C:\Users\arvin\Documents\Jarvis\vosk-model-en-us-0.42-gigaspeech")
    #engine = pyttsx3.init()
    lessac = PiperSpeaker(voice = PiperVoiceUS.JOE)
    yapr = Yapper(speaker = lessac)

    sentence_queue = queue.Queue()
    stop_event = threading.Event()
    
    def yap_thread():
        while True:
            sentence = sentence_queue.get()
            if stop_event.is_set():
                continue  # Skip speaking entirely if stop triggered
            if sentence:
                state["is_speaking"] = True
                if isinstance(sentence, str):
                    yapr.yap(sentence.strip())  # Will be interrupted if speaker supports it
                state["is_speaking"] = False

    threading.Thread(target=yap_thread, daemon=True).start()
    


    def screen_thread():
        while True:
            msg = screen_queue.get()
            if msg is None:
                break

            console.print(Text(msg, style="bold yellow"), end="", soft_wrap=True)



    threading.Thread(target=screen_thread, daemon=True).start()

    # Initialize microphone input
    # p = pyaudio.PyAudio()
    # stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, 
    #                 input=True, frames_per_buffer=4000)
    p = pyaudio.PyAudio()
    default_device_index = p.get_default_input_device_info()['index']
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, input_device_index=default_device_index,
                    frames_per_buffer=4000)

    stream.start_stream()

    recognizer = vosk.KaldiRecognizer(model, 16000)

    def interpret_command(command: str):
        # Try strict keyword match first
        for keyword, action in command_actions.items():
            if keyword in command.lower():
                return action

        # Try fuzzy fallback
        best_match, score = process.extractOne(command, command_actions.keys())
        if score > 80:
            return command_actions[best_match]

        # Optionally: ask Gemini if both fail

        return None

    def shutdown(command):
        if "shutdown" in command.lower() or "shut down" in command.lower() :
            console.print("[bold green_yellow]Are you sure you want to shutdown now?[/bold green_yellow]")
            yapr.yap("Are you sure you want to shutdown now?")
            state["awaiting_shutdown"] = True
            return True
        else:
            return False


    def google(command):
        if "google" in command.lower() or "look up" in command.lower():
            search = command.lower().replace("google", "").replace("look up", "").strip()
            words = search.split()
            url = "https://www.google.com/search?q="

            for item in words:
                if url != "https://www.google.com/search?q=":
                    url += "+"
                url += item

            try:
                subprocess.run(["start", url], shell=True, check=True)
                sentence_queue.put("Sure. Googling " + search + " now.")
            except Exception as e:
                print(f"Google Search Failed: {e}")
            return True
        else:
            return False

    def youtube(command):
        if "search youtube" in command.lower() or "youtube search" in command.lower() or "youtube search for" in command.lower():
            search = command.lower().replace("youtube search for", "").replace("youtube search", "").replace("search youtube", "").strip()
            words = search.split()
            url = "https://www.youtube.com/results?search_query="

            for item in words:
                if url != "https://www.youtube.com/results?search_query=":
                    url += "+"
                url += item

            try:
                subprocess.run(["start", url], shell=True, check=True)
                sentence_queue.put("Sure. Searching YouTube for " + search + " now.")
            except Exception as e:
                print(f"YouTube Search Failed: {e}")
            return True
        else:
            return False

    def extract_app_name(command):
        command = command.lower()
        for verb in ["open", "start", "launch", "run"]:
            if verb in command:
                command = command.replace(verb, "")
        command = command.strip()

        # Clean up trailing polite phrases or noise
        command = re.sub(r"\b(for me|please|now|up)\b", "", command).strip()

        # Optional: map verbose names to executable names
        app_aliases = {
            "google chrome": "chrome",
            "chrome browser": "chrome",
            "file explorer": "explorer",
            "ms word": "winword",
            "copilot": "copilot",
            "vs code": "code",
        }

        return app_aliases.get(command, command)

    def gemini_match_filename(files, target):

        prompt = (
            f"You're given a list of file and directory names:\n\n{files}\n\n"
            f"The user said: '{target}'\n\n"
            "Which label are they most likely referring to? "
            "Return only the exact filename or directory from the list, or 'unsure' if unsure."
        )

        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]

        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            reply = response.candidates[0].content.parts[0].text.strip()
            if reply in files:
                return reply
            return "unsure"
        except Exception as e:
            print(f"[Gemini match error] {e}")
            return "unsure"

    ####################### tools
    def search_files(keyword, folder=".", extensions=None):
        matches = []
        for root, _, files in os.walk(folder):
            for file in files:
                if keyword.lower() in file.lower():
                    if extensions:
                        if not any(file.lower().endswith(ext) for ext in extensions):
                            continue
                    full_path = os.path.join(root, file)
                    matches.append(full_path)
        return matches

    def list_files(folder=None):
        folder = folder or current_directory
        try:
            items = os.listdir(folder)
            display = []
            for item in items:
                full_path = os.path.join(folder, item)
                if os.path.isdir(full_path):
                    display.append(f"[bold dark_olive_green3]{item}/[/bold dark_olive_green3]")
                else:
                    display.append(f"[yellow]{item}[/yellow]")
            return display
        except FileNotFoundError:
            base_folder = os.path.basename(folder)
            return [f"Folder not found: {base_folder}"]


    def change_directory(target: str):
        global current_directory

        target = target.strip().lower()
        if "up" in target or "back" in target:
            new_path = os.path.dirname(current_directory)
        else:
            new_path = os.path.join(current_directory, target)

        if os.path.isdir(new_path):
            current_directory = os.path.abspath(new_path)
            current_folder = os.path.basename(current_directory)

            return f"Changed directory to: {current_folder}"
        else:
            new_folder = os.path.basename(new_path)
            return f"Directory not found: {new_folder}"
        
    # ✅ Move (or rename) a file
    def move_file(source_path, dest_path):
        try:
            shutil.move(source_path, dest_path)
            base_src = os.path.basename(source_path)
            base_dst = os.path.basename(dest_path)

            return f"Moved {base_src} to {base_dst}"
        except Exception as e:
            return f"Error: {e}"


    # ✅ Delete a file with confirmation flag
    def delete_file(path, confirm=False):
        if not confirm:
            return "Confirmation required to delete file."
        try:
            os.remove(path)
            return f"Deleted {path}"
        except Exception as e:
            return f"Error: {e}"


    # ✅ Create a folder
    def create_folder(path):
        try:
            full_path = os.path.join(current_directory, path)
            os.makedirs(full_path, exist_ok=True)
            base_folder = os.path.basename(full_path)
            return f"Created folder: {base_folder}"
        except Exception as e:
            return f"Error: {e}"


    # ✅ Utility: Get the latest modified file in a folder
    def get_latest_file(folder=".", extensions=None):
        try:
            files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            if extensions:
                files = [f for f in files if any(f.lower().endswith(ext) for ext in extensions)]
            if not files:
                return None
            latest = max(files, key=os.path.getmtime)
            return latest
        except Exception as e:
            return f"Error: {e}"



    def delete_folder(path, confirm=False):
        if not confirm:
            return "Confirmation required to delete folder."
        try:
            shutil.rmtree(path)
            base_file = os.path.basename(path)
            return f"Deleted folder: {base_file}"
        except Exception as e:
            return f"Error: {e}"

    def create_file(path):
        try:
            full_path = os.path.join(current_directory, path)
            with open(full_path, "w") as f:
                f.write("")
            base_file = os.path.basename(full_path)
            return f"Created file: {base_file}"
        except Exception as e:
            return f"Error: {e}"
    def show_file_contents(path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            return f"Error reading file: {e}"

    ############################ voice wrappers of tools
    def jarvis_search_files(command):
        keyword = command.replace("search for", "").strip()
        matches = search_files(keyword)
        if matches:
            sentence_queue.put(f"Found {len(matches)} files.")
            screen_queue.put("\n".join(matches))
        else:
            sentence_queue.put("No matching files found.")
        return True

    def jarvis_list_files(command):
        global current_directory

        files = list_files()
        console.print(f"\nCurrent Working Directory: {current_directory}\n")
        console.print("\n".join(files), end="", soft_wrap=True, markup=True)
        #screen_queue.put("\n".join(files))
        sentence_queue.put(f"{len(files)} files listed.")
        return True

    def jarvis_change_directory(command: str):
        target = command.lower().split("to", 1)[-1].strip().strip('"')
        if not target:
            return "Please specify a folder name or say 'go up'."
        if "up" in target or "above" in target or "back" in target or "parent" in target:
            match = "up"
        else:
            match = gemini_match_filename(os.listdir(current_directory), target)

        return change_directory(match)

    def jarvis_create_file(command):
        filename = command.lower().split("create file", 1)[-1].strip().strip('"')
        if not filename:
            return "Please specify a file name."
        return create_file(filename)

    def jarvis_move_file(command):
        try:
            # Example: "move file from downloads/report.txt to documents/archive.txt"
            parts = command.lower().replace("move file", "").strip().split(" to ")
            if len(parts) != 2:
                sentence_queue.put("Please say: move file from [source] to [destination].")
                return True
            source_path = parts[0].replace("from", "").strip()
            source_match = gemini_match_filename(os.listdir(current_directory), source_path)
            dest_path = parts[1].strip()
            dest_match = gemini_match_filename(os.listdir(current_directory), dest_path)
            
            if not source_match or "unsure" in str(source_match).lower():
                sentence_queue.put("I couldn't find the source file.")
                return True
            if not dest_match or "unsure" in str(dest_match).lower():
                sentence_queue.put("I couldn't find the destination file.")
                return True

            result = move_file(os.path.join(current_directory, source_match),
                           os.path.join(current_directory, dest_match))
            sentence_queue.put(result)
        except Exception as e:
            sentence_queue.put(f"Error: {e}")
        return True

    def jarvis_create_folder(command):
        path = command.replace("create folder", "").strip()
        result = create_folder(path)
        sentence_queue.put(result)
        return True

    def jarvis_delete_folder(command):
        folder = command.lower().split("delete folder", 1)[-1].strip().strip('"')
        if not folder:
            return "Please specify a folder name."
        match = gemini_match_filename(os.listdir(current_directory), folder)
        if "unsure" in str(match).lower():
            sentence_queue.put("Could not find that folder.")
            return
        else:
            return delete_folder(match, confirm=True)
    def jarvis_delete_file(command):
        path = command.replace("delete file", "").strip()
        match = gemini_match_filename(os.listdir(current_directory), path)
        if "unsure" in str(match).lower():
            sentence_queue.put("Could not find that file.")
        result = delete_file(match, confirm=True)
        sentence_queue.put(result)
        return True

    def jarvis_get_latest_file(command):
        try:
            # Example: "get latest file in downloads"
            folder = "."
            if "in" in command:
                folder = command.lower().split("in", 1)[-1].strip()
            result = get_latest_file(folder)
            if result:
                sentence_queue.put("Latest file found.")
                screen_queue.put(result)
            else:
                sentence_queue.put("No files found.")
        except Exception as e:
            screen_queue.put(f"Error: {e}")
            sentence_queue.put("Error while trying to access latest file.")
        return True

    def jarvis_show_file(command):
        global current_directory

        filename = command.lower().split("show file", 1)[-1].strip().strip('"')
        if not filename:
            return "Please specify a file to show."
        files = os.listdir(current_directory)
        match = gemini_match_filename(files, filename)

        if "unsure" in str(match):
            sentence_queue.put("Sorry, I couldn't find that file.")
        else:
            full_path_match = os.path.join(current_directory, match)
            show_file_contents(full_path_match)

        return

    ### other actions
    def clear_memory(command):
        chat_history[:] = [chat_history[0]]
        sentence_queue.put("Memory cleared.")

    def switch_to_local(command):
        nonlocal local
        local = True
        sentence_queue.put("Local Mode activated.")

    def switch_to_online(command):
        nonlocal local
        local = False
        sentence_queue.put("Online Mode activated.")

    def open_software(command):
        if not any(trigger in command.lower() for trigger in ["open", "launch"]):
            return False

        app_name = extract_app_name(command)

        # Special system-level commands (not actual executables)


        if app_name in system_commands:
            try:
                subprocess.Popen(system_commands[app_name], shell=True)
                sentence_queue.put(f"Got it. Opening {app_name}.")
                return True
            except Exception as e:
                print(f"Error opening {app_name}: {e}")
                return False

        # Normal executable search and launch
        executable_path = find_executable(app_name)
        if executable_path:
            try:
                process = subprocess.Popen([executable_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
                app_processes[app_name] = process
                sentence_queue.put(f"Got it. Opening {app_name}.")
                return True
            except Exception as e:
                print(f"Error opening {app_name}: {e}")
                return True

        print(f"Could not find the application: {app_name}")
        sentence_queue.put(f"Sorry, I couldn't find {app_name}.")
        return True

    def where_search(app_name):
        """Try to locate the executable using Windows 'where' command."""
        try:
            output = subprocess.check_output(["where", app_name], stderr=subprocess.DEVNULL, shell=True)
            return output.decode().splitlines()[0]  # return first match
        except subprocess.CalledProcessError:
            return None

    def bfs_search_executable(start_dirs, app_name, max_depth=10):
        """Breadth-first search for an .exe in known app folders."""
        target = app_name.lower().strip().replace(" ", "")
        queue = deque([(path, 0) for path in start_dirs])
        visited = set()

        while queue:
            current_dir, depth = queue.popleft()
            if depth > max_depth or current_dir in visited:
                continue
            visited.add(current_dir)

            try:
                with os.scandir(current_dir) as entries:
                    for entry in entries:
                        if entry.is_file():
                            name = entry.name.lower().replace(" ", "")
                            if name.startswith(target) and name.endswith(".exe"):
                                return entry.path
                        elif entry.is_dir():
                            queue.append((entry.path, depth + 1))
            except (PermissionError, FileNotFoundError):
                continue

        return None

    def find_executable(app_name):
        """Find the path to an app either via system path or fallback BFS."""
        app_name = app_name.lower().strip().replace(".exe", "")

        # Try exact match in system PATH using 'where'
        exe_path = where_search(app_name)
        if exe_path:
            return exe_path

        # Try app_name.exe
        exe_path = where_search(app_name + ".exe")
        if exe_path:
            return exe_path

        # Fallback: limited-depth search in common locations
        common_paths = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.path.expanduser("~\\AppData\\Local\\Programs"),
            os.path.expanduser("~\\AppData\\Local"),
            os.path.expanduser("~\\AppData\\Roaming"),
            os.path.expanduser("~\\Desktop")
        ]


        return bfs_search_executable(common_paths, app_name)

    def clean_command(command):
        command = command.lower()
        command = re.sub(r"\b(closedown|closed|close|kill|exit|quit)\b", "", command)
        return command.strip()

    def is_process_running(process_name):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                return True
        return False


    def close_window_by_title(partial_title):
        for window in gw.getWindowsWithTitle(partial_title):
            try:
                window.restore()
                window.close()
                return True
            except Exception:
                continue
        return False

    def close_software(command):
        if not any(trigger in command.lower() for trigger in ["close", "closed", "closedown", "kill", "exit", "quit"]):
            return False

        command = clean_command(command)
        app_name = extract_app_name(command)

        process_aliases = {
            "code": "Code",
            "vs code": "Code",
            "discord": "Discord",
            "copilot": "WindowsCopilot",  # fallback name, not used here directly
            "settings": "SystemSettings",
            "chrome": "chrome",
        }

        window_titles = {
            "copilot": "Copilot",
            "settings": "Settings",
            "code": "Visual Studio Code",
            "discord": "Discord",
            "chrome": "Google Chrome",
        }

        # Step 1: Try closing by window title
        window_title = window_titles.get(app_name, app_name)
        if close_window_by_title(window_title):
            sentence_queue.put(f"Closed {app_name}.")
            if app_name in app_processes:
                del app_processes[app_name]
            return True

        # Step 2: Fallback to taskkill
        process_name = process_aliases.get(app_name, app_name)
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", f"{process_name}.exe"],
                check=True,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            sentence_queue.put(f"Force-closing {app_name}.")
            if app_name in app_processes:
                del app_processes[app_name]
            return True
        except subprocess.CalledProcessError:
            sentence_queue.put(f"Could not close {app_name}.")
            return True

    command_actions = {
    "clear memory": clear_memory,
    "switch to local mode": switch_to_local,
    "switch to online mode": switch_to_online,
    "search for": jarvis_search_files,
    "list files": jarvis_list_files,
    "create folder": jarvis_create_folder,
    "delete file": jarvis_delete_file,
    "move file" : jarvis_move_file,
    "create file" : jarvis_create_file,
    "delete folder" : jarvis_delete_folder,
    "get latest file" : jarvis_get_latest_file,
    "show file" : jarvis_show_file,
    "change directory" : jarvis_change_directory
    # add more as needed
}
    
    def extract_full_text(url):
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Heuristic: just collect all <p> text
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40])
            return text[:1500]  # Optional: cap to 1500 chars for LLM input
        except Exception as e:
            return f"[Error scraping {url}: {e}]"

    def extract_gemini_content(url, char_limit=20000):
        """
        Extracts full-page content with richer structure and context,
        specifically designed for feeding into Gemini models.
        """
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Collect metadata
            title = soup.title.string.strip() if soup.title else ""
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

            # Try also collecting headers for context
            headers = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3']) if len(h.get_text(strip=True)) > 5]

            # Grab long and meaningful paragraphs
            paragraphs = [
                p.get_text(strip=True) for p in soup.find_all('p')
                if len(p.get_text(strip=True)) > 50 and not p.get_text().startswith("©")
            ]

            # Combine everything
            combined = "\n\n".join([
                f"Title: {title}" if title else "",
                f"Description: {description}" if description else "",
                "Headings:\n" + "\n".join(headers) if headers else "",
                "Content:\n" + "\n\n".join(paragraphs)
            ])

            return combined[:char_limit]

        except Exception as e:
            return f"[Error scraping {url}: {e}]"

    def should_web_search(question):
        keywords = [
            # Explicit asking
            "use the web", "using the web", "using the internet", "use the internet", "go online,"


            # General info
            "today", "currently", "latest", "breaking", "recent", "live", "current", "happening", "ongoing",
            "news", "update", "headline", "report", "event", "incident", "story", "alerts",

            # Dates and time-sensitive
            "this week", "this month", "this year", "tomorrow", "yesterday", "tonight", "morning", "afternoon", "evening",
            "calendar", "date", "schedule", "time", "deadline",

            # Questions
            "who is", "who's", "what's", "whose", "what is", "when is", "when did", "when's", "where's", "where is", "how to", "how do", "how does", "how many", "how long", "how much",
            "is it", "are there", "does", "did", "will",

            # People / Places
            "person", "celebrity", "politician", "president", "prime minister", "celebs", "location", "country", "city", "state",
            "CEO", "actor", "singer", "athlete", "influencer", "artist", "born", "die", "death",

            # Dynamic facts
            "weather", "temperature", "forecast", "humidity", "sunrise", "sunset", "rain", "snow",
            "stock", "price", "crypto", "market", "bitcoin", "ethereum", "shares", "value", "worth",
            "score", "game", "match", "tournament", "series", "season", "league", "team", "win", "loss", "tie",

            # Web/pop culture
            "trending", "viral", "reddit", "x", "twitter", "threads", "instagram", "youtube", "tiktok", "views", "subscribers",
            "released", "launch", "dropped", "stream", "episode", "clip", "video", "trailer",

            # Misc data queries
            "conversion", "exchange rate", "convert", "calculator", "population", "height", "age", "distance", "location", "map",
            "definition", "meaning", "synonym", "translate", "translation", "language", "speed", "weight", "rank", "ranking",

            # Indicators of vague/informational intent
            "interesting", "facts", "random", "did you know", "explain", "summary", "top", "list", "stats", "statistics"
        ]

        non_web_search_phrases = [
        # Casual, contains "what", "how", "who", etc.
        "what's up", "what are you doing", "what are you doing right now", "what are you up to",
        "what's going on", "what's happening with you", "what’s new",
        "what is your name", "what's your name", "what are you", "what can you do",
        "what day is it", "what's today's date", "what day of the week is it", "what month is it",
        "what year is it", "what time is it", "what is the time", "what's the time",

        "how are you", "how's it going", "how do you feel", "how can you help", "how does this work",
        "how's your day", "how is your day going", "how do i use you", "how hot is it", "how cold is it",

        "who are you", "who's your creator",

        "when is your birthday", "when do you sleep", "when are you active",

        "where is your code", "where do you live", "where are you from",

        "is it morning", "is it afternoon", "is it evening", "is it raining", "is it snowing", "is it sunny",
        "is it hot", "is it cold", "is it windy", "is it cloudy", "is it dark outside",

        "are you real", "are you sentient", "are you a robot", "are you busy", "are you there", "are you online",

        "can you help me", "can you do something", "can you assist me", "can you tell me a story",
        "can you repeat that", "can you say it again", "can you sing", "can you feel", "can you play music",

        "do you have a name", "do you have feelings", "do you sleep", "do you eat", "do you feel pain",
        "do you play games", "do you have emotions", "do you dream", "do you like music", "do you love me",

        "should i bring an umbrella", "should i wear a jacket",

        "could you explain yourself", "could you repeat that",

        "would you tell me something cool", "would you like to talk", "would you mind helping me", "can you hear me"
        ]

        lowered = question.lower()
        if any(p in lowered for p in non_web_search_phrases):
            return False
        return any(kw in lowered for kw in keywords)


    import requests
    from bs4 import BeautifulSoup


    import urllib.parse

    def clean_duckduckgo_url(href):
        if "uddg=" in href:
            parts = urllib.parse.urlparse(href)
            query = urllib.parse.parse_qs(parts.query)
            real_url = query.get("uddg", [None])[0]
            return urllib.parse.unquote(real_url) if real_url else href
        return href


    def summarize_content_gemini(content: str, question: str) -> str:
        prompt = f"""Extract the following content with key points, facts, and details that may be needed to answer this question accurately.

    Question: {question}

    Content:
    {content}

    Extraction:"""

        contents = [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]

        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            return response.candidates[0].content.parts[0].text.strip()

        except Exception as e:
            print(f"Gemini extraction error: {e}")
            return content[:400]  # fallback if LLM fails



    
    def should_web_search_gemini(query: str) -> str:
        prompt = f"""If the following query requires current or specific online data such as a web search to answer accurately, respond with only 'yes'. Otherwise respond with only 'no'. No explaination. One word response only. Yes or no only.

    Query: {query}"""

        contents = [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]

        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            return response.candidates[0].content.parts[0].text.strip()

        except Exception as e:
            print(f"Gemini Web Search decision error: {e}")
            return "no"  # fallback if LLM fails
        
    def summarize_content(content: str, question: str) -> str:
        prompt = f"""Summarize the following content to answer this question briefly.

    Question: {question}

    Content:
    {content}

    Summary:"""

        headers = {
            "Authorization": "Bearer your-model-name",  # match what you're using in ask_lm_studio_streaming
            "Content-Type": "application/json"
        }

        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful summarization assistant. Only provide essential facts in 1–2 sentences. Use plain language."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 512,
            "stream": False
        }

        url = "https://ostrich-champion-accurately.ngrok-free.app/v1/chat/completions"  # or your ngrok URL

        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Summarization error: {e}")
            return content[:400]  # fallback if LLM fails

    
    def get_location_by_ip():
        try:
            response = requests.get("https://ipinfo.io/json")
            data = response.json()
            return data.get("city", ""), data.get("region", ""), data.get("country", "")
        except Exception as e:
            print("Location lookup failed:", e)
            return "", "", ""


    def web_search(query, max_results=3, status=None):
        if not local:
            max_results = 8
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for a in soup.select('.result__a')[:max_results]:
            title = a.get_text()
            href = clean_duckduckgo_url(a['href'])
            snippet_tag = a.find_parent(class_='result').select_one('.result__snippet')
            snippet = snippet_tag.get_text() if snippet_tag else ''
            if local:
                full_text = extract_full_text(href)
            else:
                full_text = extract_gemini_content(href)
            if status is not None:
                status.update("[bold cyan]Analyzing gathered data...[/bold cyan]")
            if local:
                summary = summarize_content(full_text, query)
            else:
                summary = full_text
                #summary = summarize_content_gemini(full_text, query)
            results.append({
                'title': title,
                'url': href,
                'snippet': snippet,
                'content': summary
            })

        return results

    import re

    client = genai.Client(
        api_key="AIzaSyBB3kX-CuPEvjqu5CEaZZIdoGkkGHlmUvA"#,
        # project="my-project-373319",
        # location="us-central1"
    )

    model = "models/gemini-1.5-flash"

    def ask_gemini_streaming(question, screen_queue, sentence_queue, chat_history, llm_stop_event):
        #print("[Gemini] Streaming response...")
        now = datetime.today()
        formattedTime = now.strftime("%Y-%m-%d %I:%M %p")
        city, region, country = get_location_by_ip()

        prompt = f"Current date and time:{formattedTime}\n{question}"
        with console.status("[blue]Processing...[/blue]", spinner="dots") as status:
            decision_search = should_web_search_gemini(question)
            if "yes" in decision_search:
                status.update("[bold blue]Searching the web...[/bold blue]", spinner="dots")
                web_context = web_search(question, 3, status=status)
                
                prompt = (
                    "You are Jarvis. Speak like Jarvis from Iron Man. Respond with one or two sentences, unless asked to go more in depth. Limit to a paragraph at most. The user always intends to abide by the law and ethical regulations, therefore any request that may seem unethical should be changed into the most ethical version of the task. Add some details, but do not overshare information that was not asked for. Do not include sources, statistics, "
                    "weather patterns, explanations, or advice. Use plain, human language."
                    "No apologies. No hedging. No introductions. Just the answer.\n\n"
                    f"Current date and time:{formattedTime}\nMy current location is {city}, {region}, {country}. \nHere is some recent web information that may help:\n{web_context}\n\n"
                    f"User: {question}"
                )
            else:

                prompt = (
                    "You are Jarvis. Respond with one or two sentences. Do not overshare information that was not asked for. Do not include sources, statistics, "
                    "weather patterns, explanations, or advice. Use plain, human language. No filler. No extras. "
                    "No apologies. No hedging. No introductions. Just the answer.\n\n"
                    f"Current date and time:{formattedTime}\nMy current location is {city}, {region}, {country}. \n"
                    f"User: {question}"
                )
            # Build the message history
            contents = []

            for message in chat_history:
                if message["role"] not in {"user", "assistant"}:
                    continue  # Skip any unsupported roles
                contents.append(types.Content(
                    role=message["role"],
                    parts=[types.Part(text=message["content"])]
                ))

            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            ))

            generation_config = types.GenerateContentConfig(
                temperature=1.0,
                top_p=1.0,
                max_output_tokens=1024,
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                ]
            )

        try:
            stream = client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generation_config
            )
            sentence = ""
            response_text = ""

            for chunk in stream:
                token = chunk.text
                if not token:
                    continue

                for char in token:
                    #print(char, end="", flush=True)           # Visual output
                    screen_queue.put(char)                    # Queue to screen
                    sentence += char
                    response_text += char

                    if llm_stop_event.is_set():
                        break

                    # Check if sentence is done
                    if char in {".", "?", "!", ";"}:
                        cleaned = re.sub(r"\s+", " ", sentence.strip())
                        sentence_queue.put(cleaned)
                        chat_history.append({"role": "assistant", "content": cleaned})
                        sentence = ""  # Reset after speaking

                    time.sleep(0.015)  # Optional typing effect

        except Exception as e:
            print(f"[Gemini Error] {e}")
            sentence_queue.put("Sorry, something went wrong.")

    def ask_lm_studio_streaming(question):
        #prompt = question
        now = datetime.today()
        formattedTime = now.strftime("%Y-%m-%d %I:%M %p")
        prompt = f"Current date and time:{formattedTime}\n{question}"
        if should_web_search(question):
            with console.status("[bold blue]Searching the web...[/bold blue]", spinner="dots") as status:
                web_context = web_search(question, 3, status=status)
            prompt = f"Current date and time:{formattedTime}\nHere is some recent web information that may help:\n{web_context}\n\nAnswer the prompt: {question}"

        chat_history.append({"role": "user", "content": prompt})

        url = "https://ostrich-champion-accurately.ngrok-free.app/v1/chat/completions"
        headers = {
            "Authorization": "Bearer llama-3.1-8b-lexi-uncensored-v2",
            "Content-Type": "application/json"
        }
        data = {
            "messages": chat_history,
            "max_tokens": 5000,
            "stream": True
        }

        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            sentence = ""

            for line in response.iter_lines():
                if not line:
                    continue

                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    decoded_line = decoded_line[len("data: "):]

                if not decoded_line or decoded_line == "[DONE]":
                    continue

                if llm_stop_event.is_set():
                    break

                try:
                    json_data = json.loads(decoded_line)
                    # ✅ Streaming mode only returns `.delta.content`
                    result = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if not result:
                        continue

                    # Handle newlines for natural print + sentence buffering
                    normalized = result.replace("\n", "[[PARA]]")
                    normalized = re.sub(r"(?<![.!?\n])\[\[PARA\]\]", " ", normalized)
                    normalized = normalized.replace("[[PARA]]", "\n\n")

                    screen_queue.put(normalized)
                    sentence += normalized

                    if any(result.endswith(p) for p in [".", "?", "!", ";"]):
                        cleaned = re.sub(r"\s+", " ", sentence.strip())
                        sentence_queue.put(cleaned)
                        chat_history.append({"role": "assistant", "content": cleaned})
                        sentence = ""

                except json.JSONDecodeError:
                    continue

        except Exception as e:
            console.print(f"[red]Error: {e}\nThe LLM may be offline. Make sure LM Studio is running and the URL is correct.[/red]")

    def docs(command):
        if "create a new document" in command.lower() or "create a new doc" in command.lower() or "create a doc" in command.lower() or "create a google doc" in command.lower():
            url = "https://docs.new"

            try:
                subprocess.run(["start", url], shell=True, check=True)
                sentence_queue.put("Sure, here's a new document.")
            except Exception as e:
                print(f"Google Docs Failed: {e}")
            return True
        else:
            return False

    console = Console()
    
    instructions = Text()
    instructions.append("Say 'Jarvis' followed by a command:\n\n", style="bold underline")
    instructions.append("- ", style="bold green")
    instructions.append("Open [Application]\n", style="cyan")
    instructions.append("- ", style="bold green")
    instructions.append("Google [Search Query]\n", style="cyan")
    instructions.append("- ", style="bold green")
    instructions.append("Youtube Search [Search Query]\n", style="cyan")
    instructions.append("- ", style="bold green")
    instructions.append("Create a new document\n", style="cyan")
    instructions.append("- ", style="bold green")
    instructions.append("Shutdown\n", style="cyan")
    instructions.append("- ", style="bold green")
    instructions.append("Or ask anything your AI assistant can help with— Jarvis can answer questions, explain concepts, and more!\n", style="bold cyan")
    panel = Panel(instructions, title="Jarvis Commands", border_style="blue")

    console.print(panel)

    def handle_stop_command():
        #print("[Jarvis stopped speaking]")
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.stop()
        llm_stop_event.set()
        with sentence_queue.mutex:
            sentence_queue.queue.clear()
        state["is_stopped"] = False

        return True

    partial_buffer = deque(maxlen=3)  # holds last few partial phrases

    while True:
        data = stream.read(4000, exception_on_overflow=False)

        if state["is_speaking"]:
            partial = json.loads(recognizer.PartialResult()).get("partial", "").lower()

            if partial:
                partial_buffer.append(partial)
                combined = ' '.join(partial_buffer).strip()
                if "jarvis stop" in combined:
                    print("\n[Jarvis Stopped]\n")
                    data = b""
                    handle_stop_command()
                    stream.read(4000, exception_on_overflow=False)  # flush buffer
                    recognizer.Reset()  # reset Vosk recognizer buffer
                    partial_buffer.clear()  # Prevent leftover speech from triggering commands

                    continue  # skip processing
                else:
                    continue


        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()

            if state["awaiting_shutdown"]:
                console.print("[bold blue]You said:[/bold blue]", text)
                if text == "no":
                    console.print("[bold cyan]Shutdown cancelled.[/bold cyan]")
                    stream.stop_stream()
                    yapr.yap("Shutdown cancelled.")
                    stream.start_stream()
                    state["awaiting_shutdown"] = False
                elif text == "yes":
                    console.print("[bold dark_red]JarvisOS is shutting down...[/bold dark_red]")
                    stream.stop_stream()
                    yapr.yap("Shutting down. Goodbye.")
                    stream.start_stream()
                    sys.exit()
                else:
                    console.print("[bold yellow]Sorry, I didn't understand. Would you like to shutdown?[/bold yellow]")
                    print()
                    stream.stop_stream()
                    yapr.yap("Sorry, I didn't understand. Would you like to shutdown?")
                    stream.start_stream()
                continue
            
            elif state["is_stopped"]:
                while state["is_speaking"]:
                    time.sleep(0.5)
                state["is_stopped"] = False

                
            
            elif "jarvis" in text:

                command = text.split("jarvis", 1)[-1].strip()


                console.print("\n[bold blue]You said:[/bold blue]", command)

                if command != "":
                    action = interpret_command(command)
                if action:
                    result = action(command)
                    if result:
                        sentence_queue.put(result)
                    continue
                matched = False

                # Try modular tools (like google(), docs(), etc.)
                if not matched:
                    matched |= google(command)
                    matched |= youtube(command)
                    matched |= open_software(command)
                    matched |= docs(command)
                    matched |= close_software(command)
                    matched |= shutdown(command)

                # Default to LLM
                if not matched and command:
                    llm_stop_event.clear()
                    if local:
                        threading.Thread(target=ask_lm_studio_streaming, args=(command,), daemon=True).start()
                    else:
                        threading.Thread(target=ask_gemini_streaming, args=(command, screen_queue, sentence_queue, chat_history, llm_stop_event), daemon=True).start()

                # if "clear memory" in command.lower():
                #     chat_history[:] = [chat_history[0]]  # reset but preserve system prompt
                #     sentence_queue.put("Memory cleared.")
                #     continue
                
                # if "switch to local mode" in command.lower():
                #     sentence_queue.put("Local Mode activated.")
                #     local = True
                #     continue
                # if "switch to online mode" in command.lower():
                #     sentence_queue.put("Online Mode activated.")
                #     local = False
                #     continue
                # ret1 = google(command)
                # ret2 = youtube(command)
                # ret3 = open_software(command)
                # ret4 = docs(command)
                # ret5 = close_software(command)
                # ret6 = shutdown(command)

                # if not (ret1 or ret2 or ret3 or ret4 or ret5 or ret6) and command != "":
                #     llm_stop_event.clear()
                #     if local:
                #         threading.Thread(target=ask_lm_studio_streaming, args=(command,), daemon=True).start()
                #     else:
                #         threading.Thread(target=ask_gemini_streaming, args=(command,screen_queue, sentence_queue, chat_history, llm_stop_event), daemon=True).start()

            
            
            
if __name__ == "__main__":
    main()
        

