# Jarvis OS

**Jarvis OS** is a voice assistant designed to streamline and automate anything from your daily tasks to hardcore developing and everything in between. It integrates offline speech recognition, AI-powered natural language responses, and system-level command execution. Additional customization can be done by using LM studio alongside Jarvis on your own machine. Jarvis can also be used as a voice-powered CLI, accesing, organizing, and manipulating files as well as running simple bash commands. 

## Features

- Offline speech recognition with [Vosk](https://alphacephei.com/vosk/)
- Natural voice synthesis using [Yapper TTS](https://github.com/n1teshy/yapper-tts)
- Streaming from Local or Online LLM models
    - Default: Gemini 1.5 Flash
    - Local Default: Llama 3.2 1B parameters [Run LM Studio server and change URL for LLM calls in main.py to customize or change model] 
- Implemented RAG system for queries that may require or benefit from web searches
- Terminal-based interface with dynamic boot and loading screens
- Executes system commands: open applications, perform searches, file management, shut down, and more

## Example commands:

"Jarvis open vscode"

"Jarvis google how to bake sourdough"

"Jarvis shutdown"

"Jarvis explain quantum entanglement"

"Jarvis delete the read me file"

## Reccomended before Install

It is best to run inside a python virtual enviornment:

```bash
python -m venv jarvis-env
```
Windows:
```bash
jarvis-env\Scripts\activate
```
POSIX (Max/Linux):
```bash
source jarvis-env/bin/activate
```
-- )


## Installation

```bash
pip install jarvis-os
```

## Configuration
Python version 3.8 or higher is required

Ensure microphone input is enabled on your system

To use an AI backend (like LM Studio), modify the API endpoint in main.py

## Additional Notes
This package was initially built for Windows software. Support for POSIX is in progress (so some features work and others may not).

## License
This project is licensed under the Apache License 2.0.

## Author
Arvin Adeli

