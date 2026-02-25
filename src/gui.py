"""
GUI Module
Tkinter-based interface for the Voice Command Calculator.

Layout:
    +--------------------------------------------+
    |       Voice Command Calculator             |
    +--------------------------------------------+
    |   Result:  1081                            |
    +--------------------------------------------+
    |   Recognized: "twenty three times forty.." |
    |   Expression: 23 * 47                      |
    +--------------------------------------------+
    |   [ Listen ]            [ Clear History ]  |
    +--------------------------------------------+
    |   History:                                 |
    |   > "twenty three times forty seven" = 1081|
    +--------------------------------------------+

Critical threading note:
    Speech recognition blocks while waiting for audio. We run it in a
    background thread so the GUI stays responsive. All widget updates
    from the background thread go through root.after() because tkinter
    is NOT thread-safe.
"""

import tkinter as tk
from tkinter import scrolledtext
import threading

from src.speech_input import listen
from src.nlp_parser import parse
from src.evaluator import evaluate
from src.speech_output import speak, format_result


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Command Calculator")
        self.root.resizable(True, True)

        # ---- Result display ----
        result_frame = tk.Frame(root)
        result_frame.pack(pady=(20, 5), padx=20, fill=tk.X)

        self.result_var = tk.StringVar(value="Say a math problem...")
        self.result_label = tk.Label(
            result_frame,
            textvariable=self.result_var,
            font=("Arial", 28, "bold"),
            fg="#2e7d32",
            anchor="center",
        )
        self.result_label.pack(fill=tk.X)

        # ---- Detail display (recognized text + parsed expression) ----
        detail_frame = tk.Frame(root)
        detail_frame.pack(pady=(0, 10), padx=20, fill=tk.X)

        self.recognized_var = tk.StringVar(value="")
        self.recognized_label = tk.Label(
            detail_frame,
            textvariable=self.recognized_var,
            font=("Arial", 11),
            fg="#555555",
            anchor="w",
        )
        self.recognized_label.pack(fill=tk.X)

        self.expression_var = tk.StringVar(value="")
        self.expression_label = tk.Label(
            detail_frame,
            textvariable=self.expression_var,
            font=("Courier", 12),
            fg="#1565c0",
            anchor="w",
        )
        self.expression_label.pack(fill=tk.X)

        # ---- Buttons ----
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.listen_btn = tk.Button(
            btn_frame,
            text="Listen",
            font=("Arial", 13),
            width=12,
            bg="#4caf50",
            fg="white",
            activebackground="#388e3c",
            command=self.on_listen,
        )
        self.listen_btn.pack(side=tk.LEFT, padx=8)

        self.clear_btn = tk.Button(
            btn_frame,
            text="Clear History",
            font=("Arial", 11),
            width=12,
            command=self.clear_history,
        )
        self.clear_btn.pack(side=tk.LEFT, padx=8)

        # ---- History log ----
        history_label = tk.Label(root, text="History:", font=("Arial", 11), anchor="w")
        history_label.pack(padx=20, anchor="w")

        self.history = scrolledtext.ScrolledText(
            root,
            height=10,
            width=60,
            font=("Courier", 10),
            state=tk.DISABLED,
            bg="#fafafa",
        )
        self.history.pack(pady=(2, 15), padx=20, fill=tk.BOTH, expand=True)

        # ---- Status bar ----
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            root,
            textvariable=self.status_var,
            font=("Arial", 9),
            fg="#888888",
            anchor="w",
            relief=tk.SUNKEN,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- Actions ----

    def on_listen(self):
        """Start listening in a background thread to keep GUI responsive."""
        self.result_var.set("Listening...")
        self.recognized_var.set("")
        self.expression_var.set("")
        self.status_var.set("Calibrating microphone...")
        self.listen_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._process_voice, daemon=True)
        thread.start()

    def _process_voice(self):
        """Background thread: listen → parse → evaluate → speak."""
        # 1. Listen
        self._set_status("Listening... speak now")
        text = listen(noise_duration=1.0)
        if text is None:
            self._show_error("Could not understand. Try again.")
            return

        self._set_recognized(f'Heard: "{text}"')

        # 2. Parse
        self._set_status("Parsing...")
        try:
            expression = parse(text)
        except Exception as e:
            self._show_error(f"Parse error: {e}")
            return

        self._set_expression(f"Expression: {expression}")

        # 3. Evaluate
        self._set_status("Evaluating...")
        try:
            result = evaluate(expression)
        except ZeroDivisionError:
            self._show_error("Cannot divide by zero.")
            self._add_history(f'"{text}" → {expression} → ERROR: division by zero')
            return
        except (ValueError, SyntaxError) as e:
            self._show_error(f"Cannot compute: {expression}")
            self._add_history(f'"{text}" → {expression} → ERROR: {e}')
            return

        # 4. Display result
        display = int(result) if isinstance(result, float) and result == int(result) else result
        self._set_result(str(display))
        self._add_history(f'"{text}" → {expression} = {display}')
        self._set_status("Speaking result...")

        # 5. Speak result
        speak(format_result(result))
        self._set_status("Ready")

    # ---- Thread-safe GUI updates (all go through root.after) ----

    def _set_result(self, text):
        self.root.after(0, lambda: self.result_var.set(text))
        self.root.after(0, lambda: self.listen_btn.config(state=tk.NORMAL))

    def _set_recognized(self, text):
        self.root.after(0, lambda: self.recognized_var.set(text))

    def _set_expression(self, text):
        self.root.after(0, lambda: self.expression_var.set(text))

    def _set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def _show_error(self, message):
        self.root.after(0, lambda: self.result_var.set(message))
        self.root.after(0, lambda: self.listen_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.status_var.set("Ready"))

    def _add_history(self, entry):
        def update():
            self.history.config(state=tk.NORMAL)
            self.history.insert(tk.END, f"> {entry}\n")
            self.history.config(state=tk.DISABLED)
            self.history.see(tk.END)
        self.root.after(0, update)

    def clear_history(self):
        self.history.config(state=tk.NORMAL)
        self.history.delete("1.0", tk.END)
        self.history.config(state=tk.DISABLED)
