import socket
import struct
import threading
import tkinter as tk
from tkinter import ttk
from app.app_base import AppBase
from utils.const import HEADER_FMT, HEADER_SIZE, PAYLOAD_SIZE, UDP_SOCKET_TIMOUT
from utils.helpers import format_speed
from utils.types import Protocol


class Server(AppBase):
    def __init__(self, protocol: Protocol):
        super().__init__(f"Получатель {protocol.value.upper()}")
        self.protocol = protocol

        content_frame = ttk.Frame(self)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Labels + entries
        ttk.Label(content_frame, text="IP для приёма:", anchor="w").grid(
            row=0, column=0, pady=5, sticky="w"
        )
        self.ip_entry = ttk.Entry(content_frame)
        self.ip_entry.insert(0, "0.0.0.0")
        self.ip_entry.grid(row=0, column=1, padx=(8, 0), pady=5)

        ttk.Label(content_frame, text="Порт:", anchor="w").grid(
            row=1, column=0, pady=5, sticky="w"
        )
        self.port_entry = ttk.Entry(content_frame, width=20)
        self.port_entry.insert(0, "8080")
        self.port_entry.grid(row=1, column=1, padx=(8, 0), pady=5)

        self.status_var = tk.StringVar(value="Ожидание...")
        ttk.Label(
            content_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=2, column=0, columnspan=2, pady=5, sticky="w")

        # Start button
        self.start_btn = ttk.Button(
            content_frame, text="Запустить", command=self.on_start
        )
        self.start_btn.grid(
            row=3, column=0, columnspan=2, pady=(15, 0), ipadx=10, ipady=4
        )

    def on_start(self):
        try:
            ip = self.ip_entry.get()
            port = int(self.port_entry.get())
        except ValueError:
            return self.show_error("Неверные параметры подключения.")

        self.start_btn.config(state="disabled")
        threading.Thread(target=self.worker, args=(ip, port), daemon=True).start()

    def worker(self, ip, port):
        try:
            if self.protocol == Protocol.TCP:
                self.tcp_worker(ip, port)
            elif self.protocol == Protocol.UDP:
                self.udp_worker(ip, port)
            else:
                raise RuntimeError("Неизвестный протокол.")
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.start_btn.config(state="normal")

    def tcp_worker(self, ip, port):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind((ip, port))
        srv.listen(1)
        conn, _ = srv.accept()

        received_seq = set()
        total_bytes, expected_total = 0, None
        ts_start, ts_end = None, None

        # The main loop to receive data
        while True:
            hdr = conn.recv(HEADER_SIZE)
            if not hdr:
                break
            total_count, seq, ts, length = struct.unpack(HEADER_FMT, hdr)
            if expected_total is None:
                expected_total = total_count
            conn.recv(length)
            total_bytes += length
            received_seq.add(seq)
            if ts_start is None:
                ts_start = ts
            ts_end = ts
        conn.close()
        srv.close()

        self.display_stats(received_seq, ts_start, ts_end, total_bytes, expected_total)

    def udp_worker(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((ip, port))

        received_seq = set()
        total_bytes, expected_total = 0, None
        ts_start, ts_end = None, None

        # Receive until all packets are seen or timeout occurs
        sock.settimeout(UDP_SOCKET_TIMOUT)
        while True:
            try:
                data, _ = sock.recvfrom(HEADER_SIZE + PAYLOAD_SIZE)
            except socket.timeout:
                break

            hdr = data[:HEADER_SIZE]
            total_count, seq, ts, length = struct.unpack(HEADER_FMT, hdr)
            if expected_total is None:
                expected_total = total_count
            payload = data[HEADER_SIZE : HEADER_SIZE + length]
            total_bytes += len(payload)
            received_seq.add(seq)
            if ts_start is None:
                ts_start = ts
            ts_end = ts

            # If all packets are received, we can exit early
            if len(received_seq) >= expected_total:
                break
        sock.close()

        self.display_stats(received_seq, ts_start, ts_end, total_bytes, expected_total)

    def display_stats(
        self, received_seq, ts_start, ts_end, total_bytes, expected_total
    ):
        if len(received_seq) == 0:
            raise ValueError("Не получено ни одного пакета")
        if ts_end == ts_start:
            raise ValueError(
                "Пакеты получены, но с одинаковым временем отправки.\n"
                "Попробуйте увеличить количество отправляемых пакетов."
            )

        duration_ns = (ts_end - ts_start) if len(received_seq) > 1 else 1
        duration = duration_ns / 1e9
        speed = total_bytes / duration

        self.status_var.set(
            f"Скорость передачи: {format_speed(speed)}\n"
            f"Число полученных пакетов: {len(received_seq)}/{expected_total}"
        )
