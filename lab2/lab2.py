import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

class LFSR:
    def __init__(self, init_state):
        """
        init_state: строка из 35 символов '0'/'1' или целое число
        """
        if isinstance(init_state, str):
            filtered = ''.join(c for c in init_state if c in '01')[-35:]
            if len(filtered) < 35:
                filtered = filtered.rjust(35, '0')
            self.state = int(filtered, 2)
        else:
            self.state = init_state & ((1 << 35) - 1)

        if self.state == 0:
            raise ValueError("Состояние не может быть нулевым")

        self.mask = (1 << 35) - 1

    def next_bit(self):
        """возвращает очередной бит гаммы (старший бит) и обновляет состояние (сдвиг влево)"""
        out_bit = (self.state >> 34) & 1                     
        feedback = ((self.state >> 34) & 1) ^ ((self.state >> 1) & 1)   
        self.state = ((self.state << 1) & self.mask) | feedback          
        return out_bit

    def next_byte(self):
        """возвращает байт (8 бит) гаммы, первый бит – старший (соответствует порядку выдачи)"""
        byte = 0
        for i in range(8):
            byte |= (self.next_bit() << i)
        return byte


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №2 – LFSR шифрование")
        root.geometry("900x700")
        root.minsize(800, 600)

        # Переменные
        self.original_data = b''          
        self.encrypted_data = b''        
        self.gamma_data = b''            
        self.key_str = tk.StringVar(value='1'*35)   

        # Настройка стилей
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        # Основной контейнер
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- Поле для ввода сеансового ключа (начальное состояние) ----
        key_frame = ttk.LabelFrame(main_frame, text="Сеансовый ключ (35 бит, только 0 и 1)", padding="5")
        key_frame.pack(fill=tk.X, pady=5)

        vcmd = (root.register(self.validate_key), '%P')
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_str, font=('Courier', 12),
                                   validate='key', validatecommand=vcmd)
        self.key_entry.pack(fill=tk.X, padx=5, pady=5)
        self.key_entry.bind('<KeyRelease>', self.check_key_length)

        # ---- Кнопки загрузки/сохранения ----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Загрузить исходный файл", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Зашифровать", command=self.encrypt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Расшифровать", command=self.decrypt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сохранить результат", command=self.save_file).pack(side=tk.LEFT, padx=5)

        # ---- Поля для отображения ----
        # Исходный файл
        orig_frame = ttk.LabelFrame(main_frame, text="Исходный файл", padding="5")
        orig_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.orig_text = scrolledtext.ScrolledText(orig_frame, font=('Courier', 10), wrap=tk.WORD, height=6)
        self.orig_text.pack(fill=tk.BOTH, expand=True)

        # Итерационный ключ
        gamma_frame = ttk.LabelFrame(main_frame, text="Итерационный ключ", padding="5")
        gamma_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.gamma_text = scrolledtext.ScrolledText(gamma_frame, font=('Courier', 10), wrap=tk.WORD, height=4)
        self.gamma_text.pack(fill=tk.BOTH, expand=True)

        # Выходной файл
        enc_frame = ttk.LabelFrame(main_frame, text="Выходной файл", padding="5")
        enc_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.enc_text = scrolledtext.ScrolledText(enc_frame, font=('Courier', 10), wrap=tk.WORD, height=6)
        self.enc_text.pack(fill=tk.BOTH, expand=True)

        # Статус-бар
        self.status = ttk.Label(root, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def validate_key(self, new_value):
        """Разрешены только 0 и 1, не более 35 символов"""
        if new_value == "" or all(c in '01' for c in new_value):
            return len(new_value) <= 35
        return False

    def check_key_length(self, event=None):
        """Если больше 35, обрезать"""
        val = self.key_str.get()
        if len(val) > 35:
            self.key_str.set(val[:35])

    def load_file(self):
        file_path = filedialog.askopenfilename(title="Выберите файл для загрузки")
        if not file_path:
            return
        try:
            with open(file_path, 'rb') as f:
                self.original_data = f.read()
            self.display_binary(self.orig_text, self.original_data)
            self.status.config(text=f"Загружен файл: {file_path} ({len(self.original_data)} байт)")
            self.encrypted_data = b''
            self.gamma_data = b''
            self.enc_text.delete(1.0, tk.END)
            self.gamma_text.delete(1.0, tk.END)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    def save_file(self):
        if not self.encrypted_data:
            messagebox.showwarning("Предупреждение", "Нет зашифрованных данных для сохранения")
            return
        file_path = filedialog.asksaveasfilename(title="Сохранить зашифрованный файл",
                                                  defaultextension=".bin",
                                                  filetypes=[("Все файлы", "*.*")])
        if not file_path:
            return
        try:
            with open(file_path, 'wb') as f:
                f.write(self.encrypted_data)
            self.status.config(text=f"Файл сохранён: {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def encrypt(self):
        """Выполняет шифрование (XOR с гаммой)"""
        if not self.original_data:
            messagebox.showwarning("Предупреждение", "Сначала загрузите исходный файл")
            return
        key_str = self.key_str.get().strip()
        if not key_str:
            messagebox.showerror("Ошибка", "Введите сеансовый ключ")
            return
        if len(key_str) < 35:
            key_str = key_str.rjust(35, '0')
        if all(c == '0' for c in key_str):
            messagebox.showerror("Ошибка", "Сеансовый ключ не может быть нулевым")
            return

        try:
            lfsr = LFSR(key_str)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        data_len = len(self.original_data)
        gamma_bytes = bytearray()
        encrypted = bytearray()
        for _ in range(data_len):
            gb = lfsr.next_byte()
            gamma_bytes.append(gb)
            encrypted.append(self.original_data[_] ^ gb)

        self.gamma_data = bytes(gamma_bytes)
        self.encrypted_data = bytes(encrypted)

        self.display_binary(self.gamma_text, self.gamma_data) 
        self.display_binary(self.enc_text, self.encrypted_data)
        self.status.config(text=f"Зашифровано {data_len} байт. Гамма сгенерирована.")

    def decrypt(self):
        self.encrypt()
        self.status.config(text="Дешифрование выполнено (результат в поле зашифрованного)")

    def display_binary(self, text_widget, data, max_bytes=500):
        text_widget.delete(1.0, tk.END)
        if not data:
            return

        show_data = data[:max_bytes]
        bits_list = [f"{b:08b}"[::-1] for b in show_data]
        text_widget.insert(1.0, ' '.join(bits_list))

        if len(data) > max_bytes:
            text_widget.insert(tk.END, f"\n... и ещё {len(data)-max_bytes} байт")


# ------------------------- Main -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()