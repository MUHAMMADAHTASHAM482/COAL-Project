# CHIP-8 Emulator (Python / Tkinter)

A complete **CHIP-8 emulator** written in **Python 3.11** using **Tkinter** for graphics and input.
This project was developed as part of a **COAL (Computer Organization & Assembly Language)** course to demonstrate low-level system concepts through a working virtual machine.

---

## Overview

CHIP-8 is a simple interpreted system with a small instruction set, making it ideal for understanding:

* Instruction fetch–decode–execute cycles
* Register-based architectures
* Stack-based subroutines
* Timers, memory, and input handling
* Bitwise opcode decoding

This emulator implements the full CHIP-8 instruction set and includes debugging utilities for educational use.

---

## Features

* Full CHIP-8 opcode implementation
* 4KB memory model
* 16 general-purpose 8-bit registers (V0–VF)
* Index register (I) and Program Counter (PC)
* Stack for subroutine calls
* Delay and sound timers (60Hz)
* 64×32 monochrome display
* Tkinter-based rendering
* Keyboard input mapped to CHIP-8 hex keypad
* ROM loading from command line
* Pause, step, reset execution
* Save / load emulator state
* Lightweight rewind (execution history)
* Disassembly overlay for debugging

---

## Tech Stack

* **Language:** Python 3.11
* **GUI:** Tkinter (standard library)
* **Dependencies:** None

---

## Installation

Ensure Python 3.11 or later is installed.

```bash
git clone https://github.com/your-username/chip8-emulator.git
cd chip8-emulator
```

---

## Usage

```bash
python chip8_emulator.py path/to/rom.ch8
```

Example:

```bash
python chip8_emulator.py roms/PONG.ch8
```

---

## Controls

### Emulator Controls

| Key       | Action                        |
| --------- | ----------------------------- |
| ESC       | Quit                          |
| Space     | Pause / Resume                |
| S         | Step one instruction (paused) |
| F5        | Save state                    |
| F9        | Load state                    |
| D         | Toggle disassembly            |
| R         | Reset emulator                |
| Backspace | Rewind execution              |

### CHIP-8 Keypad Mapping

```
CHIP-8        Keyboard
1 2 3 C   ->  1 2 3 4
4 5 6 D   ->  Q W E R
7 8 9 E   ->  A S D F
A 0 B F   ->  Z X C V
```

---

## Architecture Summary

### Memory Layout

* `0x000–0x1FF` : Reserved
* `0x050–0x09F` : Font set
* `0x200–0xFFF` : Program ROM

### Execution Model

1. Fetch opcode from memory
2. Decode using bit masking
3. Execute instruction
4. Update registers, memory, and timers
5. Render display if required

---

## Debugging Features

* Instruction-level stepping
* Live register inspection
* Disassembly overlay
* Save / restore emulator state
* Execution rewind

These tools make the emulator suitable for **learning and analysis**, not just gameplay.

---

## Limitations

* No audio output (sound timer only)
* Not cycle-accurate to original hardware
* Designed for educational purposes

---

## Course Relevance

This project directly applies **Computer Organization & Assembly Language** concepts by modeling a real instruction set architecture, showing how software emulates hardware-level behavior.

---

## Author

**Ahtasham**
Computer Science Student
