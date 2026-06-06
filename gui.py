"""
16-bit Processor Simulator — GUI Frontend
CE-222 COAL Project · FCSE · GIKI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processor import Processor
from assembler import Assembler, AssemblerError

# ─────────────────────────────────────────────────────────────
#  COLOUR PALETTE  —  Modern Dark IDE  (amber accent)
# ─────────────────────────────────────────────────────────────
BG_ROOT    = '#12121F'
BG_PANEL   = '#1A1A2E'
BG_WIDGET  = '#0F0F1C'
BG_EDITOR  = '#0D0D19'
BG_ALT     = '#161626'
BG_PC      = '#152A46'

FG_TEXT    = '#DCE4FF'
FG_DIM     = '#44476A'
FG_MID     = '#6870A0'
FG_BRIGHT  = '#FFFFFF'
FG_ACCENT  = '#82AAFF'
FG_AMBER   = '#FFD166'
FG_GREEN   = '#95E69E'
FG_RED     = '#FF6B8A'
FG_CYAN    = '#78D8F0'
FG_MAGENTA = '#C792EA'
FG_ORANGE  = '#FFA861'

BORDER     = '#232340'
BORDER_MID = '#2E2E58'
BORDER_HI  = '#464678'

FONT_CODE     = ('Courier New', 10)
FONT_GUTTER   = ('Courier New', 9)
FONT_SM       = ('Courier New', 8)
FONT_MD       = ('Courier New', 10, 'bold')
FONT_LG       = ('Courier New', 14, 'bold')
FONT_XL       = ('Courier New', 22, 'bold')
FONT_REG_NAME = ('Courier New', 9,  'bold')
FONT_REG_HEX  = ('Courier New', 15, 'bold')
FONT_REG_DEC  = ('Courier New', 8)
FONT_SECT     = ('Courier New', 8,  'bold')
FONT_BTN_LG   = ('Courier New', 10, 'bold')
FONT_TITLE    = ('Courier New', 13, 'bold')
FONT_SUB      = ('Courier New', 9)


# ─────────────────────────────────────────────────────────────
#  Pill Button  (Canvas-based rounded button)
# ─────────────────────────────────────────────────────────────
def _smooth_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class PillButton(tk.Canvas):
    def __init__(self, parent, text, command,
                 btn_bg, btn_hover, btn_fg=FG_BRIGHT,
                 w=114, h=32, radius=15, **kw):
        bg = kw.pop('bg', parent.cget('bg'))
        super().__init__(parent, width=w, height=h,
                         bd=0, highlightthickness=0,
                         cursor='hand2', bg=bg, **kw)
        self._text    = text
        self._cmd     = command
        self._col     = btn_bg
        self._hov     = btn_hover
        self._fg      = btn_fg
        self._r       = radius
        self._enabled = True
        self._hovered = False

        self.bind('<Configure>',  lambda e: self._draw())
        self.bind('<Button-1>',   self._on_click)
        self.bind('<Enter>',      lambda e: self._on_hover(True))
        self.bind('<Leave>',      lambda e: self._on_hover(False))

    def _on_hover(self, v):
        self._hovered = v
        self._draw()

    def _on_click(self, *_):
        if self._enabled:
            self._cmd()

    def _draw(self):
        self.delete('all')
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 4 or h < 4:
            return
        if not self._enabled:
            fill, fg = BORDER, FG_DIM
        elif self._hovered:
            fill, fg = self._hov, self._fg
        else:
            fill, fg = self._col, self._fg
        _smooth_rect(self, 1, 1, w-1, h-1, self._r, fill=fill, outline='')
        self.create_text(w // 2, h // 2, text=self._text,
                         fill=fg, font=FONT_BTN_LG)

    def set_state(self, enabled: bool):
        self._enabled = enabled
        self._hovered = False
        self.config(cursor='hand2' if enabled else 'arrow')
        self._draw()


# ─────────────────────────────────────────────────────────────
#  Register Row
# ─────────────────────────────────────────────────────────────
class RegRow(tk.Frame):
    def __init__(self, parent, name, bits=16, **kw):
        super().__init__(parent, bg=BG_PANEL, **kw)
        self._bits = bits
        self._prev = None

        # Name chip
        chip = tk.Frame(self, bg=BORDER_MID, padx=5, pady=2)
        chip.pack(side='left', padx=(8, 6), pady=4)
        tk.Label(chip, text=name, font=FONT_REG_NAME,
                 bg=BORDER_MID, fg=FG_MID,
                 width=4, anchor='w').pack()

        # Hex box
        hbox = tk.Frame(self, bg=BG_WIDGET,
                        highlightbackground=BORDER_MID, highlightthickness=1)
        hbox.pack(side='left', padx=(0, 8), pady=4)
        self._hex_var = tk.StringVar(value='0000' if bits == 16 else '00')
        self._hex_lbl = tk.Label(hbox, textvariable=self._hex_var,
                                  font=FONT_REG_HEX,
                                  bg=BG_WIDGET, fg=FG_AMBER,
                                  width=4 if bits == 16 else 2,
                                  anchor='center', padx=8, pady=2)
        self._hex_lbl.pack()

        # Decimal
        self._dec_var = tk.StringVar(value='      0')
        tk.Label(self, textvariable=self._dec_var,
                 font=FONT_REG_DEC, bg=BG_PANEL, fg=FG_MID,
                 width=7, anchor='e').pack(side='left')

    def update(self, val: int):
        mask = (1 << self._bits) - 1
        val &= mask
        self._hex_var.set(f'{val:02X}' if self._bits == 8 else f'{val:04X}')
        self._dec_var.set(f'{val:7d}')
        if self._prev is not None and self._prev != val:
            self._hex_lbl.config(fg=FG_GREEN)
            self.after(300, lambda: self._hex_lbl.config(fg=FG_AMBER))
        self._prev = val


# ─────────────────────────────────────────────────────────────
#  Main GUI
# ─────────────────────────────────────────────────────────────
class ProcessorGUI:

    DEFAULT_CODE = """        ORG  0          / Subtraction: DIF = MIN - SUB
        LDA  SUB        / Load subtrahend (3) into AC
        CMA             / Complement AC
        INC             / Negate: 2's complement
        ADD  MIN        / AC = MIN - SUB = 5 - 3 = 2
        STA  DIF        / Store result
        HLT
MIN,    DEC  5          / Minuend
SUB,    DEC  3          / Subtrahend
DIF,    HEX  0          / Result stored here
        END
"""

    EXAMPLES = {
        'Fibonacci Sequence':   'fibonacci',
        'Multiplication (MUL)': 'multiply',
        'Division (DIV)':       'divide',
        'Power (PWR)':          'power',
        'Addressing Modes':     'addressing_modes',
        'Mano Style (MIN-SUB)': 'mano_style',
    }

    _MRI = {'AND','OR','XOR','ADD','SUB','MUL','DIV','PWR',
            'LDA','STA','BUN','BSA','ISZ','MOD','CMP'}
    _RRI = {'CLA','CLE','CMA','CME','CIR','CIL','INC','HLT'}
    _IOR = {'INP','OUT','SKI','SKO','ION','IOF'}
    _DIRECTIVES = {'ORG', 'DAT', 'DEC', 'HEX', 'END'}

    def __init__(self, root: tk.Tk):
        self.root       = root
        self.cpu        = Processor()
        self.asm        = Assembler()
        self.running    = False
        self._thread    = None
        self._run_delay = 0.05
        self._prog      = []
        self._src_map   = []
        self._last_pc   = -1

        root.title('16-Bit Processor Simulator  —  CE-222 COAL  —  FCSE GIKI')
        root.geometry('1440x900')
        root.minsize(1200, 760)
        root.configure(bg=BG_ROOT)

        self._style()
        self._build()
        self._editor_insert(self.DEFAULT_CODE)
        self._refresh()

    # ─────────────────────────────────────────────
    def _style(self):
        s = ttk.Style()
        s.theme_use('default')
        s.configure('Mem.Treeview',
                    background=BG_WIDGET, foreground=FG_MID,
                    fieldbackground=BG_WIDGET,
                    font=('Courier New', 9),
                    rowheight=22, borderwidth=0, relief='flat')
        s.configure('Mem.Treeview.Heading',
                    background=BG_PANEL, foreground=FG_AMBER,
                    font=('Courier New', 9, 'bold'), relief='flat',
                    padding=(4, 5))
        s.map('Mem.Treeview',
              background=[('selected', BG_PC)],
              foreground=[('selected', FG_BRIGHT)])

    # ─────────────────────────────────────────────
    def _build(self):
        self._build_titlebar()
        self._build_bottombar()

        main = tk.Frame(self.root, bg=BG_ROOT)
        main.pack(fill='both', expand=True, padx=6, pady=(3, 3))

        left = tk.Frame(main, bg=BG_ROOT, width=340)
        left.pack(side='left', fill='both', padx=(0, 4))
        left.pack_propagate(False)

        ctr = tk.Frame(main, bg=BG_ROOT)
        ctr.pack(side='left', fill='both', expand=True, padx=4)

        right = tk.Frame(main, bg=BG_ROOT, width=330)
        right.pack(side='left', fill='both', padx=(4, 0))
        right.pack_propagate(False)

        self._build_left(left)
        self._build_centre(ctr)
        self._build_right(right)

    # ─────────────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=BG_PANEL, height=44)
        bar.pack(fill='x')
        bar.pack_propagate(False)
        tk.Frame(bar, bg=FG_AMBER, height=2).pack(side='bottom', fill='x')

        lf = tk.Frame(bar, bg=BG_PANEL)
        lf.pack(side='left', fill='y', padx=(14, 0))
        tk.Label(lf, text='16-BIT PROCESSOR SIMULATOR',
                 font=FONT_TITLE, bg=BG_PANEL, fg=FG_AMBER).pack(side='left', pady=4)
        tk.Label(lf, text='    CE-222 COAL  ·  FCSE, GIKI',
                 font=FONT_SUB, bg=BG_PANEL, fg=FG_MID).pack(side='left', pady=4)

        rf = tk.Frame(bar, bg=BG_PANEL)
        rf.pack(side='right', padx=16)

        self._halt_lbl = tk.Label(rf, text='',
                                   font=('Courier New', 9, 'bold'),
                                   bg=BG_PANEL, fg=FG_RED, width=9)
        self._halt_lbl.pack(side='right', padx=(8, 0))

        self._cycle_lbl = tk.Label(rf, text='CYCLES  000000',
                                    font=('Courier New', 9),
                                    bg=BG_PANEL, fg=FG_DIM)
        self._cycle_lbl.pack(side='right', padx=14)

        led_f = tk.Frame(rf, bg=BG_PANEL)
        led_f.pack(side='right')
        self._status_cv = tk.Canvas(led_f, width=14, height=14,
                                     bg=BG_PANEL, bd=0, highlightthickness=0)
        self._status_cv.pack(side='left', padx=(0, 5))
        self._status_lbl = tk.Label(led_f, text='IDLE',
                                     font=('Courier New', 9, 'bold'),
                                     bg=BG_PANEL, fg=FG_DIM, width=8)
        self._status_lbl.pack(side='left')
        self._draw_status(False)

    def _draw_status(self, on: bool):
        c = self._status_cv
        c.delete('all')
        if on:
            c.create_oval(1, 1, 13, 13, fill='#2A7A2A', outline='#3AA03A', width=1)
            c.create_oval(4, 4, 10, 10, fill=FG_GREEN, outline='')
        else:
            c.create_oval(1, 1, 13, 13, fill=BORDER, outline=BORDER_MID, width=1)
            c.create_oval(5, 5, 9,  9,  fill=FG_DIM,  outline='')

    # ─────────────────────────────────────────────
    def _build_left(self, parent):
        self._sect(parent, 'FILE')

        fs = tk.Frame(parent, bg=BG_PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        fs.pack(fill='x', padx=4, pady=(0, 4))

        r1 = tk.Frame(fs, bg=BG_PANEL)
        r1.pack(fill='x', padx=8, pady=(7, 3))
        self._mkbtn(r1, 'LOAD FILE',    self._do_load).pack(side='left', padx=2)
        self._mkbtn(r1, 'SAVE FILE',    self._do_save).pack(side='left', padx=2)
        self._mkbtn(r1, 'EXAMPLES',     self._do_examples).pack(side='left', padx=2)

        r2 = tk.Frame(fs, bg=BG_PANEL)
        r2.pack(fill='x', padx=8, pady=(0, 7))
        self._mkbtn(r2, 'CLEAR EDITOR', self._do_clear_editor,
                    fg=FG_RED).pack(side='left', padx=2)

        self._sect(parent, 'ASSEMBLY CODE EDITOR')

        ef = tk.Frame(parent, bg=BG_EDITOR,
                      highlightbackground=BORDER_MID, highlightthickness=1)
        ef.pack(fill='both', expand=True, padx=4)

        # Gutter
        gutter = tk.Frame(ef, bg=BG_PANEL, width=40)
        gutter.pack(side='left', fill='y')
        gutter.pack_propagate(False)
        tk.Frame(gutter, bg=BORDER_MID, width=1).pack(side='right', fill='y')
        self._ln = tk.Text(gutter, width=4, bg=BG_PANEL, fg=FG_DIM,
                           font=FONT_GUTTER, bd=0, relief='flat',
                           state='disabled', selectbackground=BG_PANEL,
                           cursor='arrow', padx=4)
        self._ln.pack(fill='both', expand=True)

        esb_v = tk.Scrollbar(ef, orient='vertical',
                              bg=BG_PANEL, troughcolor=BG_ROOT, width=8, bd=0, relief='flat')
        esb_v.pack(side='right', fill='y')
        esb_h = tk.Scrollbar(ef, orient='horizontal',
                              bg=BG_PANEL, troughcolor=BG_ROOT, width=8, bd=0, relief='flat')
        esb_h.pack(side='bottom', fill='x')

        self.editor = tk.Text(ef, bg=BG_EDITOR, fg=FG_TEXT,
                              font=FONT_CODE, bd=0, relief='flat',
                              insertbackground=FG_AMBER, insertwidth=2,
                              selectbackground=BG_PC, selectforeground=FG_BRIGHT,
                              yscrollcommand=esb_v.set, xscrollcommand=esb_h.set,
                              undo=True, wrap='none', tabs='2.5c',
                              spacing1=2, spacing3=2)
        self.editor.pack(fill='both', expand=True)
        esb_v.config(command=self._editor_yview_sync)
        esb_h.config(command=self.editor.xview)
        self.editor.bind('<KeyRelease>', self._on_key)
        self.editor.bind('<MouseWheel>', self._on_scroll)
        self._setup_tags()

        # Assemble button
        self._asm_btn = tk.Button(parent, text='▶▶   ASSEMBLE  &  LOAD',
                                   font=('Courier New', 11, 'bold'),
                                   bg='#173317', fg=FG_GREEN,
                                   activebackground='#214921',
                                   activeforeground=FG_BRIGHT,
                                   relief='flat', bd=0, pady=9,
                                   cursor='hand2', command=self._do_assemble)
        self._asm_btn.pack(fill='x', padx=4, pady=(6, 2))

        self._asm_status = tk.Label(parent,
                                     text='Load a program and press Assemble.',
                                     font=FONT_SM, bg=BG_ROOT, fg=FG_DIM,
                                     wraplength=320, justify='left', anchor='w')
        self._asm_status.pack(fill='x', padx=8, pady=(0, 4))

    # ─────────────────────────────────────────────
    def _build_centre(self, parent):
        self._sect(parent, 'MAIN MEMORY  —  1024 × 16-BIT WORDS')

        tb = tk.Frame(parent, bg=BG_PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        tb.pack(fill='x', padx=4)

        itb = tk.Frame(tb, bg=BG_PANEL)
        itb.pack(fill='x', padx=8, pady=5)

        tk.Label(itb, text='SHOW:', font=FONT_SM,
                 bg=BG_PANEL, fg=FG_DIM).pack(side='left', padx=(0, 4))
        self._show_all = tk.BooleanVar(value=False)
        tk.Checkbutton(itb, text='ALL WORDS', variable=self._show_all,
                       command=self._refresh_mem,
                       font=FONT_SM, bg=BG_PANEL, fg=FG_MID,
                       activebackground=BG_PANEL, selectcolor=BG_WIDGET,
                       cursor='hand2').pack(side='left', padx=2)

        self._mkbtn(itb, 'GOTO PC',   self._goto_pc,      sm=True).pack(side='left', padx=8)
        self._mkbtn(itb, 'CLEAR MEM', self._do_clear_mem, sm=True, fg=FG_RED).pack(side='right')

        tvf = tk.Frame(parent, bg=BG_ROOT)
        tvf.pack(fill='both', expand=True, padx=4, pady=(2, 0))

        vsb = tk.Scrollbar(tvf, orient='vertical',
                            bg=BG_PANEL, troughcolor=BG_ROOT, width=8, bd=0, relief='flat')
        vsb.pack(side='right', fill='y')

        cols = ('addr', 'hex', 'dec', 'disasm', 'src')
        self.tv = ttk.Treeview(tvf, columns=cols, show='headings',
                                style='Mem.Treeview', yscrollcommand=vsb.set,
                                selectmode='browse')
        self.tv.pack(fill='both', expand=True)
        vsb.config(command=self.tv.yview)

        hdrs = [
            ('ADDR',         58, 'center'),
            ('HEX',          60, 'center'),
            ('DECIMAL',      72, 'center'),
            ('DISASSEMBLY', 148, 'w'),
            ('SOURCE',        0, 'w'),
        ]
        for col, (h, w, a) in zip(cols, hdrs):
            self.tv.heading(col, text=h)
            self.tv.column(col, width=w, minwidth=max(w, 50),
                           anchor=a, stretch=(col == 'src'))

        self.tv.tag_configure('pc',    background=BG_PC,   foreground=FG_ACCENT)
        self.tv.tag_configure('pc_nz', background=BG_PC,   foreground=FG_BRIGHT)
        self.tv.tag_configure('nz',    foreground=FG_TEXT)
        self.tv.tag_configure('alt',   background=BG_ALT)
        self.tv.tag_configure('zero',  foreground=FG_DIM)

        self.tv.bind('<Double-1>', self._on_mem_dclick)
        self._pop_tree()

    # ─────────────────────────────────────────────
    def _build_right(self, parent):
        self._sect(parent, 'CPU REGISTERS')

        rf = tk.Frame(parent, bg=BG_PANEL,
                      highlightbackground=BORDER, highlightthickness=1)
        rf.pack(fill='x', padx=4, pady=(0, 4))

        hdr = tk.Frame(rf, bg=BG_PANEL)
        hdr.pack(fill='x', padx=8, pady=(6, 2))
        for txt, w in [('REG', 8), ('HEX', 10), ('DEC', 9)]:
            tk.Label(hdr, text=txt, font=('Courier New', 7, 'bold'),
                     bg=BG_PANEL, fg=FG_DIM, width=w, anchor='w').pack(side='left')

        tk.Frame(rf, bg=BORDER_MID, height=1).pack(fill='x', padx=8, pady=(0, 2))

        self.regs = {}
        for nm in ('PC', 'AR', 'IR', 'DR', 'AC'):
            r = RegRow(rf, nm)
            r.pack(fill='x', pady=1)
            self.regs[nm] = r

        tk.Frame(rf, bg=BORDER, height=1).pack(fill='x', padx=8, pady=4)

        for nm in ('INPR', 'OUTR'):
            r = RegRow(rf, nm, bits=8)
            r.pack(fill='x', pady=1)
            self.regs[nm] = r

        tk.Label(rf, text='', bg=BG_PANEL, height=1).pack()

        # Execution Log
        self._sect(parent, 'EXECUTION LOG')

        logf = tk.Frame(parent, bg=BG_ROOT)
        logf.pack(fill='both', expand=True, padx=4, pady=(0, 2))

        lsb = tk.Scrollbar(logf, orient='vertical',
                            bg=BG_PANEL, troughcolor=BG_ROOT, width=8, bd=0, relief='flat')
        lsb.pack(side='right', fill='y')

        self._log = tk.Text(logf, bg=BG_WIDGET, fg=FG_MID,
                            font=('Courier New', 9), bd=0, relief='flat',
                            state='disabled', yscrollcommand=lsb.set,
                            wrap='none', height=12,
                            highlightbackground=BORDER_MID, highlightthickness=1,
                            spacing1=1, spacing3=1)
        self._log.pack(fill='both', expand=True)
        lsb.config(command=self._log.yview)

        for tag, col in [('fetch', FG_DIM),    ('mri', FG_AMBER),
                          ('rri',  FG_CYAN),    ('io',  FG_MAGENTA),
                          ('ok',   FG_GREEN),   ('err', FG_RED),
                          ('halt', FG_RED),     ('info', FG_MID),
                          ('sep',  BORDER_MID)]:
            self._log.tag_configure(tag, foreground=col)

    # ─────────────────────────────────────────────
    def _build_bottombar(self):
        bar = tk.Frame(self.root, bg=BG_PANEL, height=58)
        bar.pack(fill='x', side='bottom')
        bar.pack_propagate(False)
        tk.Frame(bar, bg=FG_AMBER, height=2).pack(fill='x')
        tk.Frame(bar, bg=BORDER,   height=1).pack(fill='x')

        inner = tk.Frame(bar, bg=BG_PANEL)
        inner.pack(fill='both', expand=True, padx=10)

        ctrl = tk.Frame(inner, bg=BG_PANEL)
        ctrl.pack(side='left', pady=10)

        H = 34
        self._run_btn  = PillButton(ctrl, '▶  RUN',
                                     self._do_run,
                                     btn_bg='#1B421B', btn_hover='#255925',
                                     btn_fg=FG_GREEN,  w=114, h=H, bg=BG_PANEL)
        self._step_btn = PillButton(ctrl, '⏭  STEP',
                                     self._do_step,
                                     btn_bg='#3A2F0A', btn_hover='#503F10',
                                     btn_fg=FG_AMBER,  w=114, h=H, bg=BG_PANEL)
        self._stop_btn = PillButton(ctrl, '⏹  STOP',
                                     self._do_stop,
                                     btn_bg='#3A1010', btn_hover='#521A1A',
                                     btn_fg=FG_RED,    w=114, h=H, bg=BG_PANEL)
        self._rst_btn  = PillButton(ctrl, '↺  RESET',
                                     self._do_reset,
                                     btn_bg='#0F2340', btn_hover='#163150',
                                     btn_fg=FG_ACCENT, w=114, h=H, bg=BG_PANEL)
        self._stop_btn.set_state(False)

        for b in (self._run_btn, self._step_btn, self._stop_btn, self._rst_btn):
            b.pack(side='left', padx=4)

        # PC display
        pc_f = tk.Frame(inner, bg=BG_PANEL)
        pc_f.pack(side='right', padx=14)
        tk.Label(pc_f, text='PC', font=('Courier New', 9, 'bold'),
                 bg=BG_PANEL, fg=FG_DIM).pack(side='left', padx=(0, 8))
        self._pc_big = tk.Label(pc_f, text='0000', font=FONT_XL,
                                 bg=BG_PANEL, fg=FG_AMBER)
        self._pc_big.pack(side='left')

    # ═════════════════════════════════════════════
    #  Syntax Highlighting
    # ═════════════════════════════════════════════
    def _setup_tags(self):
        e = self.editor
        e.tag_configure('comment',   foreground='#525870')
        e.tag_configure('mri',       foreground=FG_AMBER)
        e.tag_configure('rri',       foreground=FG_CYAN)
        e.tag_configure('ior',       foreground=FG_MAGENTA)
        e.tag_configure('directive', foreground=FG_RED)
        e.tag_configure('label',     foreground=FG_GREEN)
        e.tag_configure('indirect',  foreground=FG_ORANGE)
        e.tag_configure('number',    foreground=FG_ACCENT)
        e.tag_configure('marker',    foreground=FG_ORANGE)

    def _highlight(self, *_):
        e = self.editor
        for t in ('comment','mri','rri','ior','directive','label',
                  'indirect','number','marker'):
            e.tag_remove(t, '1.0', 'end')

        for ln, line in enumerate(e.get('1.0', 'end').split('\n'), 1):
            for delim in (';', '/'):
                if delim in line:
                    ci = line.index(delim)
                    e.tag_add('comment', f'{ln}.{ci}', f'{ln}.end')
                    line = line[:ci]
                    break

            mm = re.match(r'^([A-Za-z_]\w*)\s*,', line)
            if mm:
                e.tag_add('label',  f'{ln}.0',           f'{ln}.{mm.end(1)}')
                e.tag_add('marker', f'{ln}.{mm.end(1)}', f'{ln}.{mm.end(1)+1}')

            for m in re.finditer(r'\b(ORG|DAT|DEC|HEX|END)\b', line, re.I):
                e.tag_add('directive', f'{ln}.{m.start()}', f'{ln}.{m.end()}')

            for m in re.finditer(r'(?<!\w)I(?!\w)', line):
                e.tag_add('indirect', f'{ln}.{m.start()}', f'{ln}.{m.end()}')

            for m in re.finditer(r'\b([A-Za-z]{2,4})\b', line):
                w = m.group(1).upper()
                if w in self._DIRECTIVES:
                    pass
                elif w in self._MRI:
                    e.tag_add('mri', f'{ln}.{m.start()}', f'{ln}.{m.end()}')
                elif w in self._RRI:
                    e.tag_add('rri', f'{ln}.{m.start()}', f'{ln}.{m.end()}')
                elif w in self._IOR:
                    e.tag_add('ior', f'{ln}.{m.start()}', f'{ln}.{m.end()}')

            for m in re.finditer(r'(0[xX][0-9A-Fa-f]+|\b\d+\b)', line):
                e.tag_add('number', f'{ln}.{m.start()}', f'{ln}.{m.end()}')

    def _update_gutter(self):
        n = self.editor.get('1.0', 'end-1c').count('\n') + 1
        self._ln.config(state='normal')
        self._ln.delete('1.0', 'end')
        self._ln.insert('1.0', '\n'.join(f'{i:3}' for i in range(1, n + 1)))
        self._ln.config(state='disabled')

    def _on_key(self, *_):
        self._highlight()
        self._update_gutter()

    def _editor_yview_sync(self, *args):
        self.editor.yview(*args)
        self._ln.yview(*args)

    def _on_scroll(self, event):
        delta = int(-1 * (event.delta / 120))
        self.editor.yview_scroll(delta, 'units')
        self._ln.yview_scroll(delta, 'units')

    def _editor_insert(self, text: str):
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', text)
        self._on_key()

    # ═════════════════════════════════════════════
    #  Memory Tree
    # ═════════════════════════════════════════════
    def _pop_tree(self):
        self.tv.delete(*self.tv.get_children())
        show_all = self._show_all.get()
        pc       = self.cpu.PC
        src_lk   = {addr: s for addr, s in self._src_map}

        for addr in range(Processor.MEMORY_SIZE):
            word    = self.cpu.memory[addr]
            has_src = addr in src_lk

            if not show_all and word == 0 and not has_src \
                    and addr not in (pc, pc-1, pc+1):
                if addr >= 64:
                    continue

            is_pc  = (addr == pc)
            is_nz  = (word != 0)
            is_alt = (addr % 2 == 1)

            if   is_pc and is_nz: tag = ('pc_nz',)
            elif is_pc:            tag = ('pc',)
            elif is_nz:            tag = ('nz',)
            elif is_alt:           tag = ('alt',)
            else:                  tag = ('zero',)

            arrow = '►' if is_pc else ' '
            src   = (src_lk.get(addr, '') or '')[:32]
            self.tv.insert('', 'end', iid=f'a{addr}',
                           values=(f'{arrow}{addr:03X}',
                                   f'{word:04X}',
                                   f'{word:5d}',
                                   self.asm.disassemble(word), src),
                           tags=tag)

    def _refresh_mem(self):
        self._pop_tree()

    def _goto_pc(self):
        iid = f'a{self.cpu.PC}'
        try:
            self.tv.see(iid)
            self.tv.selection_set(iid)
        except tk.TclError:
            pass

    def _update_pc_row(self):
        old, new = self._last_pc, self.cpu.PC

        if old >= 0:
            iid = f'a{old}'
            if self.tv.exists(iid):
                w  = self.cpu.memory[old]
                tg = ('nz',) if w else (('alt',) if old % 2 else ('zero',))
                vs = list(self.tv.item(iid, 'values'))
                vs[0] = f' {old:03X}'
                self.tv.item(iid, values=vs, tags=tg)

        iid = f'a{new}'
        if self.tv.exists(iid):
            w  = self.cpu.memory[new]
            tg = ('pc_nz',) if w else ('pc',)
            vs = list(self.tv.item(iid, 'values'))
            vs[0] = f'►{new:03X}'
            self.tv.item(iid, values=vs, tags=tg)
            try:
                self.tv.see(iid)
            except tk.TclError:
                pass
        else:
            self._pop_tree()
            self._goto_pc()

        self._last_pc = new

    def _on_mem_dclick(self, event):
        iid = self.tv.identify_row(event.y)
        if not iid:
            return
        addr_s = self.tv.item(iid, 'values')[0].strip().lstrip('►').strip()
        try:
            self._mem_edit_dialog(int(addr_s, 16))
        except ValueError:
            pass

    def _mem_edit_dialog(self, addr: int):
        cur = self.cpu.memory[addr]
        dlg = tk.Toplevel(self.root)
        dlg.title(f'Edit  M[0x{addr:03X}]')
        dlg.geometry('320x140')
        dlg.configure(bg=BG_ROOT)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text=f'Memory  0x{addr:03X}  ({addr})',
                 font=FONT_MD, bg=BG_ROOT, fg=FG_TEXT).pack(pady=(14, 6))

        var = tk.StringVar(value=f'0x{cur:04X}')
        ent = tk.Entry(dlg, textvariable=var, font=FONT_LG,
                       bg=BG_WIDGET, fg=FG_AMBER, insertbackground=FG_AMBER,
                       relief='flat', bd=2, width=10, justify='center')
        ent.pack(pady=4)
        ent.select_range(0, 'end')
        ent.focus()

        def apply():
            try:
                s = var.get().strip()
                v = int(s, 16) if s.lower().startswith('0x') else int(s, 0)
                self.cpu.memory[addr] = v & 0xFFFF
                dlg.destroy()
                self._refresh()
            except ValueError:
                ent.config(fg=FG_RED)

        br = tk.Frame(dlg, bg=BG_ROOT)
        br.pack(pady=8)
        self._mkbtn(br, 'APPLY',  apply).pack(side='left', padx=6)
        self._mkbtn(br, 'CANCEL', dlg.destroy, fg=FG_RED).pack(side='left', padx=6)
        ent.bind('<Return>', lambda *_: apply())

    # ═════════════════════════════════════════════
    #  Refresh
    # ═════════════════════════════════════════════
    def _refresh(self):
        self._refresh_regs()
        self._refresh_mem()
        self._goto_pc()
        self._update_cycle()
        self._update_halt()

    def _refresh_regs(self):
        s = self.cpu.get_state()
        for nm in ('PC','AR','IR','DR','AC','INPR','OUTR'):
            self.regs[nm].update(s[nm])
        self._pc_big.config(text=f'{s["PC"]:04X}')

    def _update_cycle(self):
        n = self.cpu.cycle_count
        self._cycle_lbl.config(text=f'CYCLES  {n:06d}',
                                fg=FG_TEXT if n > 0 else FG_DIM)

    def _update_halt(self):
        self._halt_lbl.config(text='● HALTED' if self.cpu.halted else '')

    # ═════════════════════════════════════════════
    #  Execution Log
    # ═════════════════════════════════════════════
    def _log_write(self, msg: str, tag: str = 'ok'):
        self._log.config(state='normal')
        self._log.insert('end', msg + '\n', tag)
        self._log.see('end')
        lines = int(self._log.index('end-1c').split('.')[0])
        if lines > 600:
            self._log.delete('1.0', f'{lines - 400}.0')
        self._log.config(state='disabled')

    def _log_sep(self):
        self._log_write('─' * 52, 'sep')

    def _classify_log(self, msg: str) -> str:
        if 'HLT' in msg or 'halted' in msg.lower():
            return 'halt'
        for m in self._MRI:
            if m in msg: return 'mri'
        for m in self._RRI:
            if m in msg: return 'rri'
        for m in self._IOR:
            if m in msg: return 'io'
        return 'ok'

    # ═════════════════════════════════════════════
    #  Actions
    # ═════════════════════════════════════════════
    def _do_assemble(self):
        src = self.editor.get('1.0', 'end-1c').strip()
        if not src:
            self._asm_status.config(text='No source code.', fg=FG_RED)
            return
        try:
            prog = self.asm.assemble(src)
        except AssemblerError as e:
            self._asm_status.config(text=f'Error: {str(e)[:80]}', fg=FG_RED)
            self._log_write(f'ASSEMBLE ERROR: {e}', 'err')
            return

        self._prog    = prog
        self._src_map = list(self.asm.source_map)
        self.cpu.reset()
        self.cpu.load_program(prog, 0)
        self._last_pc = -1

        self._asm_status.config(text=f'{len(prog)} words assembled — ready.', fg=FG_GREEN)
        self._log_sep()
        self._log_write(f'Assembled {len(prog)} words.  PC → 0x000', 'ok')
        self._refresh()
        self.root.after(50, self._goto_pc)

    def _do_run(self):
        if self.cpu.halted:
            messagebox.showinfo('Halted', 'CPU is halted.\nPress RESET to restart.')
            return
        if self.running:
            return
        self.running = True
        self._run_btn.set_state(False)
        self._step_btn.set_state(False)
        self._stop_btn.set_state(True)
        self._status_lbl.config(text='RUNNING', fg=FG_GREEN)
        self._draw_status(True)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        while self.running and not self.cpu.halted:
            self.cpu.step()
            self.root.after(0, self._on_step)
            if self._run_delay > 0:
                time.sleep(self._run_delay)
        self.root.after(0, self._on_run_done)

    def _on_step(self):
        if not self.root.winfo_exists():
            return
        self._refresh_regs()
        self._update_cycle()
        self._update_pc_row()
        if self.cpu.execution_log:
            msg = self.cpu.execution_log[-1]
            self._log_write(msg, self._classify_log(msg))

    def _on_run_done(self):
        self.running = False
        self._run_btn.set_state(True)
        self._step_btn.set_state(True)
        self._stop_btn.set_state(False)
        self._status_lbl.config(text='IDLE', fg=FG_DIM)
        self._draw_status(False)
        self._update_halt()
        if self.cpu.halted:
            self._log_write('CPU HALTED', 'halt')

    def _do_step(self):
        if self.cpu.halted:
            messagebox.showinfo('Halted', 'CPU is halted.\nPress RESET to restart.')
            return
        if self.running:
            return
        self.cpu.step()
        self._on_step()
        if self.cpu.halted:
            self._update_halt()
            self._log_write('CPU HALTED', 'halt')

    def _do_stop(self):
        self.running = False

    def _do_reset(self):
        self.running = False
        time.sleep(0.05)
        saved_mem = list(self.cpu.memory)
        self.cpu.reset()
        self.cpu.memory = saved_mem
        if self._prog:
            self.cpu.load_program(self._prog, 0)
        self._last_pc = -1
        self._run_btn.set_state(True)
        self._step_btn.set_state(True)
        self._stop_btn.set_state(False)
        self._status_lbl.config(text='IDLE', fg=FG_DIM)
        self._draw_status(False)
        self._halt_lbl.config(text='')
        self._log_sep()
        self._log_write('CPU RESET — registers cleared.', 'info')
        self._refresh()

    # ═════════════════════════════════════════════
    #  File Operations
    # ═════════════════════════════════════════════
    def _do_load(self):
        path = filedialog.askopenfilename(
            title='Open Assembly File',
            filetypes=[('Assembly', '*.asm'), ('Text', '*.txt'), ('All', '*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                self._editor_insert(f.read())
            self._asm_status.config(
                text=f'Loaded: {os.path.basename(path)}', fg=FG_GREEN)
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _do_save(self):
        path = filedialog.asksaveasfilename(
            title='Save Assembly File', defaultextension='.asm',
            filetypes=[('Assembly', '*.asm'), ('Text', '*.txt')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.editor.get('1.0', 'end-1c'))
            self._asm_status.config(
                text=f'Saved: {os.path.basename(path)}', fg=FG_GREEN)
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _do_clear_editor(self):
        if messagebox.askyesno('Clear Editor', 'Erase all code in the editor?'):
            self.editor.delete('1.0', 'end')
            self._on_key()

    def _do_clear_mem(self):
        if messagebox.askyesno('Clear Memory', 'Zero all 1024 memory words?'):
            self.cpu.memory = [0] * Processor.MEMORY_SIZE
            self._src_map   = []
            self._prog      = []
            self._refresh()
            self._log_write('Memory cleared.', 'info')

    def _do_examples(self):
        n_ex = len(self.EXAMPLES)
        dlg = tk.Toplevel(self.root)
        dlg.title('Example Programs')
        dlg.geometry(f'370x{80 + 48 * n_ex}')
        dlg.configure(bg=BG_ROOT)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        # Header strip
        hf = tk.Frame(dlg, bg=BG_PANEL)
        hf.pack(fill='x')
        tk.Frame(hf, bg=FG_AMBER, height=2).pack(fill='x')
        tk.Label(hf, text='SELECT AN EXAMPLE PROGRAM',
                 font=('Courier New', 10, 'bold'),
                 bg=BG_PANEL, fg=FG_AMBER, pady=10).pack()
        tk.Frame(hf, bg=BORDER_MID, height=1).pack(fill='x')

        bf = tk.Frame(dlg, bg=BG_ROOT)
        bf.pack(fill='both', expand=True, padx=14, pady=10)

        for name, fname in self.EXAMPLES.items():
            def make_cb(n=name, f=fname):
                def cb():
                    base = os.path.dirname(os.path.abspath(__file__))
                    path = os.path.join(base, 'examples', f + '.asm')
                    if not os.path.exists(path):
                        messagebox.showerror('Not Found', f'{f}.asm not found.')
                        return
                    with open(path, 'r', encoding='utf-8') as fp:
                        self._editor_insert(fp.read())
                    self._asm_status.config(text=f'Loaded: {n}', fg=FG_GREEN)
                    dlg.destroy()
                return cb

            row = tk.Frame(bf, bg=BG_PANEL,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill='x', pady=2)
            accent = tk.Frame(row, bg=FG_DIM, width=3)
            accent.pack(side='left', fill='y')
            btn = tk.Button(row, text=f'  {name}',
                            font=('Courier New', 9, 'bold'),
                            bg=BG_PANEL, fg=FG_TEXT,
                            activebackground=BORDER_MID,
                            activeforeground=FG_AMBER,
                            relief='flat', bd=0, padx=10, pady=9,
                            cursor='hand2', anchor='w', width=34,
                            command=make_cb())
            btn.pack(fill='x')

            def on_enter(e, a=accent, b=btn):
                a.config(bg=FG_AMBER)
                b.config(fg=FG_AMBER, bg=BORDER)
            def on_leave(e, a=accent, b=btn):
                a.config(bg=FG_DIM)
                b.config(fg=FG_TEXT, bg=BG_PANEL)
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
            row.bind('<Enter>', on_enter)
            row.bind('<Leave>', on_leave)

        tk.Frame(dlg, bg=BORDER_MID, height=1).pack(fill='x', padx=14)
        tk.Button(dlg, text='CLOSE', font=('Courier New', 8),
                  bg=BG_ROOT, fg=FG_DIM,
                  activebackground=BG_ROOT, activeforeground=FG_RED,
                  relief='flat', bd=0, padx=8, pady=6,
                  cursor='hand2', command=dlg.destroy).pack(pady=8)

    # ═════════════════════════════════════════════
    #  Widget Helpers
    # ═════════════════════════════════════════════
    def _sect(self, parent, title: str):
        f = tk.Frame(parent, bg=BG_ROOT)
        f.pack(fill='x', pady=(10, 3))
        tk.Frame(f, bg=FG_AMBER, width=3).pack(side='left', fill='y', padx=(6, 0))
        tk.Label(f, text=f'  {title}', font=FONT_SECT,
                 bg=BG_ROOT, fg=FG_MID, anchor='w').pack(side='left', padx=(2, 4))
        tk.Frame(f, bg=BORDER_MID, height=1).pack(
            side='left', fill='x', expand=True, padx=(0, 6))

    def _mkbtn(self, parent, text, cmd, sm=False, fg=FG_ACCENT):
        fs  = ('Courier New', 7, 'bold') if sm else ('Courier New', 8, 'bold')
        pad = (5, 2) if sm else (9, 4)
        return tk.Button(parent, text=text, font=fs,
                         bg=BORDER, fg=fg,
                         activebackground=BORDER_HI,
                         activeforeground=FG_BRIGHT,
                         relief='flat', bd=0,
                         padx=pad[0], pady=pad[1],
                         cursor='hand2', command=cmd)


# ─────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()

    try:
        root.update()
        import ctypes
        HWND = ctypes.windll.user32.GetParent(root.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            HWND, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass

    app = ProcessorGUI(root)

    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            app._editor_insert(f.read())
        app._asm_status.config(text=f'Loaded: {sys.argv[1]}', fg=FG_GREEN)

    root.mainloop()


if __name__ == '__main__':
    main()