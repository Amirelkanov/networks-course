import os
import socket
import threading
import time
from tkinter import ttk

from app.app_base import AppBase
from utils.const import PAYLOAD_SIZE
from utils.helpers import make_packet
from utils.types import Protocol


class Client(AppBase):
    def __init__(self, protocol: Protocol):
        super().__init__(f"Отправитель {protocol.value.upper()}")
        self.protocol = protocol

        content_frame = ttk.Frame(self)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Labels + entries
        ttk.Label(content_frame, text="IP адрес получателя:", anchor="w").grid(
            row=0, column=0, pady=5, sticky="w"
        )
        self.ip_entry = ttk.Entry(content_frame, width=20)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=0, column=1, padx=(8, 0), pady=5)

        ttk.Label(content_frame, text="Порт:", anchor="w").grid(
            row=1, column=0, pady=5, sticky="w"
        )
        self.port_entry = ttk.Entry(content_frame, width=20)
        self.port_entry.insert(0, "8080")
        self.port_entry.grid(row=1, column=1, padx=(8, 0), pady=5)

        ttk.Label(content_frame, text="Число пакетов:", anchor="w").grid(
            row=2, column=0, pady=5, sticky="w"
        )
        self.count_entry = ttk.Entry(content_frame, width=20)
        self.count_entry.insert(0, "100")
        self.count_entry.grid(row=2, column=1, padx=(8, 0), pady=5)

        # Send button
        self.send_btn = ttk.Button(
            content_frame, text="Отправить", command=self.on_send
        )
        self.send_btn.grid(
            row=3, column=0, columnspan=2, pady=(15, 0), ipadx=10, ipady=4
        )

    def on_send(self):
        try:
            ip = self.ip_entry.get()
            port = int(self.port_entry.get())
            count = int(self.count_entry.get())
        except ValueError:
            return self.show_error("Некорректные параметры подключения.")

        self.send_btn.config(state="disabled")
        threading.Thread(
            target=self.worker, args=(ip, port, count), daemon=True
        ).start()

    def worker(self, ip, port, total_count):
        try:
            if self.protocol == Protocol.TCP:
                self.tcp_worker(ip, port, total_count)
            elif self.protocol == Protocol.UDP:
                self.udp_worker(ip, port, total_count)
            else:
                raise RuntimeError("Неизвестный протокол.")
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.send_btn.config(state="normal")

    def tcp_worker(self, ip, port, total_count):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        total_bytes = 0
        for seq in range(total_count):
            payload = os.urandom(PAYLOAD_SIZE)
            ts = time.time()
            packet = make_packet(total_count, seq, ts, payload)
            sock.sendall(packet)
            total_bytes += len(payload)

        sock.close()

    def udp_worker(self, ip, port, total_count):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        total_bytes = 0
        for seq in range(total_count):
            payload = os.urandom(PAYLOAD_SIZE)
            ts = time.time()
            packet = make_packet(total_count, seq, ts, payload)
            sock.sendto(packet, (ip, port))
            total_bytes += len(payload)

        sock.close()
