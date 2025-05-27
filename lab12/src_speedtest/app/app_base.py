from tkinter import messagebox
import tkinter as tk


class AppBase(tk.Tk):
    def __init__(self, title):
        super().__init__()
        self.title(title)

        # Fix window size and center
        self.update_idletasks()
        w, h = 300, 180
        x, y = (self.winfo_screenwidth() - w) // 2, (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(False, False)

    def show_error(self, err_msg):
        messagebox.showerror("Error", err_msg)
