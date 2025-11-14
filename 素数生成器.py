"""
素数生成器 — 简洁合并版

功能：
- 区间内生成素数（埃氏筛 + 分段筛生成器）
- 素数判断（小范围试除 + Miller-Rabin）
- 质因数分解（朴素试除实现）
- 持久化：JSON（小规模）与 NDJSON（逐行追加）
- 简单 GUI（Tkinter + matplotlib 嵌入）
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

# Miller-Rabin 在 64-bit 下的确定性基
MR_BASES_64 = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]

# 默认写入块大小
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
            sieve[start: limit + 1: step] = b"\x00" * (((limit - start) // step) + 1)
    return [i for i, v in enumerate(sieve) if v]


def segmented_sieve_generator(start, end, segment_size=32768):
    if end < 2 or start > end:
        return
    limit = int(math.isqrt(end)) + 1
    base_primes = sieve_of_eratosthenes(limit)
    low = max(start, 2)
    while low <= end:
        high = min(low + segment_size - 1, end)
        segment = bytearray(b"\x01") * (high - low + 1)
        for p in base_primes:
            if p * p > high:
                break
            start_idx = max(p * p, ((low + p - 1) // p) * p)
            for j in range(start_idx, high + 1, p):
                segment[j - low] = 0
        for i, val in enumerate(segment, start=low):
            if val:
                yield i
        low += segment_size


def is_prime(n):
    if n < 2:
        return False
    if n <= 1000000:
        if n % 2 == 0:
            return n == 2
        r = int(math.isqrt(n))
        for d in range(3, r + 1, 2):
            if n % d == 0:
                return False
        return True
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


def count_primes_in_ranges(start, end, interval, segment_size=65536):
    labels = []
    counts = []
    low = start
    while low <= end:
        high = min(low + interval - 1, end)
        labels.append(f"{low}-{high}")
        counts.append(0)
        low += interval

    if end <= 1000000:
        primes = sieve_of_eratosthenes(end)
        for p in primes:
            if p < start:
                continue
            idx = (p - start) // interval
            if 0 <= idx < len(counts):
                counts[idx] += 1
    else:
        for p in segmented_sieve_generator(start, end, segment_size=segment_size):
            idx = (p - start) // interval
            if 0 <= idx < len(counts):
                counts[idx] += 1

    return labels, counts


def save_primes_ndappend(primes_iterable):
    if not primes_iterable:
        return
    with open(PRIME_DB_ND, 'a', encoding='utf-8') as f:
        for p in primes_iterable:
            f.write(f"{p}\n")


def save_primes_json(primes):
    try:
        primes_sorted = sorted(set(primes))
        with open(PRIME_DB_JSON, 'w', encoding='utf-8') as f:
            json.dump(primes_sorted, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("保存 JSON 失败:", e)


def load_prime_db():
    primes = set()
    if os.path.exists(PRIME_DB_JSON):
        try:
            with open(PRIME_DB_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    primes.update(data)
        except Exception:
            pass
    if os.path.exists(PRIME_DB_ND):
        try:
            with open(PRIME_DB_ND, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if s:
                        try:
                            primes.add(int(s))
                        except:
                            continue
        except Exception:
            pass
    return sorted(primes)


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
        try:
            if os.path.exists(PRIME_DB_JSON):
                os.remove(PRIME_DB_JSON)
        except Exception:
            pass
        try:
            if os.path.exists(PRIME_DB_ND):
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
"""
素数生成器 — 清洁合并版

说明：该文件为合并后的单一实现，包含素数生成（埃氏筛与分段筛）、素数判断、质因数分解、
持久化（JSON/NDJSON）与一个基于 Tkinter 的简单 GUI。
"""

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import math
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 文件存储
PRIME_DB_JSON = "primes_db.json"
PRIME_DB_ND = "primes_db.ndjson"

# Miller-Rabin 在 64-bit 下的确定性基
MR_BASES_64 = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]

# 默认分块写入大小
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
            sieve[start: limit + 1: step] = b"\x00" * (((limit - start) // step) + 1)
    return [i for i, v in enumerate(sieve) if v]


def segmented_sieve_generator(start, end, segment_size=32768):
    if end < 2 or start > end:
        return
    limit = int(math.isqrt(end)) + 1
    base_primes = sieve_of_eratosthenes(limit)
    low = max(start, 2)
    while low <= end:
        high = min(low + segment_size - 1, end)
        segment = bytearray(b"\x01") * (high - low + 1)
        for p in base_primes:
            if p * p > high:
                break
            start_idx = max(p * p, ((low + p - 1) // p) * p)
            for j in range(start_idx, high + 1, p):
                segment[j - low] = 0
        for i, val in enumerate(segment, start=low):
            if val:
                yield i
        low += segment_size



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
            except:
                pass
        if os.path.exists(PRIME_DB_ND):
            try:
                os.remove(PRIME_DB_ND)
            except:
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
        except:
            messagebox.showerror("输入错误", "请输入合理的数值！")
            return

        for widget in self.fig_frame.winfo_children():
            widget.destroy()

        ranges, counts = count_primes_in_ranges(start, end, interval)

        fig, ax = plt.subplots(figsize=(7, 5))
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
from tkinter import messagebox, ttk
import json
import os
import math
import random
import time
import itertools
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Database: for small sets use JSON, for large streaming use NDJSON append
PRIME_DB_JSON = "primes_db.json"
PRIME_DB_ND = "primes_db.ndjson"

"""
素数生成器（带 GUI）
功能：
- 区间内生成素数（支持分段筛生成器以节约内存）
- 位数/末位筛选（示例中为个位）
- 素数判断（Miller-Rabin + 小范围试除）
- 质因数分解（朴素试除法）
- 素数库持久化（JSON 与 NDJSON 两种模式）
- 素数分布可视化（matplotlib 嵌入 Tkinter）

文件已添加注释以便阅读与维护：每个函数的复杂度与适用场景都有说明。

注意：对于非常大范围（数百万/数千万以上），请优先使用“分段生成器”并分块保存结果，避免一次性在内存中构建巨大列表。
"""

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import math
import random
import time
import itertools
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------
# 常量与持久化文件
# ---------------------------
# 使用两种文件格式：
# - JSON（适合小规模数据，保存为列表）
# - NDJSON（换行分割的逐行整数，适合流式追加，节省内存）
PRIME_DB_JSON = "primes_db.json"
PRIME_DB_ND = "primes_db.ndjson"

# ---------------------------
# 算法区
# ---------------------------

# 64-bit 下确定性 Miller-Rabin 基（对 64 位整数可做确定性判定）
MR_BASES_64 = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]


def miller_rabin(n, bases=MR_BASES_64):
    """
    Miller-Rabin 素数判定（确定性版本在 64-bit 范围内使用指定 bases 可保证正确）。

    适用场景：对大于 1e6 的整数判定是否为素数时性能通常优于试除法。
    对非常大的整数（数百位），请注意随机性/轮数设置或使用专门的大数库。
    """
    if n < 2:
        return False
    # 先用小素数快速排除
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    # 写成 n-1 = d * 2^s
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
    """
    埃氏筛：一次性生成 0..limit 的素数列表。

    时间复杂度：O(n log log n)。
    空间复杂度：O(n)。

    适用场景：limit 在几百万以内（视内存），用于小区间生成最快。
    """
    if limit < 2:
        return []
    # 使用 bytearray 节约内存并且速度更快
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(math.isqrt(limit)) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start: limit + 1: step] = b"\x00" * (((limit - start) // step) + 1)
    return [i for i, v in enumerate(sieve) if v]


def segmented_sieve_generator(start, end, segment_size=32768):
    """
    分段筛的生成器版本：按段生成 [start, end] 范围内的素数，逐个 yield。

    优点：不会一次性占用大量内存，适合在 GUI 中逐步写入文件或实时展示。

    参数：
      - start, end: 区间边界
      - segment_size: 每段大小（可根据可用内存调整）
    """
    if end < 2 or start > end:
        return
    limit = int(math.isqrt(end)) + 1
    base_primes = sieve_of_eratosthenes(limit)
    low = max(start, 2)
    while low <= end:
        high = min(low + segment_size - 1, end)
        # 用 bytearray 表示段内是否为素数
        segment = bytearray(b"\x01") * (high - low + 1)
        for p in base_primes:
            if p * p > high:
                break
            # 求段内第一个 p 的倍数
            start_idx = max(p * p, ((low + p - 1) // p) * p)
            for j in range(start_idx, high + 1, p):
                segment[j - low] = 0
        for i, val in enumerate(segment, start=low):
            if val:
                yield i
        low += segment_size


def is_prime(n):
    """
    统一的素数判断接口：对小数使用快速试除，对大数使用 Miller-Rabin。

    说明：对于 n <= 1e6，朴素试除相当快速且确定；
    对于更大的 n，使用 Miller-Rabin 更高效。
    """
    if n < 2:
        return False
    if n <= 1000000:
        # 对小 n 使用简单试除（跳过偶数）
        if n % 2 == 0:
            return n == 2
        r = int(math.isqrt(n))
        for d in range(3, r + 1, 2):
            if n % d == 0:
                return False
        return True
    # 对更大 n 使用 Miller-Rabin（确定性基在 64-bit 范围内）
    return miller_rabin(n)


def prime_factors(n):
    """
    朴素质因数分解（试除法）。

    说明：适合中等大小整数。对于非常大的整数请考虑 Pollard's Rho 等更高效算法。
    """
    factors = []
    if n <= 1:
        return factors
    # 小素数试除
    for p in (2, 3, 5):
        while n % p == 0:
            factors.append(p)
            n //= p
    # wheel-like 方式跳过偶数，加快试除
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


def count_primes_in_ranges(start, end, interval, segment_size=65536):
    """
    统计 [start, end] 区间按照 interval 分箱后的素数数量。
    返回 (labels, counts)
    """
    # 构建桶标签
    buckets = []
    labels = []
    low = start
    while low <= end:
        high = min(low + interval - 1, end)
        labels.append(f"{low}-{high}")
        buckets.append(0)
        low += interval

    # 当 end 不大时直接一次性生成素数更快
    if end <= 1000000:
        primes = sieve_of_eratosthenes(end)
        for p in primes:
            if p < start:
                continue
            idx = (p - start) // interval
            if 0 <= idx < len(buckets):
                buckets[idx] += 1
    else:
        # 使用分段生成器逐个计数，避免内存峰值
        for p in segmented_sieve_generator(start, end, segment_size=segment_size):
            idx = (p - start) // interval
            if 0 <= idx < len(buckets):
                buckets[idx] += 1

    return labels, buckets


# ---------------------------
# 数据持久化工具
# ---------------------------

def save_primes_ndappend(primes_iterable):
    """
    将可迭代的素数逐行追加到 NDJSON（这里每行一个整数）文件中。

    适用于流式写入，避免在内存中存储全部素数。
    参数：primes_iterable - 可迭代对象（生成器、列表等）。
    """
    if not primes_iterable:
        return
    with open(PRIME_DB_ND, 'a', encoding='utf-8') as f:
        for p in primes_iterable:
            f.write(f"{p}\n")


def save_primes_json(primes):
    """
    将一组素数保存为 JSON 列表（覆盖写入）。

    仅适合小规模数据。
    """
    try:
        primes_sorted = sorted(set(primes))
        with open(PRIME_DB_JSON, 'w', encoding='utf-8') as f:
            json.dump(primes_sorted, f, indent=2)
    except Exception as e:
        print("保存 JSON 失败:", e)


def load_prime_db():
    """
    从 JSON 与 ND 文件中加载素数，合并去重并返回排序后的列表。

    注意：若文件非常大，加载会占用较多内存，请谨慎调用。
    """
    primes = set()
    if os.path.exists(PRIME_DB_JSON):
        try:
            with open(PRIME_DB_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    primes.update(data)
        except Exception:
            pass
    if os.path.exists(PRIME_DB_ND):
        try:
            with open(PRIME_DB_ND, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if s:
                        try:
                            primes.add(int(s))
                        except:
                            continue
        except Exception:
            pass
    return sorted(primes)

    self.root.geometry("900x750")
    self.root.resizable(True, True)

    self.notebook = ttk.Notebook(root)
    self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

    self.create_gen_page()
    self.create_check_page()
    self.create_db_page()
    self.create_plot_page()

    def create_gen_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="素数生成")

        tk.Label(frame, text="起始值：").grid(row=0, column=0, sticky='e', padx=10, pady=10)
        self.start_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.start_var, width=25).grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="终止值：").grid(row=1, column=0, sticky='e', padx=10, pady=10)
        self.end_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.end_var, width=25).grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="个位筛选（可选）：").grid(row=2, column=0, sticky='e', padx=10, pady=10)
        self.digit_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.digit_var, width=25).grid(row=2, column=1, padx=10, pady=10)

        tk.Button(frame, text="生成素数", command=self.generate_action, bg="#4CAF50", fg="white").grid(row=3, column=0, columnspan=2, pady=10)

        tk.Label(frame, text="结果：").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.gen_text = tk.Text(frame, height=12, width=75, font=("Courier", 9))
        self.gen_text.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

    def generate_action(self):
        try:
            start = int(self.start_var.get().strip())
            end = int(self.end_var.get().strip())
            if start > end or start < 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入有效的非负整数范围！")
            return

        digit = self.digit_var.get().strip()
        if digit and (not digit.isdigit() or len(digit) != 1):
            messagebox.showerror("错误", "个位筛选请输入0-9的数字！")
            return
        target_digit = int(digit) if digit else None

        range_size = end - start + 1

        # safety caps to avoid UI freeze / memory blow
        MAX_IN_MEMORY = 200_000  # when to avoid collecting entire list
        CHUNK_SIZE = 5000

        self.gen_text.delete(1.0, tk.END)

        # Prepare progress window
        progress = tk.Toplevel(self.root)
        progress.title("生成中...")
        tk.Label(progress, text=f"生成素数: {start} 到 {end}").pack(padx=10, pady=5)
        pb = ttk.Progressbar(progress, mode='determinate', length=400)
        pb.pack(padx=10, pady=10)
        progress.update()

        primes_count = 0
        preview = []

        try:
            if range_size <= 0:
                raise ValueError

            # choose strategy
            if end <= 1_000_000 and range_size <= 1_000_000:
                # small: full sieve up to end
                all_primes = sieve_of_eratosthenes(end)
                iterator = (p for p in all_primes if p >= start)
            else:
                # large: segmented generator
                # choose segment size proportional to memory and range
                seg_size = 65536
                if range_size > 5_000_000:
                    seg_size = 262144
                if range_size > 50_000_000:
                    seg_size = 524288
                iterator = segmented_sieve_generator(start, end, segment_size=seg_size)

            # iterate and process in chunks
            buffer = []
            last_update = time.time()
            processed = 0
            # we'll append primes to NDJSON to avoid keeping huge lists
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
                        # write chunk to NDJSON
                        for v in buffer:
                            ndfile.write(f"{v}\n")
                        buffer.clear()
                    # update progress occasionally
                    if range_size > 0:
                        if time.time() - last_update > 0.2:
                            pb['value'] = min(100, processed / range_size * 100)
                            progress.update()
                            last_update = time.time()

                # flush remaining buffer
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
            except:
                pass

        # show result preview
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
        except:
            messagebox.showerror("错误", "请输入有效的非负整数！")
            return

        self.check_text.delete(1.0, tk.END)
        if is_prime(n):
            self.check_text.insert(tk.END, f"{n} 是素数。\n")
            save_to_prime_db([n])
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
        if os.path.exists(PRIME_DB):
            os.remove(PRIME_DB)
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
        except:
            messagebox.showerror("输入错误", "请输入合理的数值！")
            return

        for widget in self.fig_frame.winfo_children():
            widget.destroy()

        ranges, counts = count_primes_in_ranges(start, end, interval)

        fig, ax = plt.subplots(figsize=(7, 5))
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