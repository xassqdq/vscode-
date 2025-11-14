"""
素数生成器 - 修复副本

说明：这是清理并修复缩进后的单一版本。请用此文件替代原文件或作为参考。
"""

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import math
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

PRIME_DB_JSON = "primes_db.json"
PRIME_DB_ND = "primes_db.ndjson"
MR_BASES_64 = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]
CHUNK_SIZE = 5000


def miller_rabin(n, bases=MR_BASES_64):
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    def check(a, s, d, n):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                return True
        return False

    for a in bases:
        if a % n == 0:
            continue
        if not check(a, s, d, n):
            return False
    return True


def sieve_of_eratosthenes(limit):
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(math.isqrt(limit)) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start: limit + 1: step] = b"\x00" * ((limit - start) // step + 1)
    return [i for i, isprime in enumerate(sieve) if isprime]


def segmented_sieve_generator(start, end, segment_size=32768):
    if end < 2 or start > end:
        return
    if start < 2:
        start = 2
    limit = int(math.isqrt(end)) + 1
    small_primes = sieve_of_eratosthenes(limit)
    low = start
    while low <= end:
        high = min(low + segment_size - 1, end)
        seg_len = high - low + 1
        segment = bytearray(b"\x01") * seg_len
        for p in small_primes:
            if p * p > high:
                break
            start_idx = max(p * p, ((low + p - 1) // p) * p)
            for multiple in range(start_idx, high + 1, p):
                segment[multiple - low] = 0
        for i in range(seg_len):
            if segment[i]:
                yield low + i
        low += segment_size


def is_prime(n):
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False
    return miller_rabin(n)


def prime_factors(n):
    factors = []
    if n <= 1:
        return factors
    for p in (2, 3, 5):
        while n % p == 0:
            factors.append(p)
            n //= p
    f = 7
    step = 4
    while f * f <= n:
        while n % f == 0:
            factors.append(f)
            n //= f
        f += step
        step = 6 - step
    if n > 1:
        factors.append(n)
    return factors


def save_primes_ndappend(primes_iterable, filename=PRIME_DB_ND):
    with open(filename, "a", encoding="utf-8") as f:
        for p in primes_iterable:
            f.write(f"{p}\n")


def save_primes_json(primes_list, filename=PRIME_DB_JSON):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(primes_list, f, ensure_ascii=False)


def load_prime_db(json_file=PRIME_DB_JSON, nd_file=PRIME_DB_ND):
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    if os.path.exists(nd_file):
        primes = []
        try:
            with open(nd_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        primes.append(int(line))
                    except:
                        continue
        except Exception:
            return []
        return primes
    return []


def count_primes_in_ranges(start, end, interval):
    ranges = []
    counts = []
    if start < 2:
        start = 2
    current = start
    while current < end:
        nxt = min(current + interval - 1, end)
        cnt = 0
        for p in segmented_sieve_generator(current, nxt, segment_size=max(32768, interval)):
            cnt += 1
        ranges.append(f"{current}-{nxt}")
        counts.append(cnt)
        current = nxt + 1
    return ranges, counts


class PrimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("素数生成器")
        self.root.geometry("900x700")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.create_generate_page()
        self.create_check_page()
        self.create_db_page()
        self.create_plot_page()

    def create_generate_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="生成与保存")
        tk.Label(frame, text="起始值：").grid(row=0, column=0, sticky='e', padx=6, pady=6)
        self.start_var = tk.StringVar(value="1")
        tk.Entry(frame, textvariable=self.start_var, width=20).grid(row=0, column=1, padx=6, pady=6)
        tk.Label(frame, text="终止值：").grid(row=1, column=0, sticky='e', padx=6, pady=6)
        self.end_var = tk.StringVar(value="100000")
        tk.Entry(frame, textvariable=self.end_var, width=20).grid(row=1, column=1, padx=6, pady=6)
        tk.Label(frame, text="个位筛选（留空表示不筛）：").grid(row=2, column=0, sticky='e', padx=6, pady=6)
        self.digit_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.digit_var, width=20).grid(row=2, column=1, padx=6, pady=6)
        tk.Button(frame, text="开始生成", command=self.generate_action, bg="#4CAF50", fg="white").grid(row=3, column=0, columnspan=2, pady=8)
        self.gen_text = tk.Text(frame, height=14, width=90, font=("Courier", 9))
        self.gen_text.grid(row=4, column=0, columnspan=2, padx=6, pady=6)

    def generate_action(self):
        try:
            start = int(self.start_var.get().strip())
            end = int(self.end_var.get().strip())
            if start < 0 or end <= start:
                raise ValueError
        except Exception:
            messagebox.showerror("输入错误", "请输入合理的起始与终止值！")
            return
        target_digit = None
        d = self.digit_var.get().strip()
        if d != "":
            try:
                td = int(d)
                if 0 <= td <= 9:
                    target_digit = td
                else:
                    raise ValueError
            except Exception:
                messagebox.showerror("输入错误", "个位筛选请输入 0-9 或留空！")
                return
        range_size = end - start + 1
        if range_size <= 5_000_000:
            iterator = (p for p in sieve_of_eratosthenes(end) if p >= start)
        else:
            seg_size = 65536
            if range_size > 50_000_000:
                seg_size = 262144
            iterator = segmented_sieve_generator(start, end, segment_size=seg_size)
        progress = tk.Toplevel(self.root)
        progress.title("进度")
        tk.Label(progress, text=f"正在生成 {start} 到 {end} 的素数...").pack(padx=10, pady=6)
        pb = ttk.Progressbar(progress, orient='horizontal', length=400, mode='determinate')
        pb.pack(padx=10, pady=6)
        self.gen_text.delete(1.0, tk.END)
        primes_count = 0
        preview = []
        buffer = []
        last_update = time.time()
        processed = 0
        try:
            with open(PRIME_DB_ND, 'a', encoding='utf-8') as ndfile:
                for p in iterator:
                    processed += 1
                    if target_digit is not None and p % 10 != target_digit:
                        continue
                    primes_count += 1
                    if len(preview) < 200:
                        preview.append(p)
                    buffer.append(p)
                    if len(buffer) >= CHUNK_SIZE:
                        for v in buffer:
                            ndfile.write(f"{v}\n")
                        buffer.clear()
                    if range_size > 0 and (time.time() - last_update) > 0.2:
                        pb['value'] = min(100, processed / range_size * 100)
                        progress.update()
                        last_update = time.time()
                if buffer:
                    for v in buffer:
                        ndfile.write(f"{v}\n")
                    buffer.clear()
            pb['value'] = 100
            progress.update()
        except Exception as e:
            messagebox.showerror("错误", f"生成过程中出错: {e}")
        finally:
            try:
                progress.destroy()
            except Exception:
                pass
        self.gen_text.insert(tk.END, f"共找到 {primes_count} 个素数（已追加到 {PRIME_DB_ND}）：\n")
        self.gen_text.insert(tk.END, ", ".join(map(str, preview)) + ("..." if primes_count > len(preview) else ""))
        messagebox.showinfo("完成", f"已生成并保存 {primes_count} 个素数（分块追加）！")

    def create_check_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="素数判断")
        tk.Label(frame, text="输入数字：").pack(pady=10)
        self.check_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.check_var, width=30).pack()
        tk.Button(frame, text="判断", command=self.check_action, bg="#2196F3", fg="white").pack(pady=10)
        self.check_text = tk.Text(frame, height=14, width=75, font=("Courier", 9))
        self.check_text.pack(padx=10, pady=5)

    def check_action(self):
        try:
            n = int(self.check_var.get().strip())
            if n < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("错误", "请输入有效的非负整数！")
            return
        self.check_text.delete(1.0, tk.END)
        if is_prime(n):
            self.check_text.insert(tk.END, f"{n} 是素数。\n")
            save_primes_ndappend([n])
        else:
            factors = prime_factors(n)
            self.check_text.insert(tk.END, f"{n} 不是素数。\n")
            self.check_text.insert(tk.END, f"质因数分解：{' × '.join(map(str, factors))} = {n}\n")
            self.check_text.insert(tk.END, f"质因数列表：{factors}")

    def create_db_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="素数库")
        tk.Button(frame, text="加载素数库", command=self.load_db, bg="#9C27B0", fg="white").pack(pady=10)
        tk.Button(frame, text="清空素数库", command=self.clear_db, bg="#f44336", fg="white").pack(pady=5)
        self.db_text = tk.Text(frame, height=16, width=75, font=("Courier", 9))
        self.db_text.pack(padx=10, pady=5)

    def load_db(self):
        primes = load_prime_db()
        self.db_text.delete(1.0, tk.END)
        if primes:
            self.db_text.insert(tk.END, f"素数库共 {len(primes)} 个素数：\n")
            for i in range(0, len(primes), 20):
                self.db_text.insert(tk.END, ", ".join(map(str, primes[i:i+20])) + "\n")
        else:
            self.db_text.insert(tk.END, "素数库为空。")

    def clear_db(self):
        if os.path.exists(PRIME_DB_JSON):
            try:
                os.remove(PRIME_DB_JSON)
            except Exception:
                pass
        if os.path.exists(PRIME_DB_ND):
            try:
                os.remove(PRIME_DB_ND)
            except Exception:
                pass
        self.db_text.delete(1.0, tk.END)
        self.db_text.insert(tk.END, "素数库已清空。")
        messagebox.showinfo("提示", "素数库已清空！")

    def create_plot_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="分布图")
        tk.Label(frame, text="起始值：").grid(row=0, column=0, sticky='e', padx=10, pady=5)
        self.plot_start_var = tk.StringVar(value="1")
        tk.Entry(frame, textvariable=self.plot_start_var, width=25).grid(row=0, column=1, padx=10, pady=5)
        tk.Label(frame, text="终止值：").grid(row=1, column=0, sticky='e', padx=10, pady=5)
        self.plot_end_var = tk.StringVar(value="1000")
        tk.Entry(frame, textvariable=self.plot_end_var, width=25).grid(row=1, column=1, padx=10, pady=5)
        tk.Label(frame, text="区间大小：").grid(row=2, column=0, sticky='e', padx=10, pady=5)
        self.interval_var = tk.StringVar(value="100")
        tk.Entry(frame, textvariable=self.interval_var, width=25).grid(row=2, column=1, padx=10, pady=5)
        tk.Button(frame, text="生成分布图", command=self.plot_distribution, bg="#FF9800", fg="white").grid(row=3, column=0, columnspan=2, pady=10)
        self.fig_frame = tk.Frame(frame)
        self.fig_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    def plot_distribution(self):
        try:
            start = int(self.plot_start_var.get().strip())
            end = int(self.plot_end_var.get().strip())
            interval = int(self.interval_var.get().strip())
            if start < 0 or end <= start or interval <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("输入错误", "请输入合理的数值！")
            return
        for widget in self.fig_frame.winfo_children():
            widget.destroy()
        ranges, counts = count_primes_in_ranges(start, end, interval)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(ranges, counts, color='lightgreen')
        ax.set_title("素数区间分布")
        ax.set_xlabel("数值区间")
        ax.set_ylabel("素数个数")
        plt.setp(ax.get_xticklabels(), rotation=45)
        canvas = FigureCanvasTkAgg(fig, master=self.fig_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = PrimeApp(root)
    root.mainloop()
