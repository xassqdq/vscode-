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

# Database: for small sets use JSON, for large streaming use NDJSON append
PRIME_DB_JSON = "primes_db.json"
PRIME_DB_ND = "primes_db.ndjson"


# ===== 算法区 =====


# Deterministic Miller-Rabin bases suitable for testing 64-bit integers
MR_BASES_64 = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]


def miller_rabin(n, bases=MR_BASES_64):
    """Deterministic Miller-Rabin for n < 2^64 using known bases."""
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23)
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False

    # write n-1 as d*2^s
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
    """Yield primes in [start, end] using a segmented sieve with limited memory."""
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
            # find first multiple >= low
            start_idx = max(p * p, ((low + p - 1) // p) * p)
            for j in range(start_idx, high + 1, p):
                segment[j - low] = 0
        for i, val in enumerate(segment, start=low):
            if val:
                yield i
        low += segment_size


def is_prime(n):
    """Choose a fast method to determine primality for a single n."""
    if n < 2:
        return False
    if n <= 1000000:
        # small check via trial division up to sqrt
        if n % 2 == 0:
            return n == 2
        r = int(math.isqrt(n))
        for d in range(3, r + 1, 2):
            if n % d == 0:
                return False
        return True
    # use deterministic Miller-Rabin for larger numbers (efficient)
    return miller_rabin(n)


def prime_factors(n):
    factors = []
    if n <= 1:
        return factors
    # trial divide small primes
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
    # Use generator to count without storing all primes
    buckets = []
    labels = []
    low = start
    while low <= end:
        high = min(low + interval - 1, end)
        labels.append(f"{low}-{high}")
        buckets.append(0)
        low += interval

    if end <= 1000000:
        primes = sieve_of_eratosthenes(end)
        for p in primes:
            if p < start:
                continue
            idx = (p - start) // interval
            if 0 <= idx < len(buckets):
                buckets[idx] += 1
    else:
        for p in segmented_sieve_generator(start, end, segment_size=segment_size):
            idx = (p - start) // interval
            if 0 <= idx < len(buckets):
                buckets[idx] += 1

    return labels, buckets


# ===== 数据持久化 =====


def save_primes_ndappend(primes_iterable):
    """Append primes to NDJSON file, one prime per line. Safe for large streams."""
    if not primes_iterable:
        return
    with open(PRIME_DB_ND, 'a', encoding='utf-8') as f:
        for p in primes_iterable:
            f.write(f"{p}\n")


def load_prime_db():
    """Load primes from both JSON and ND files (may be large). Return deduped sorted list (careful with huge files)."""
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


def save_primes_json(primes):
    try:
        primes_sorted = sorted(set(primes))
        with open(PRIME_DB_JSON, 'w', encoding='utf-8') as f:
            json.dump(primes_sorted, f, indent=2)
    except Exception as e:
        print("保存 JSON 失败:", e)


# ===== GUI主程序 =====


class PrimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("素数生成器 v3.0")
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