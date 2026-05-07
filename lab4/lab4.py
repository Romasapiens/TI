import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import tempfile

# ---------- Математические функции ----------
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def quick_pow(base: int, exp: int, mod: int) -> int:
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result

def extended_gcd(a: int, b: int):
    if b == 0:
        return a, 1, 0
    gcd, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return gcd, x, y

def mod_inverse(a: int, m: int) -> int:
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError(f"Обратного элемента не существует: gcd({a},{m})={gcd}")
    return x % m

# ---------- Хеш-функция (формула 3.2) с поддержкой русского и английского ----------
def char_value(ch: str) -> int:
    """Возвращает числовое значение символа:
       Для русских букв (включая Ё): А=1, Б=2, ..., Я=33.
       Для английских букв: A=1, B=2, ..., Z=26 (регистронезависимо).
       Для остальных символов: 0."""
    # Русский алфавит с Ё
    rus_upper = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    rus_lower = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    if ch in rus_upper:
        return rus_upper.index(ch) + 1
    elif ch in rus_lower:
        return rus_lower.index(ch) + 1
    elif 'A' <= ch <= 'Z':
        return ord(ch) - ord('A') + 1
    elif 'a' <= ch <= 'z':
        return ord(ch) - ord('a') + 1
    else:
        return 0

def compute_hash(file_path: str, n: int, log_callback=None) -> int:
    """Вычисляет хеш-образ текстового файла по формуле Hi = (Hi-1 + Mi)^2 mod n.
       Mi – числовое значение буквы (1..33 для русских, 1..26 для английских), остальные символы игнорируются.
       H0 = 100.
       Если log_callback задан, вызывается с сообщением о каждом шаге.
    """
    H = 100
    if log_callback:
        log_callback(f"Начальное H0 = {H}")
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    for i, ch in enumerate(text):
        val = char_value(ch)
        if val == 0:
            continue
        H_prev = H
        H = (H + val) ** 2 % n
        if log_callback:
            log_callback(f"Шаг {i+1}: символ '{ch}' -> M={val}, H_prev={H_prev}, H_new = ({H_prev}+{val})^2 mod {n} = {H}")
    return H

# ---------- Основное приложение ----------
class RSASignatureApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №4 – ЭЦП RSA")
        root.geometry("950x850")
        root.minsize(800, 750)

        # Переменные
        self.p_var = tk.StringVar()
        self.q_var = tk.StringVar()
        self.d_var = tk.StringVar()
        self.e_var = tk.StringVar()
        self.n_var = tk.StringVar()
        self.phi_var = tk.StringVar()
        self.hash_var = tk.StringVar()
        self.signature_var = tk.StringVar()

        self.input_file_path = ""
        self.verify_file_path = ""

        # Стиль
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        # Основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- Параметры ключей ----
        key_frame = ttk.LabelFrame(main_frame, text="Параметры RSA", padding="5")
        key_frame.pack(fill=tk.X, pady=5)

        ttk.Label(key_frame, text="Простое число p:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.p_entry = ttk.Entry(key_frame, textvariable=self.p_var, width=15)
        self.p_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(key_frame, text="Простое число q:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.q_entry = ttk.Entry(key_frame, textvariable=self.q_var, width=15)
        self.q_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(key_frame, text="Закрытый ключ d (1<d<φ(n), взаимно прост с φ(n)):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.d_entry = ttk.Entry(key_frame, textvariable=self.d_var, width=15)
        self.d_entry.grid(row=2, column=1, padx=5, pady=5)

        self.gen_keys_btn = ttk.Button(key_frame, text="Вычислить открытый ключ e", command=self.compute_e)
        self.gen_keys_btn.grid(row=2, column=2, padx=10, pady=5)

        ttk.Label(key_frame, text="n = p*q:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(key_frame, textvariable=self.n_var, font=('Courier', 10)).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(key_frame, text="φ(n) = (p-1)(q-1):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(key_frame, textvariable=self.phi_var, font=('Courier', 10)).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(key_frame, text="Открытый ключ e:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(key_frame, textvariable=self.e_var, font=('Courier', 10)).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        # ---- Файлы ----
        file_frame = ttk.LabelFrame(main_frame, text="Подписание файла", padding="5")
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Button(file_frame, text="Выбрать исходный файл", command=self.select_input_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Подписать файл", command=self.sign_file).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(file_frame, text="Файл не выбран", foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)

        # ---- Проверка подписи ----
        verify_frame = ttk.LabelFrame(main_frame, text="Проверка подписи", padding="5")
        verify_frame.pack(fill=tk.X, pady=5)

        ttk.Button(verify_frame, text="Выбрать файл с подписью", command=self.select_verify_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(verify_frame, text="Проверить подпись", command=self.verify_signature).pack(side=tk.LEFT, padx=5)
        self.verify_label = ttk.Label(verify_frame, text="Файл не выбран", foreground="gray")
        self.verify_label.pack(side=tk.LEFT, padx=10)

        # ---- Вывод результатов ----
        result_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="5")
        result_frame.pack(fill=tk.X, pady=5)

        ttk.Label(result_frame, text="Хеш-образ сообщения (десятичное):").pack(anchor=tk.W, padx=5, pady=2)
        self.hash_entry = ttk.Entry(result_frame, textvariable=self.hash_var, font=('Courier', 10), width=60)
        self.hash_entry.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(result_frame, text="Цифровая подпись S (десятичное):").pack(anchor=tk.W, padx=5, pady=2)
        self.sign_entry = ttk.Entry(result_frame, textvariable=self.signature_var, font=('Courier', 10), width=60)
        self.sign_entry.pack(fill=tk.X, padx=5, pady=2)

        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог (промежуточные значения)", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Courier', 10), wrap=tk.WORD, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Статус
        self.status = ttk.Label(root, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def compute_e(self):
        try:
            p = int(self.p_var.get())
            q = int(self.q_var.get())
            d = int(self.d_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целые числа p, q, d")
            return
        if not is_prime(p):
            messagebox.showerror("Ошибка", f"p = {p} не является простым")
            return
        if not is_prime(q):
            messagebox.showerror("Ошибка", f"q = {q} не является простым")
            return
        if p == q:
            messagebox.showerror("Ошибка", "p и q должны быть различными")
            return
        n = p * q
        phi = (p-1)*(q-1)
        if not (1 < d < phi):
            messagebox.showerror("Ошибка", f"d должно быть в интервале (1, {phi})")
            return
        try:
            e = mod_inverse(d, phi)
        except ValueError as err:
            messagebox.showerror("Ошибка", f"d не обратимо по модулю φ(n): {err}")
            return
        self.n_var.set(str(n))
        self.phi_var.set(str(phi))
        self.e_var.set(str(e))
        self.log(f"Вычислено: n = {n}, φ(n) = {phi}")
        self.log(f"Открытый ключ e = {e}")

    def select_input_file(self):
        path = filedialog.askopenfilename(title="Выберите текстовый файл для подписи",
                                          filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if path:
            self.input_file_path = path
            self.file_label.config(text=os.path.basename(path))
            self.hash_var.set("")
            self.signature_var.set("")

    def select_verify_file(self):
        path = filedialog.askopenfilename(title="Выберите файл с подписью",
                                          filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if path:
            self.verify_file_path = path
            self.verify_label.config(text=os.path.basename(path))

    def sign_file(self):
        if not self.input_file_path:
            messagebox.showerror("Ошибка", "Выберите исходный файл")
            return
        if not self.e_var.get():
            messagebox.showerror("Ошибка", "Сначала вычислите открытый ключ (кнопка 'Вычислить открытый ключ e')")
            return
        try:
            n = int(self.n_var.get())
            d = int(self.d_var.get())
        except:
            messagebox.showerror("Ошибка", "Некорректные значения параметров")
            return

        self.log(f"\n--- Подписание файла: {self.input_file_path} ---")
        def log_hash(msg):
            self.log(msg)

        try:
            h = compute_hash(self.input_file_path, n, log_callback=log_hash)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при вычислении хеша: {e}")
            return
        self.hash_var.set(str(h))
        self.log(f"Финальный хеш-образ сообщения h = {h}")

        s = quick_pow(h, d, n)
        self.signature_var.set(str(s))
        self.log(f"Цифровая подпись S = {h}^{d} mod {n} = {s}")

        base, ext = os.path.splitext(self.input_file_path)
        signed_path = base + "_signed.txt"
        try:
            with open(self.input_file_path, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
            with open(signed_path, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
                f_out.write(f"\n{s}")
            self.log(f"Подписанный файл сохранён как: {signed_path}")
            messagebox.showinfo("Успех", f"Подпись создана.\nФайл сохранён: {signed_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении подписанного файла: {e}")
        self.log("--- Подписание завершено ---\n")

    def verify_signature(self):
        if not self.verify_file_path:
            messagebox.showerror("Ошибка", "Выберите файл с подписью")
            return
        if not self.e_var.get():
            messagebox.showerror("Ошибка", "Сначала вычислите открытый ключ (кнопка 'Вычислить открытый ключ e')")
            return
        try:
            n = int(self.n_var.get())
            e = int(self.e_var.get())
        except:
            messagebox.showerror("Ошибка", "Некорректные значения параметров")
            return

        self.log(f"\n--- Проверка подписи файла: {self.verify_file_path} ---")
        try:
            with open(self.verify_file_path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            if not lines:
                messagebox.showerror("Ошибка", "Файл пуст")
                return
            last_line = lines[-1].strip()
            try:
                signature = int(last_line)
            except ValueError:
                messagebox.showerror("Ошибка", "Последняя строка файла не является числом (подписью)")
                self.log("ОШИБКА: последняя строка не число, проверка невозможна.")
                return
            message_content = "\n".join(lines[:-1])
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as tmp:
                tmp.write(message_content)
                tmp_path = tmp.name
            def log_hash(msg):
                self.log(msg)
            h_calc = compute_hash(tmp_path, n, log_callback=log_hash)
            os.unlink(tmp_path)

            h_from_sig = quick_pow(signature, e, n)

            self.log(f"\nРезультаты проверки:")
            self.log(f"1. Хеш, вычисленный из полученного сообщения (h1) = {h_calc}")
            self.log(f"2. Хеш, восстановленный из цифровой подписи (h2) = {h_from_sig} (S^{e} mod n)")

            if h_calc == h_from_sig:
                self.log("--> h1 == h2, следовательно, подпись ВЕРНА.")
                self.log("Сообщение не было изменено, подпись принадлежит отправителю.")
                messagebox.showinfo("Результат проверки", f"Подпись верна!\n\nh1 = h2 = {h_calc}")
            else:
                self.log("--> h1 != h2, следовательно, подпись НЕВЕРНА.")
                messagebox.showwarning("Результат проверки", f"Подпись неверна!\n\nh1 = {h_calc}\nh2 = {h_from_sig}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при проверке: {e}")
        self.log("--- Проверка завершена ---\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = RSASignatureApp(root)
    root.mainloop()