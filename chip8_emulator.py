
Author: Ahtasham
"""

import sys
import time
import pickle
import os
import random
import tkinter as tk
from collections import deque

# Configuration
SCALE = 12
WINDOW_W = 64
WINDOW_H = 32
FPS = 60
CPU_FREQ = 700  # approximate cycles per second

# Key mapping: tkinter keysym -> chip-8 hex key
KEY_MAP = {
    '1': 0x1,
    '2': 0x2,
    '3': 0x3,
    '4': 0xC,
    'q': 0x4,
    'w': 0x5,
    'e': 0x6,
    'r': 0xD,
    'a': 0x7,
    's': 0x8,
    'd': 0x9,
    'f': 0xE,
    'z': 0xA,
    'x': 0x0,
    'c': 0xB,
    'v': 0xF,
}

FONTSET = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]

class Chip8:
    def __init__(self):
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.gfx = [0] * (64 * 32)
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.key = [0] * 16
        self.draw_flag = False
        for i, b in enumerate(FONTSET):
            self.memory[0x50 + i] = b
        self.paused = False
        self.step_once = False
        self.disasm = False
        self.history = deque(maxlen=200)
        self.cycle_count = 0
        self.last_timer_update = time.time()

    def reset(self):
        # reinitialize but keep ROM loaded
        rom = self.memory[0x200:]
        self.__init__()
        for i, b in enumerate(rom):
            self.memory[0x200 + i] = b

    def load_rom(self, path):
        with open(path, 'rb') as f:
            rom = f.read()
        for i, b in enumerate(rom):
            self.memory[0x200 + i] = b
        print(f"Loaded ROM: {os.path.basename(path)} ({len(rom)} bytes)")

    def save_state(self, path='state.sav'):
        st = {
            'memory': self.memory,
            'V': self.V,
            'I': self.I,
            'pc': self.pc,
            'gfx': self.gfx,
            'stack': self.stack,
            'delay_timer': self.delay_timer,
            'sound_timer': self.sound_timer,
        }
        with open(path, 'wb') as f:
            pickle.dump(st, f)
        print(f"Saved state to {path}")

    def load_state(self, path='state.sav'):
        with open(path, 'rb') as f:
            st = pickle.load(f)
        self.memory = st['memory']
        self.V = st['V']
        self.I = st['I']
        self.pc = st['pc']
        self.gfx = st['gfx']
        self.stack = st['stack']
        self.delay_timer = st['delay_timer']
        self.sound_timer = st['sound_timer']
        self.draw_flag = True
        print(f"Loaded state from {path}")

    def push_history(self):
        st = pickle.dumps({
            'V': self.V, 'I': self.I, 'pc': self.pc, 'memory': self.memory, 'gfx': self.gfx, 'stack': self.stack,
            'delay_timer': self.delay_timer, 'sound_timer': self.sound_timer
        })
        self.history.append(st)

    def restore_history(self):
        if not self.history:
            print('No history to restore')
            return
        st = pickle.loads(self.history.pop())
        self.V = st['V']
        self.I = st['I']
        self.pc = st['pc']
        self.memory = st['memory']
        self.gfx = st['gfx']
        self.stack = st['stack']
        self.delay_timer = st['delay_timer']
        self.sound_timer = st['sound_timer']

    def cycle(self):
        if self.paused and not self.step_once:
            return
        # fetch
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        # push history occasionally
        if self.cycle_count % 10 == 0:
            self.push_history()
        self.cycle_count += 1
        # advance pc by default
        self.pc = (self.pc + 2) & 0xFFF
        self.execute_opcode(opcode)
        if self.step_once:
            self.step_once = False
            self.paused = True

    def execute_opcode(self, opcode):
        nnn = opcode & 0x0FFF
        n = opcode & 0x000F
        x = (opcode >> 8) & 0x000F
        y = (opcode >> 4) & 0x000F
        kk = opcode & 0x00FF

        if opcode == 0x00E0:  # CLS
            self.gfx = [0] * (64 * 32)
            self.draw_flag = True
        elif opcode == 0x00EE:  # RET
            if not self.stack:
                print('RET with empty stack')
                return
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000:  # JP addr
            self.pc = nnn
        elif opcode & 0xF000 == 0x2000:  # CALL addr
            self.stack.append(self.pc)
            self.pc = nnn
        elif opcode & 0xF000 == 0x3000:  # SE Vx, byte
            if self.V[x] == kk:
                self.pc = (self.pc + 2) & 0xFFF
        elif opcode & 0xF000 == 0x4000:  # SNE Vx, byte
            if self.V[x] != kk:
                self.pc = (self.pc + 2) & 0xFFF
        elif opcode & 0xF000 == 0x5000:  # SE Vx, Vy
            if self.V[x] == self.V[y]:
                self.pc = (self.pc + 2) & 0xFFF
        elif opcode & 0xF000 == 0x6000:  # LD Vx, byte
            self.V[x] = kk
        elif opcode & 0xF000 == 0x7000:  # ADD Vx, byte
            self.V[x] = (self.V[x] + kk) & 0xFF
        elif opcode & 0xF000 == 0x8000:
            if n == 0x0:
                self.V[x] = self.V[y]
            elif n == 0x1:
                self.V[x] |= self.V[y]
            elif n == 0x2:
                self.V[x] &= self.V[y]
            elif n == 0x3:
                self.V[x] ^= self.V[y]
            elif n == 0x4:
                s = self.V[x] + self.V[y]
                self.V[0xF] = 1 if s > 0xFF else 0
                self.V[x] = s & 0xFF
            elif n == 0x5:
                self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif n == 0x6:
                self.V[0xF] = self.V[x] & 1
                self.V[x] >>= 1
            elif n == 0x7:
                self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif n == 0xE:
                self.V[0xF] = (self.V[x] >> 7) & 1
                self.V[x] = (self.V[x] << 1) & 0xFF
            else:
                print(f"Unknown 0x8000 opcode: {hex(opcode)}")
        elif opcode & 0xF000 == 0x9000:  # SNE Vx, Vy
            if self.V[x] != self.V[y]:
                self.pc = (self.pc + 2) & 0xFFF
        elif opcode & 0xF000 == 0xA000:  # LD I, addr
            self.I = nnn
        elif opcode & 0xF000 == 0xB000:  # JP V0, addr
            self.pc = (nnn + self.V[0]) & 0xFFF
        elif opcode & 0xF000 == 0xC000:  # RND Vx, byte
            self.V[x] = random.randint(0, 255) & kk
        elif opcode & 0xF000 == 0xD000:  # DRW Vx, Vy, nibble
            vx = self.V[x] % 64
            vy = self.V[y] % 32
            height = n
            self.V[0xF] = 0
            for row in range(height):
                sprite = self.memory[self.I + row]
                for col in range(8):
                    if (sprite & (0x80 >> col)) != 0:
                        xcoord = (vx + col) % 64
                        ycoord = (vy + row) % 32
                        idx = xcoord + (ycoord * 64)
                        if self.gfx[idx] == 1:
                            self.V[0xF] = 1
                        self.gfx[idx] ^= 1
            self.draw_flag = True
        elif opcode & 0xF000 == 0xE000:
            if kk == 0x9E:  # SKP Vx
                if self.key[self.V[x]]:
                    self.pc = (self.pc + 2) & 0xFFF
            elif kk == 0xA1:  # SKNP Vx
                if not self.key[self.V[x]]:
                    self.pc = (self.pc + 2) & 0xFFF
            else:
                print(f"Unknown 0xE000 opcode: {hex(opcode)}")
        elif opcode & 0xF000 == 0xF000:
            if kk == 0x07:  # LD Vx, DT
                self.V[x] = self.delay_timer
            elif kk == 0x0A:  # LD Vx, K
                pressed = False
                for i in range(16):
                    if self.key[i]:
                        self.V[x] = i
                        pressed = True
                        break
                if not pressed:
                    self.pc = (self.pc - 2) & 0xFFF
            elif kk == 0x15:  # LD DT, Vx
                self.delay_timer = self.V[x]
            elif kk == 0x18:  # LD ST, Vx
                self.sound_timer = self.V[x]
            elif kk == 0x1E:  # ADD I, Vx
                self.I = (self.I + self.V[x]) & 0xFFF
            elif kk == 0x29:  # LD F, Vx
                self.I = 0x50 + (self.V[x] * 5)
            elif kk == 0x33:  # LD B, Vx
                val = self.V[x]
                self.memory[self.I] = val // 100
                self.memory[self.I + 1] = (val // 10) % 10
                self.memory[self.I + 2] = val % 10
            elif kk == 0x55:  # LD [I], Vx
                for i in range(x + 1):
                    self.memory[self.I + i] = self.V[i]
            elif kk == 0x65:  # LD Vx, [I]
                for i in range(x + 1):
                    self.V[i] = self.memory[self.I + i]
            else:
                print(f"Unknown 0xF000 opcode: {hex(opcode)}")
        else:
            print(f"Unknown opcode: {hex(opcode)}")

    def update_timers(self):
        now = time.time()
        # decrement timers at ~60Hz
        if now - self.last_timer_update >= 1.0 / 60.0:
            if self.delay_timer > 0:
                self.delay_timer -= 1
            if self.sound_timer > 0:
                self.sound_timer -= 1
            self.last_timer_update = now

    def disassemble_current(self, lines=16):
        out = []
        addr = max(0x200, self.pc - 2 * (lines // 2))
        for i in range(lines):
            if addr + 1 >= len(self.memory):
                break
            opcode = self.memory[addr] << 8 | self.memory[addr + 1]
            out.append((addr, opcode, self.simple_disasm(opcode)))
            addr += 2
        return out

    def simple_disasm(self, opcode):
        nnn = opcode & 0x0FFF
        n = opcode & 0x000F
        x = (opcode >> 8) & 0x000F
        y = (opcode >> 4) & 0x000F
        kk = opcode & 0x00FF
        if opcode == 0x00E0:
            return 'CLS'
        if opcode == 0x00EE:
            return 'RET'
        if opcode & 0xF000 == 0x1000:
            return f'JP {hex(nnn)}'
        if opcode & 0xF000 == 0x2000:
            return f'CALL {hex(nnn)}'
        if opcode & 0xF000 == 0x3000:
            return f'SE V{x}, {hex(kk)}'
        if opcode & 0xF000 == 0x6000:
            return f'LD V{x}, {hex(kk)}'
        if opcode & 0xF000 == 0xA000:
            return f'LD I, {hex(nnn)}'
        if opcode & 0xF000 == 0xD000:
            return f'DRW V{x}, V{y}, {n}'
        return hex(opcode)

class Chip8UI:
    def __init__(self, chip, rompath):
        self.chip = chip
        self.rompath = rompath
        self.root = tk.Tk()
        self.root.title('CHIP-8 Emulator (Tkinter)')
        self.canvas = tk.Canvas(self.root, width=WINDOW_W*SCALE, height=WINDOW_H*SCALE, bg='black')
        self.canvas.pack()
        self.info_label = tk.Label(self.root, text='')
        self.info_label.pack()
        # bind keys
        self.root.bind('<KeyPress>', self.on_key_down)
        self.root.bind('<KeyRelease>', self.on_key_up)
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.bind('<space>', lambda e: self.toggle_pause())
        self.root.bind('<s>', lambda e: self.step())
        self.root.bind('<F5>', lambda e: self.chip.save_state())
        self.root.bind('<F9>', lambda e: self.chip.load_state())
        self.root.bind('<d>', lambda e: self.toggle_disasm())
        self.root.bind('<r>', lambda e: self.reset())
        self.root.bind('<BackSpace>', lambda e: self.chip.restore_history())

        # schedule
        self.running = True
        self.last_time = time.time()
        self.cycles_per_tick = max(1, int(CPU_FREQ / FPS))
        # start main loop via tkinter after
        self.root.after(0, self.mainloop_tick)

    def on_key_down(self, event):
        k = getattr(event, 'keysym', None)
        if not k:
            return
        k = k.lower()
        if k in KEY_MAP:
            self.chip.key[KEY_MAP[k]] = 1
        # special keys handled via bindings

    def on_key_up(self, event):
        k = getattr(event, 'keysym', None)
        if not k:
            return
        k = k.lower()
        if k in KEY_MAP:
            self.chip.key[KEY_MAP[k]] = 0

    def toggle_pause(self):
        self.chip.paused = not self.chip.paused

    def step(self):
        if self.chip.paused:
            self.chip.step_once = True
            self.chip.paused = False
            # run one cycle synchronously
            self.chip.cycle()
            self.chip.update_timers()
            self.chip.paused = True
            self.update_display()

    def toggle_disasm(self):
        self.chip.disasm = not self.chip.disasm

    def reset(self):
        self.chip.reset()
        self.chip.load_rom(self.rompath)

    def update_display(self):
        self.canvas.delete('all')
        if self.chip.draw_flag:
            for y in range(WINDOW_H):
                for x in range(WINDOW_W):
                    if self.chip.gfx[x + y * WINDOW_W]:
                        self.canvas.create_rectangle(x*SCALE, y*SCALE, (x+1)*SCALE, (y+1)*SCALE, fill='white', outline='')
            self.chip.draw_flag = False
        # update info
        regs = ' '.join([f'V{i:X}:{self.chip.V[i]:02X}' for i in range(8)])
        regs2 = ' '.join([f'V{i+8:X}:{self.chip.V[i+8]:02X}' for i in range(8)])
        info = f'PC:{hex(self.chip.pc)} I:{hex(self.chip.I)} DT:{self.chip.delay_timer} ST:{self.chip.sound_timer} Paused:{self.chip.paused}'
        self.info_label.config(text=regs + '\n' + regs2 + '\n' + info)
        # disasm overlay
        if self.chip.disasm:
            lines = self.chip.disassemble_current(12)
            x0 = 10
            y0 = 10
            for i, (addr, opcode, text) in enumerate(lines):
                t = f'{hex(addr)}: {text}'
                # small text using canvas
                self.canvas.create_text(WINDOW_W*SCALE - 200, 10 + i*12, anchor='nw', fill='lightgray', text=t, font=('Courier', 10))

    def mainloop_tick(self):
        if not self.running:
            return
        # run cycles
        if not self.chip.paused:
            for _ in range(self.cycles_per_tick):
                self.chip.cycle()
        # update timers
        self.chip.update_timers()
        # draw if needed
        self.update_display()
        # schedule next tick
        self.root.after(int(1000 / FPS), self.mainloop_tick)

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
            
def main():
    if len(sys.argv) < 2:
        print('Usage: python chip8_emulator.py <romfile>')
        sys.exit(1)
    rompath = sys.argv[1]
    if not os.path.exists(rompath):
        print('ROM file not found:', rompath)
        sys.exit(1)
    chip = Chip8()
    chip.load_rom(rompath)
    ui = Chip8UI(chip, rompath)
    ui.run()

if __name__ == '__main__':
    main()


