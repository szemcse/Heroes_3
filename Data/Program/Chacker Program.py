import re
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import configparser
import os

# --- Segédfüggvények ---
placeholder_re = re.compile(r"%(?:\d+\$)?[+-]?(?:\d+)?(?:\.\d+)?[sdicuxXfFeEgGp%]")

def placeholders(s): return placeholder_re.findall(s)
def count_quotes(s): return s.count('"')
def extract_text_number(line):
    m = re.match(r'\s*Text\s+(\d+):', line)
    return int(m.group(1)) if m else None

# --- Nyelvi fájl betöltés ---
def load_languages(path="languages"):
    langs = {}
    if not os.path.exists(path):
        os.makedirs(path)
    for f in os.listdir(path):
        if f.lower().endswith((".ini", ".txt")):
            config = configparser.ConfigParser()
            config.read(os.path.join(path, f), encoding="utf-8")
            if "UI" in config:
                langs[os.path.splitext(f)[0]] = dict(config["UI"])
    return langs

# --- Ellenőrző logika ---
def check_files(eng_path, hun_path, eng_encoding, hun_encoding, report_path="translation_report.csv"):
    with open(eng_path, "r", encoding=eng_encoding, errors="replace") as f:
        eng_lines = f.readlines()
    with open(hun_path, "r", encoding=hun_encoding, errors="replace") as f:
        hun_lines = f.readlines()

    problems = []
    for i, (e, h) in enumerate(zip(eng_lines, hun_lines), start=1):
        if placeholders(e) != placeholders(h):
            problems.append({"line": i, "type": "placeholder_mismatch", "eng": e.strip(), "hun": h.strip()})
        if count_quotes(e) != count_quotes(h):
            problems.append({"line": i, "type": "quote_count_mismatch", "eng": e.strip(), "hun": h.strip()})
        if extract_text_number(e) != extract_text_number(h):
            problems.append({"line": i, "type": "text_number_mismatch", "eng": e.strip(), "hun": h.strip()})

    if problems:
        with open(report_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["line","type","eng","hun"])
            writer.writeheader()
            writer.writerows(problems)
        return problems, f"{len(problems)}"
    else:
        return [], None

# --- GUI ---
class CheckerApp:
    def __init__(self, root):
        self.root = root
        self.eng_file = None
        self.hun_file = None

        # Nyelvek betöltése
        self.langs = load_languages()
        if not self.langs:
            messagebox.showerror("Error", "Nincsenek nyelvi fájlok a 'languages' mappában!")
            root.destroy()
            return

        # Nyelvválasztó
        self.current_lang = tk.StringVar(value=list(self.langs.keys())[0])
        self.lang_select = ttk.Combobox(root, textvariable=self.current_lang, values=list(self.langs.keys()))
        self.lang_select.bind("<<ComboboxSelected>>", self.update_ui)
        self.lang_select.pack(pady=5)

        # Helyfoglaló UI elemek
        self.btn_source = tk.Button(root)
        self.btn_target = tk.Button(root)
        self.enc_source = ttk.Combobox(root, values=["utf-8","cp1250","cp1251","latin2"])
        self.enc_target = ttk.Combobox(root, values=["utf-8","cp1250","cp1251","latin2"])
        self.btn_check = tk.Button(root)
        self.output = scrolledtext.ScrolledText(root, width=100, height=25)

        # Elhelyezés
        self.btn_source.pack(pady=5)
        self.enc_source.pack(pady=2)
        self.btn_target.pack(pady=5)
        self.enc_target.pack(pady=2)
        self.btn_check.pack(pady=10)
        self.output.pack(padx=10, pady=10)

        self.update_ui()

    def update_ui(self, *args):
        ui = self.langs[self.current_lang.get()]
        self.root.title(ui.get("title","HotA Checker"))
        self.btn_source.config(text=ui.get("source_file","Select source"), command=self.load_eng)
        self.btn_target.config(text=ui.get("target_file","Select target"), command=self.load_hun)
        self.btn_check.config(text=ui.get("run_check","Run check"), command=self.run_check)

    def load_eng(self):
        self.eng_file = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if self.eng_file:
            self.output.insert(tk.END, f"{self.eng_file}\n")

    def load_hun(self):
        self.hun_file = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if self.hun_file:
            self.output.insert(tk.END, f"{self.hun_file}\n")

    def run_check(self):
        if not self.eng_file or not self.hun_file:
            messagebox.showerror("Error", "Válaszd ki mindkét fájlt!")
            return
        eng_enc = self.enc_source.get() or "utf-8"
        hun_enc = self.enc_target.get() or "utf-8"
        problems, n = check_files(self.eng_file, self.hun_file, eng_enc, hun_enc)
        ui = self.langs[self.current_lang.get()]
        if problems:
            msg = ui.get("errors_found","Found {n} errors.").format(n=n,file="translation_report.csv")
            self.output.insert(tk.END, msg + "\n")
        else:
            msg = ui.get("success","No mismatches.")
            self.output.insert(tk.END, msg + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = CheckerApp(root)
    root.mainloop()
