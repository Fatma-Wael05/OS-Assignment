"""
CSE 335s - Operating Systems
Memory Management - Segmentation (First-Fit & Best-Fit)
"""

import tkinter as tk
from tkinter import messagebox

# ── Colours ──────────────────────────────────────────────────
COLORS = ["#3b7dd8","#e05c5c","#4ecb71","#f0b83a","#9b59b6","#e67e22"]
FREE_C = "#2d6e4e"
OCC_C  = "#2a2e40"

# ── Global state ─────────────────────────────────────────────
total_mem  = 0
holes      = []   # list of [start, size]
allocated  = []   # list of {pid, segments:[{name,size,base}]}
pid_colors = {}
color_idx  = 0

def get_color(pid):
    global color_idx
    if pid not in pid_colors:
        pid_colors[pid] = COLORS[color_idx % len(COLORS)]
        color_idx += 1
    return pid_colors[pid]

def sort_holes():
    holes.sort(key=lambda h: h[0])

def merge_holes():
    sort_holes()
    merged = []
    for h in holes:
        if merged and merged[-1][0] + merged[-1][1] == h[0]:
            merged[-1][1] += h[1]
        else:
            merged.append(list(h))
    holes[:] = merged

def first_fit(size):
    sort_holes()
    for i, h in enumerate(holes):
        if h[1] >= size:
            return i
    return -1

def best_fit(size):
    best, best_w = -1, float("inf")
    for i, h in enumerate(holes):
        w = h[1] - size
        if 0 <= w < best_w:
            best, best_w = i, w
    return best

def place(idx, size):
    base = holes[idx][0]
    holes[idx][0] += size
    holes[idx][1] -= size
    if holes[idx][1] == 0:
        holes.pop(idx)
    return base

# ── Operations ───────────────────────────────────────────────
def do_init():
    global total_mem, color_idx
    try:
        total_mem = int(mem_var.get())
    except:
        messagebox.showerror("Error", "Invalid memory size"); return
    holes.clear(); allocated.clear(); pid_colors.clear()
    color_idx = 0
    for sv, zv in hole_rows:
        try:
            holes.append([int(sv.get()), int(zv.get())])
        except:
            messagebox.showerror("Error", "Invalid hole values"); return
    sort_holes()
    log(f"Initialized {total_mem}K with {len(holes)} hole(s)", "green")
    refresh()

def do_allocate():
    pid = pid_var.get().strip().upper()
    algo = algo_var.get()
    if not pid: return
    if any(p["pid"] == pid for p in allocated):
        log(f"{pid} already allocated", "red"); return
    segs = []
    for nv, sv in seg_rows:
        n, s = nv.get().strip(), sv.get().strip()
        if n and s:
            try: segs.append((n, int(s)))
            except: log("Invalid segment size","red"); return
    if not segs: return
    backup = [list(h) for h in holes]
    placed = []
    for name, size in segs:
        idx = first_fit(size) if algo == "First-Fit" else best_fit(size)
        if idx == -1:
            holes[:] = backup
            log(f"FAIL: {pid} - '{name}' ({size}K) doesn't fit", "red"); return
        base = place(idx, size)
        placed.append({"name": name, "size": size, "base": base})
        log(f"  {name} ({size}K) -> base={base}K", "cyan")
    get_color(pid)
    allocated.append({"pid": pid, "segments": placed})
    log(f"OK: {pid} allocated [{algo}]", "green")
    refresh()

def do_deallocate():
    pid = pid_var.get().strip().upper()
    for i, p in enumerate(allocated):
        if p["pid"] == pid:
            for s in p["segments"]:
                holes.append([s["base"], s["size"]])
            allocated.pop(i)
            merge_holes()
            log(f"OK: {pid} deallocated, holes merged", "yellow")
            refresh(); return
    log(f"Not found: {pid}", "red")

# ── Refresh GUI ──────────────────────────────────────────────
def refresh():
    draw_bar()
    update_tables()

def draw_bar():
    canvas.delete("all")
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 2 or not total_mem: return

    blocks = []
    for p in allocated:
        for s in p["segments"]:
            blocks.append((s["base"], s["size"], p["pid"]+"."+s["name"], get_color(p["pid"])))
    for hh in holes:
        blocks.append((hh[0], hh[1], "FREE", FREE_C))
    blocks.sort()

    full, cur = [], 0
    for start, size, label, color in blocks:
        if start > cur: full.append((cur, start-cur, "Occ", OCC_C))
        full.append((start, size, label, color))
        cur = start + size
    if cur < total_mem: full.append((cur, total_mem-cur, "Occ", OCC_C))

    x = 0
    for start, size, label, color in full:
        bw = max(1, round(size / total_mem * w))
        canvas.create_rectangle(x, 0, x+bw, h, fill=color, outline="#000", width=1)
        if bw > 24:
            canvas.create_text(x+bw//2, h//2, text=label[:max(1,bw//7)],
                               fill="white", font=("Courier", 8, "bold"))
        x += bw

def update_tables():
    holes_text.config(state="normal")
    holes_text.delete("1.0", "end")
    holes_text.insert("end", f"{'Hole':<6}{'Start':>8}{'End':>8}{'Size':>8}\n", "header")
    holes_text.insert("end", "-"*32+"\n", "header")
    for i, h in enumerate(holes, 1):
        holes_text.insert("end", f"H{i:<5}{h[0]:>8}{h[0]+h[1]:>8}{h[1]:>8}\n")
    holes_text.config(state="disabled")

    seg_text.config(state="normal")
    seg_text.delete("1.0", "end")
    for p in allocated:
        seg_text.insert("end", f"-- {p['pid']} --\n", "pid")
        seg_text.insert("end", f"{'#':<4}{'Name':<10}{'Base':>7}{'Limit':>7}\n", "header")
        for i, s in enumerate(p["segments"]):
            seg_text.insert("end", f"{i:<4}{s['name']:<10}{s['base']:>7}{s['size']:>7}\n")
        seg_text.insert("end", "\n")
    seg_text.config(state="disabled")

def log(msg, color="white"):
    log_text.config(state="normal")
    log_text.insert("end", msg+"\n", color)
    log_text.see("end")
    log_text.config(state="disabled")

# ── Build UI ─────────────────────────────────────────────────
root = tk.Tk()
root.title("Memory Management - CSE 335s")
root.configure(bg="#0f1117")
root.geometry("1000x680")

left = tk.Frame(root, bg="#1a1d27", width=290)
left.pack(side="left", fill="y", padx=(8,4), pady=8)
left.pack_propagate(False)

right = tk.Frame(root, bg="#0f1117")
right.pack(side="left", fill="both", expand=True, padx=(4,8), pady=8)

def lbl(p, t):
    tk.Label(p, text=t, bg="#1a1d27", fg="#6b7099", font=("Courier",9)).pack(anchor="w", pady=(5,1))

def small_entry(parent, var, w=7):
    return tk.Entry(parent, textvariable=var, width=w, bg="#12141e", fg="white",
                    insertbackground="white", font=("Courier",9), relief="flat", bd=3)

# Algorithm
lbl(left, "Algorithm:")
algo_var = tk.StringVar(value="First-Fit")
for a in ("First-Fit","Best-Fit"):
    tk.Radiobutton(left, text=a, variable=algo_var, value=a, bg="#1a1d27",
                   fg="white", selectcolor="#12141e", font=("Courier",9)).pack(anchor="w")

tk.Frame(left, bg="#2e3350", height=1).pack(fill="x", pady=6)

# Memory size
lbl(left, "Total memory (K):")
mem_var = tk.StringVar(value="1000")
tk.Entry(left, textvariable=mem_var, bg="#12141e", fg="white", insertbackground="white",
         font=("Courier",9), relief="flat", bd=3).pack(fill="x")

# Holes
lbl(left, "Holes  [Start K]  [Size K]:")
hole_frame = tk.Frame(left, bg="#1a1d27"); hole_frame.pack(fill="x")
hole_rows = []

def add_hole(s="", z=""):
    row = tk.Frame(hole_frame, bg="#1a1d27"); row.pack(fill="x", pady=1)
    sv, zv = tk.StringVar(value=str(s)), tk.StringVar(value=str(z))
    small_entry(row, sv).pack(side="left", padx=(0,3))
    small_entry(row, zv).pack(side="left", padx=(0,3))
    def rm():
        row.destroy()
        for i,(a,b) in enumerate(hole_rows):
            if a is sv: hole_rows.pop(i); break
    tk.Button(row, text="x", command=rm, bg="#1a1d27", fg="#e05c5c",
              relief="flat", font=("Courier",9)).pack(side="left")
    hole_rows.append((sv, zv))

add_hole(0,300); add_hole(400,250); add_hole(700,200)

bf0 = tk.Frame(left, bg="#1a1d27"); bf0.pack(fill="x", pady=(3,0))
tk.Button(bf0, text="+ Hole", command=add_hole, bg="#1a1d27", fg="#5aabf0",
          relief="flat", font=("Courier",9)).pack(side="left")
tk.Button(bf0, text="Initialize", command=do_init, bg="#1a3a2a", fg="#4ecb71",
          relief="flat", font=("Courier",9,"bold"), padx=8, pady=3).pack(side="right")

tk.Frame(left, bg="#2e3350", height=1).pack(fill="x", pady=6)

# Process ops
lbl(left, "Process ID:")
pid_var = tk.StringVar(value="P1")
tk.Entry(left, textvariable=pid_var, bg="#12141e", fg="white", insertbackground="white",
         font=("Courier",9), relief="flat", bd=3).pack(fill="x")

lbl(left, "Segments  [Name]  [Size K]:")
seg_frame = tk.Frame(left, bg="#1a1d27"); seg_frame.pack(fill="x")
seg_rows = []

def add_seg(n="", s=""):
    row = tk.Frame(seg_frame, bg="#1a1d27"); row.pack(fill="x", pady=1)
    nv, sv = tk.StringVar(value=str(n)), tk.StringVar(value=str(s))
    small_entry(row, nv).pack(side="left", padx=(0,3))
    small_entry(row, sv).pack(side="left", padx=(0,3))
    def rm():
        row.destroy()
        for i,(a,b) in enumerate(seg_rows):
            if a is nv: seg_rows.pop(i); break
    tk.Button(row, text="x", command=rm, bg="#1a1d27", fg="#e05c5c",
              relief="flat", font=("Courier",9)).pack(side="left")
    seg_rows.append((nv, sv))

add_seg("Code",100); add_seg("Data",120); add_seg("Stack",90)
tk.Button(left, text="+ Segment", command=add_seg, bg="#1a1d27", fg="#5aabf0",
          relief="flat", font=("Courier",9)).pack(anchor="w", pady=(3,0))

bf2 = tk.Frame(left, bg="#1a1d27"); bf2.pack(fill="x", pady=6)
tk.Button(bf2, text="Allocate", command=do_allocate, bg="#1a2a3a", fg="#5aabf0",
          relief="flat", font=("Courier",9,"bold"), pady=4).pack(side="left", fill="x", expand=True, padx=(0,2))
tk.Button(bf2, text="Deallocate", command=do_deallocate, bg="#3a1a1a", fg="#e05c5c",
          relief="flat", font=("Courier",9,"bold"), pady=4).pack(side="left", fill="x", expand=True)

# ── Right panel ──────────────────────────────────────────────
tk.Label(right, text="Memory Layout", bg="#0f1117", fg="#6b7099",
         font=("Courier",9,"bold")).pack(anchor="w")
canvas = tk.Canvas(right, bg="#12141e", height=55, highlightthickness=1,
                   highlightbackground="#2e3350")
canvas.pack(fill="x", pady=(2,8))
canvas.bind("<Configure>", lambda e: draw_bar())

tables = tk.Frame(right, bg="#0f1117"); tables.pack(fill="both", expand=True)

hf = tk.Frame(tables, bg="#0f1117"); hf.pack(side="left", fill="both", expand=True, padx=(0,4))
tk.Label(hf, text="Free Partitions (Holes)", bg="#0f1117", fg="#6b7099",
         font=("Courier",9,"bold")).pack(anchor="w")
holes_text = tk.Text(hf, bg="#12141e", fg="white", font=("Courier",10),
                     state="disabled", relief="flat", bd=0)
holes_text.pack(fill="both", expand=True)
holes_text.tag_config("header", foreground="#6b7099")

sf = tk.Frame(tables, bg="#0f1117"); sf.pack(side="left", fill="both", expand=True, padx=(4,0))
tk.Label(sf, text="Segment Tables", bg="#0f1117", fg="#6b7099",
         font=("Courier",9,"bold")).pack(anchor="w")
seg_text = tk.Text(sf, bg="#12141e", fg="white", font=("Courier",10),
                   state="disabled", relief="flat", bd=0)
seg_text.pack(fill="both", expand=True)
seg_text.tag_config("header", foreground="#6b7099")
seg_text.tag_config("pid", foreground="#5aabf0", font=("Courier",10,"bold"))

tk.Label(right, text="Log", bg="#0f1117", fg="#6b7099",
         font=("Courier",9,"bold")).pack(anchor="w", pady=(8,0))
log_text = tk.Text(right, bg="#12141e", fg="white", font=("Courier",9),
                   height=7, state="disabled", relief="flat", bd=0)
log_text.pack(fill="x")
for c,fc in [("green","#4ecb71"),("red","#e05c5c"),("cyan","#5aabf0"),("yellow","#f0b83a"),("white","white")]:
    log_text.tag_config(c, foreground=fc)

log("Ready - Initialize memory to start.", "white")
root.mainloop()
