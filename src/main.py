"""
Main Entry Point
Launches the Voice Command Calculator GUI.

Usage:
    python3 -m src.main
"""

import tkinter as tk
from src.gui import CalculatorApp


def main():
    root = tk.Tk()
    root.geometry("620x480")
    root.minsize(400, 350)
    app = CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
