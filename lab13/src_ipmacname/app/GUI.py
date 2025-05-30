import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from utils.network import get_default_interface, scan_network


class NetworkScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Find all computers in network")
        self.geometry("650x400")

        self.local_ip = None

        # Frame for button and progress bar
        frame_top = ttk.Frame(self)
        frame_top.pack(pady=10, padx=5, fill="x")

        # Button
        self.btn_start = ttk.Button(
            frame_top, text="Начать поиск", command=self.on_start, width=20
        )
        self.btn_start.pack(side="left", padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            frame_top, orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(side="left", padx=5, expand=True, fill="x")

        # Result table
        cols = ("ip", "mac", "name")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("ip", text="IP Address")
        self.tree.heading("mac", text="MAC Address")
        self.tree.heading("name", text="Host name")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

    def on_start(self):
        self.btn_start.config(state="disabled")
        for i in self.tree.get_children():
            self.tree.delete(i)

        self.tree.insert(
            "", "end", values=("Текущий ПК", "", ""), iid="local_pc", open=True
        )
        self.tree.insert("", "end", values=("Сеть", "", ""), iid="network", open=True)

        try:
            local_ip, netmask = get_default_interface()
            self.local_ip = local_ip
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.btn_start.config(state="normal")
            return

        threading.Thread(
            target=scan_network,
            args=(local_ip, netmask, self.update_progress, self.add_result),
            daemon=True,
        ).start()

    def update_progress(self, done, total):
        self._update_progress_ui(done, total)

    def add_result(self, ip, mac, name):
        self.tree.insert(
            "local_pc" if self.local_ip == ip else "network",
            "end",
            values=(ip, mac, name),
        )

    def _update_progress_ui(self, done, total):
        self.progress["maximum"] = total
        self.progress["value"] = done
        if done >= total:
            self.btn_start.config(state="normal")
