import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import random
import os
import struct

# ---------- Вспомогательные математические функции ----------
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

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def quick_pow(base: int, exp: int, mod: int) -> int:
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result

def prime_factors(n: int) -> list:
    factors = []
    i = 2
    while i * i <= n:
        if n % i == 0:
            factors.append(i)
            while n % i == 0:
                n //= i
        i += 1
    if n > 1:
        factors.append(n)
    return factors

def is_primitive_root(g: int, p: int, factors: list) -> bool:
    if g <= 1 or g >= p:
        return False
    for q in factors:
        if quick_pow(g, (p - 1) // q, p) == 1:
            return False
    return True

def find_all_primitive_roots(p: int) -> list:
    if not is_prime(p):
        return []
    phi = p - 1
    factors = prime_factors(phi)
    first_root = None
    for g in range(2, p):
        if is_primitive_root(g, p, factors):
            first_root = g
            break
    if first_root is None:
        return []
    roots = []
    for i in range(1, phi):
        if gcd(i, phi) == 1:
            roots.append(quick_pow(first_root, i, p))
    roots.sort()
    return roots

# ---------- Класс приложения ----------
class ElGamalApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №3 – Криптосистема Эль-Гамаля")
        root.geometry("950x800")
        root.minsize(800, 700)

        # Переменные
        self.p_var = tk.StringVar()
        self.x_var = tk.StringVar()
        self.k_var = tk.StringVar()
        self.g_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.roots_list = []
        self.selected_root = None

        # Пути к файлам (теперь не храним автоматически, будем спрашивать при сохранении)
        self.input_file_path = ""

        # Стиль
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        # Основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- Параметры p, x, k ----
        param_frame = ttk.LabelFrame(main_frame, text="Параметры алгоритма", padding="5")
        param_frame.pack(fill=tk.X, pady=5)

        ttk.Label(param_frame, text="Простое число p:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.p_entry = ttk.Entry(param_frame, textvariable=self.p_var, width=20)
        self.p_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(param_frame, text="Закрытый ключ x (1 < x < p-1):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.x_entry = ttk.Entry(param_frame, textvariable=self.x_var, width=20)
        self.x_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(param_frame, text="Начальное k (1 < k < p-1, gcd(k,p-1)=1):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.k_entry = ttk.Entry(param_frame, textvariable=self.k_var, width=20)
        self.k_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        self.find_roots_btn = ttk.Button(param_frame, text="Найти все первообразные корни", command=self.find_roots)
        self.find_roots_btn.grid(row=0, column=2, padx=10, pady=5)

        # ---- Выбор первообразного корня ----
        root_frame = ttk.LabelFrame(main_frame, text="Первообразные корни", padding="5")
        root_frame.pack(fill=tk.X, pady=5)

        self.roots_listbox = tk.Listbox(root_frame, height=5, font=('Courier', 10))
        self.roots_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll_roots = ttk.Scrollbar(root_frame, orient=tk.VERTICAL, command=self.roots_listbox.yview)
        scroll_roots.pack(side=tk.RIGHT, fill=tk.Y)
        self.roots_listbox.config(yscrollcommand=scroll_roots.set)
        self.roots_listbox.bind('<<ListboxSelect>>', self.on_root_select)

        # ---- Отображение вычисленного Y ----
        y_frame = ttk.LabelFrame(main_frame, text="Вычисленный открытый ключ Y", padding="5")
        y_frame.pack(fill=tk.X, pady=5)
        ttk.Label(y_frame, text="Y = g^x mod p =").pack(side=tk.LEFT, padx=5)
        self.y_label = ttk.Label(y_frame, text="", foreground="blue", font=('Courier', 12, 'bold'))
        self.y_label.pack(side=tk.LEFT, padx=5)

        # ---- Файлы ----
        file_frame = ttk.LabelFrame(main_frame, text="Файлы", padding="5")
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Button(file_frame, text="Выбрать исходный файл", command=self.select_input_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Зашифровать", command=self.encrypt_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Расшифровать", command=self.decrypt_file).pack(side=tk.LEFT, padx=5)

        self.file_label = ttk.Label(file_frame, text="Файл не выбран", foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)

        # ---- Лог вывода ----
        log_frame = ttk.LabelFrame(main_frame, text="Вывод (числа в десятичной системе, UTF-8)", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Courier', 10), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Статус
        self.status = ttk.Label(root, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def find_roots(self):
        try:
            p = int(self.p_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целое число p")
            return
        if not is_prime(p):
            messagebox.showerror("Ошибка", f"Число {p} не является простым")
            return
        self.log(f"Поиск первообразных корней для p = {p}...")
        roots = find_all_primitive_roots(p)
        if not roots:
            self.log("Не найдено ни одного первообразного корня.")
            return
        self.roots_list = roots
        self.roots_listbox.delete(0, tk.END)
        for r in roots:
            self.roots_listbox.insert(tk.END, str(r))
        self.log(f"Найдено {len(roots)} корней: {roots}")

    def on_root_select(self, event):
        selection = self.roots_listbox.curselection()
        if selection:
            self.selected_root = int(self.roots_listbox.get(selection[0]))
            self.g_var.set(str(self.selected_root))
            self.log(f"Выбран первообразный корень g = {self.selected_root}")
            self.update_y()

    def update_y(self):
        try:
            p = int(self.p_var.get())
            g = self.selected_root
            x = int(self.x_var.get())
        except:
            return
        if g is None or not (1 < x < p-1):
            return
        y = quick_pow(g, x, p)
        self.y_var.set(str(y))
        self.y_label.config(text=str(y))
        self.log(f"Вычислен Y = {y}")

    def select_input_file(self):
        path = filedialog.askopenfilename(title="Выберите исходный файл для шифрования/дешифрования")
        if path:
            self.input_file_path = path
            self.file_label.config(text=os.path.basename(path))

    def encrypt_file(self):
        # Проверка параметров
        try:
            p = int(self.p_var.get())
        except:
            messagebox.showerror("Ошибка", "Введите p")
            return
        if not is_prime(p):
            messagebox.showerror("Ошибка", f"p = {p} не простое")
            return

        if self.selected_root is None:
            messagebox.showerror("Ошибка", "Выберите первообразный корень g из списка")
            return
        g = self.selected_root

        try:
            x = int(self.x_var.get())
        except:
            messagebox.showerror("Ошибка", "Введите закрытый ключ x")
            return
        if not (1 < x < p-1):
            messagebox.showerror("Ошибка", f"x должно быть в интервале (1, {p-1})")
            return

        try:
            first_k = int(self.k_var.get())
        except:
            messagebox.showerror("Ошибка", "Введите начальное значение k")
            return
        if not (1 < first_k < p-1):
            messagebox.showerror("Ошибка", f"k должно быть в интервале (1, {p-1})")
            return
        if gcd(first_k, p-1) != 1:
            messagebox.showerror("Ошибка", f"k должно быть взаимно простым с {p-1}")
            return

        if not self.input_file_path:
            messagebox.showerror("Ошибка", "Выберите исходный файл")
            return

        # Вычисляем y = g^x mod p
        y = quick_pow(g, x, p)
        self.y_label.config(text=str(y))
        self.log(f"Открытый ключ: (p={p}, g={g}, y={y})")
        self.log(f"Закрытый ключ: x={x}")

        # Диалог сохранения зашифрованного файла
        output_file = filedialog.asksaveasfilename(
            title="Сохранить зашифрованный файл",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not output_file:
            self.log("Шифрование отменено пользователем.")
            return

        self.log("Шифрование файла...")
        try:
            with open(self.input_file_path, 'rb') as f_in, open(output_file, 'wb') as f_out:
                k = first_k
                byte_data = f_in.read(1)
                display_pairs = []
                while byte_data:
                    m = byte_data[0]
                    a = quick_pow(g, k, p)
                    b = (quick_pow(y, k, p) * m) % p
                    # Записываем a и b как 16-битные беззнаковые (двухбайтовые величины) little-endian
                    f_out.write(struct.pack('<HH', a & 0xFFFF, b & 0xFFFF))
                    if len(display_pairs) < 20:
                        display_pairs.append((a, b))
                    # Генерируем следующее k (случайное, взаимно простое с p-1)
                    while True:
                        k = random.randint(2, p-2)
                        if gcd(k, p-1) == 1:
                            break
                    byte_data = f_in.read(1)
            self.log("Шифрование завершено.")
            self.log(f"Зашифрованный файл сохранён как: {output_file}")
            self.log("Первые 20 пар (a, b) в десятичной системе (UTF-8):")
            for i, (a, b) in enumerate(display_pairs):
                self.log(f"  {i+1}: a={a}, b={b}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при шифровании: {e}")

    def decrypt_file(self):
        try:
            p = int(self.p_var.get())
        except:
            messagebox.showerror("Ошибка", "Введите p")
            return
        try:
            x = int(self.x_var.get())
        except:
            messagebox.showerror("Ошибка", "Введите закрытый ключ x")
            return

        # Выбор зашифрованного файла (пользователь сам выбирает)
        encrypted_path = filedialog.askopenfilename(
            title="Выберите зашифрованный файл",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not encrypted_path:
            self.log("Дешифрование отменено пользователем.")
            return

        # Диалог сохранения расшифрованного файла
        # По умолчанию предлагаем исходное расширение, если исходный файл был выбран, иначе .txt
        if self.input_file_path:
            default_ext = os.path.splitext(self.input_file_path)[1]
        else:
            default_ext = ".txt"
        decrypted_path = filedialog.asksaveasfilename(
            title="Сохранить расшифрованный файл",
            defaultextension=default_ext,
            filetypes=[("Все файлы", "*.*")]
        )
        if not decrypted_path:
            self.log("Дешифрование отменено пользователем.")
            return

        self.log("Дешифрование файла...")
        try:
            with open(encrypted_path, 'rb') as f_in, open(decrypted_path, 'wb') as f_out:
                while True:
                    data = f_in.read(4)  # два 2-байтовых числа (всего 4 байта)
                    if len(data) < 4:
                        break
                    a, b = struct.unpack('<HH', data)
                    inv_a = quick_pow(a, p-1-x, p)
                    m = (b * inv_a) % p
                    f_out.write(bytes([m]))
            self.log(f"Расшифрованный файл сохранён как: {decrypted_path}")
            self.log("Дешифрование завершено.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при дешифровании: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ElGamalApp(root)
    root.mainloop()