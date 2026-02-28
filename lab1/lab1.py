import tkinter as tk
from tkinter import ttk, filedialog

# --- Русский алфавит (33 буквы с Ё) ---
RUS_ALPHABET_UPPER = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
RUS_ALPHABET_LOWER = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'

def get_rus_index(char):
    """Возвращает индекс русской буквы (0-32) или -1, если не русская."""
    if char in RUS_ALPHABET_UPPER:
        return RUS_ALPHABET_UPPER.index(char)
    elif char in RUS_ALPHABET_LOWER:
        return RUS_ALPHABET_LOWER.index(char)
    else:
        return -1

def get_rus_char(index, is_upper):
    """Возвращает русскую букву по индексу с нужным регистром."""
    if is_upper:
        return RUS_ALPHABET_UPPER[index]
    else:
        return RUS_ALPHABET_LOWER[index]

def filter_russian_letters(s):
    """Возвращает строку, содержащую только русские буквы (включая Ё) из s."""
    return ''.join(ch for ch in s if ch in RUS_ALPHABET_UPPER or ch in RUS_ALPHABET_LOWER)

def extract_rails(key):
    """Извлекает число из строки ключа для метода железнодорожной изгороди."""
    digits = ''.join(filter(str.isdigit, key))
    return int(digits) if digits else 2  # значение по умолчанию 2

# --- Внутренние функции для железнодорожной изгороди (работают с любой строкой) ---
def _rail_fence_encrypt(text, rails):
    if rails <= 1 or not text:
        return text
    fence = [[] for _ in range(rails)]
    rail = 0
    direction = 1
    for char in text:
        fence[rail].append(char)
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction *= -1
    result = []
    for r in range(rails):
        result.extend(fence[r])
    return ''.join(result)

def _rail_fence_decrypt(cipher_text, rails):
    if rails <= 1 or not cipher_text:
        return cipher_text
    length = len(cipher_text)
    fence = [['' for _ in range(length)] for _ in range(rails)]
    rail = 0
    direction = 1
    for i in range(length):
        fence[rail][i] = '*'
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction *= -1
    index = 0
    for r in range(rails):
        for c in range(length):
            if fence[r][c] == '*' and index < length:
                fence[r][c] = cipher_text[index]
                index += 1
    result = []
    rail = 0
    direction = 1
    for i in range(length):
        result.append(fence[rail][i])
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction *= -1
    return ''.join(result)

# --- Функции для железнодорожной изгороди с сохранением позиций не-букв ---
def rail_fence_encrypt_russian(text, rails):
    """Шифрует только русские буквы, сохраняя позиции остальных символов."""
    letters = []
    positions = []
    for i, ch in enumerate(text):
        if get_rus_index(ch) != -1:
            letters.append(ch)
            positions.append(i)
    encrypted_letters = _rail_fence_encrypt(''.join(letters), rails)
    result = list(text)
    for pos, ch in zip(positions, encrypted_letters):
        result[pos] = ch
    return ''.join(result)

def rail_fence_decrypt_russian(cipher_text, rails):
    """Дешифрует только русские буквы, сохраняя позиции остальных символов."""
    letters = []
    positions = []
    for i, ch in enumerate(cipher_text):
        if get_rus_index(ch) != -1:
            letters.append(ch)
            positions.append(i)
    decrypted_letters = _rail_fence_decrypt(''.join(letters), rails)
    result = list(cipher_text)
    for pos, ch in zip(positions, decrypted_letters):
        result[pos] = ch
    return ''.join(result)

# --- Функции для Виженера с прогрессивным ключом (русский алфавит) ---
def vigenere_encrypt(text, key):
    if not text:
        return text
    key_filtered = filter_russian_letters(key)
    if not key_filtered:          # нет русских букв в ключе — шифрование не применяется
        return text
    key_indices = [get_rus_index(ch) for ch in key_filtered]
    result = []
    for ch in text:
        idx = get_rus_index(ch)
        if idx == -1:
            result.append(ch)          # не русский символ – оставляем как есть
            continue
        is_upper = ch in RUS_ALPHABET_UPPER
        k_idx = key_indices[0]          # текущий первый элемент ключа
        new_idx = (idx + k_idx) % 33
        result.append(get_rus_char(new_idx, is_upper))
        # Циклический сдвиг ключа влево (прогрессивный ключ)
        key_indices.append(key_indices.pop(0)+1)
    return ''.join(result)

def vigenere_decrypt(cipher_text, key):
    if not cipher_text:
        return cipher_text
    key_filtered = filter_russian_letters(key)
    if not key_filtered:
        return cipher_text
    key_indices = [get_rus_index(ch) for ch in key_filtered]
    result = []
    for ch in cipher_text:
        idx = get_rus_index(ch)
        if idx == -1:
            result.append(ch)
            continue
        is_upper = ch in RUS_ALPHABET_UPPER
        k_idx = key_indices[0]
        new_idx = (idx - k_idx) % 33
        result.append(get_rus_char(new_idx, is_upper))
        key_indices.append(key_indices.pop(0)+1)  # прогрессивный сдвиг
    return ''.join(result)

# --- Основные функции обработки ---
def encrypt_text():
    text = txt_Source.get()
    if not text:
        return
    method = combo.get()
    key = txt_Key.get()
    
    if method == "Железнодорожная изгородь":
        rails = extract_rails(key)
        encrypted = rail_fence_encrypt_russian(text, rails)
    else:  # Виженер
        encrypted = vigenere_encrypt(text, key)
    
    dest_var.set(encrypted)

def decrypt_text():
    cipher = txt_Source.get()   
    if not cipher:
        return
    method = combo.get()
    key = txt_Key.get()
    
    if method == "Железнодорожная изгородь":
        rails = extract_rails(key)
        decrypted = rail_fence_decrypt_russian(cipher, rails)
    else:  # Виженер
        decrypted = vigenere_decrypt(cipher, key)
    
    dest_var.set(decrypted)

def save_to_file():
    text_to_save = dest_var.get()
    if not text_to_save:
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
        title="Сохранить результат в файл"
    )
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text_to_save)

def load_from_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
        title="Загрузить текст из файла"
    )
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        txt_Source.delete(0, tk.END)
        txt_Source.insert(0, content)

# --- Интерфейс ---
window = tk.Tk()
window.title("Лабораторная работа №1")
window.geometry('800x450')
window.minsize(700, 400)
window.option_add('*TCombobox*Listbox.font', ('Segoe UI', 14))

style = ttk.Style()
if 'clam' in style.theme_names():
    style.theme_use('clam')
elif 'vista' in style.theme_names():
    style.theme_use('vista')

FONT = ('Segoe UI', 14)
FONT_BOLD = ('Segoe UI', 14, 'bold')

dest_var = tk.StringVar()

# --- Размещение элементов ---
lbl_Source = ttk.Label(window, text="Исходный текст:", font=FONT_BOLD)
lbl_Source.grid(column=0, row=0, padx=(20, 5), pady=(20, 5), sticky='w')

txt_Source = ttk.Entry(window, width=40, font=FONT)
txt_Source.grid(column=1, row=0, columnspan=2, padx=(5, 20), pady=(20, 5), sticky='ew')
txt_Source.focus()

lbl_Cipher = ttk.Label(window, text="Метод шифрования:", font=FONT_BOLD)
lbl_Cipher.grid(column=0, row=1, padx=(20, 5), pady=10, sticky='w')

combo = ttk.Combobox(window, width=30, font=FONT)
combo['values'] = ("Железнодорожная изгородь", "Виженер (прогрессивный ключ)")
combo.current(0)
combo.grid(column=1, row=1, columnspan=2, padx=(5, 20), pady=10, sticky='w')

# --- Поле для ключа ---
lbl_Key = ttk.Label(window, text="Ключ:", font=FONT_BOLD)
lbl_Key.grid(column=0, row=2, padx=(20, 5), pady=5, sticky='w')

txt_Key = ttk.Entry(window, width=30, font=FONT)
txt_Key.grid(column=1, row=2, columnspan=2, padx=(5, 20), pady=5, sticky='w')

# --- Функция обновления поля ключа при смене метода ---
def on_method_change(event=None):
    method = combo.get()
    if method == "Железнодорожная изгородь":
        txt_Key.delete(0, tk.END)
        txt_Key.insert(0, "3")
    else:
        txt_Key.delete(0, tk.END)
        txt_Key.insert(0, "ключ")

combo.bind('<<ComboboxSelected>>', on_method_change)
on_method_change()  # установить начальное значение

# --- Кнопки ---
btn_encrypt = ttk.Button(window, text="Зашифровать", command=encrypt_text, width=20)
btn_encrypt.grid(column=1, row=3, padx=(5, 5), pady=15, sticky='e')

btn_decrypt = ttk.Button(window, text="Расшифровать", command=decrypt_text, width=20)
btn_decrypt.grid(column=2, row=3, padx=(5, 20), pady=15, sticky='w')

# --- Блок вывода ---
lbl_Dest = ttk.Label(window, text="Результат:", font=FONT_BOLD)
lbl_Dest.grid(column=0, row=4, padx=(20, 5), pady=(20, 5), sticky='w')

txt_Dest = ttk.Entry(window, width=40, font=FONT, textvariable=dest_var, state='readonly')
txt_Dest.grid(column=1, row=4, columnspan=2, padx=(5, 20), pady=(20, 5), sticky='ew')

# --- Кнопки работы с файлами ---
btn_load = ttk.Button(window, text="Загрузить из файла", command=load_from_file, width=25)
btn_load.grid(column=1, row=5, padx=(5, 5), pady=15, sticky='e')

btn_save = ttk.Button(window, text="Сохранить в файл", command=save_to_file, width=25)
btn_save.grid(column=2, row=5, padx=(5, 20), pady=15, sticky='w')

window.grid_rowconfigure(6, weight=1)

window.mainloop()