import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
from openpyxl import Workbook
import socket
import threading
from datetime import datetime
import json

class DishFrame(ttk.Frame):
    def __init__(self, parent, dish_data, update_callback, delete_callback):
        super().__init__(parent)
        self.dish_data = dish_data
        self.update_callback = update_callback
        self.delete_callback = delete_callback

        self.style = ttk.Style()
        self.style.configure('Dish.TFrame', font=('Arial', 14), background='white', borderwidth=2)

        self.configure(padding=10, relief='raised', borderwidth=2,style='Dish.TFrame')
        self.grid_columnconfigure(1, weight=1)
    # Элементы фрейма
        self.name_label = ttk.Label(self, text=dish_data['name'],
                                    font=('Arial', 14, 'bold'), wraplength=150,background='white')
        self.name_label.grid(row=0, column=0, sticky='w', pady=(0, 5))

        self.price_label = ttk.Label(self, text=f"{dish_data['price']} ₽", font=('Arial', 14),background='white')
        self.price_label.grid(row=0, column=1, sticky='e')

        self.ingredients_label = ttk.Label(self, text=f'Ингредиенты:\n{dish_data['ingredients']}',
                                           wraplength=200,background='white')
        self.ingredients_label.grid(row=1, column=0, columnspan=2, sticky='w')
    # Кнопки управления
        self.button_frame = ttk.Frame(self,style='Dish.TFrame')
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky='e')

        self.status_label = ttk.Label(self.button_frame, text=f"{dish_data['status']}",
                                      anchor = 'w', font=('Arial', 12),background='white')
        self.status_label.pack(side="left")

        self.edit_btn = ttk.Button(self.button_frame, text="Изменить",
                                   command=self.edit_dish)
        self.edit_btn.pack(side="right", padx=2)

        self.delete_btn = ttk.Button(self.button_frame, text="Удалить",
                                     command=self.confirm_delete)
        self.delete_btn.pack(side="right", padx=2)

    def edit_dish(self):
    # Создаем диалоговое окно для редактирования
        edit_window = tk.Toplevel(self)
        edit_window.title("Редактировать блюдо")
        edit_window.geometry("400x320")

        ttk.Label(edit_window, text="Название:").pack(pady=(10, 0), padx=10, anchor='w')
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, self.dish_data['name'])
        name_entry.pack(fill='x', padx=10, pady=(0, 10))

        change_state = ttk.Label(edit_window)
        change_state.pack(pady=(10, 0), padx=10, anchor='w')
        ttk.Label(change_state, text="Статус:").pack(side='left')
        states = ["В стоп листе", "Действителен"]
        combobox = ttk.Combobox(change_state, textvariable=self.dish_data['status'], values=states, state="readonly")
        combobox.pack(side='left', padx=5)

        ttk.Label(edit_window, text="Цена (₽):").pack(pady=(10, 0), padx=10, anchor='w')
        price_entry = ttk.Entry(edit_window)
        price_entry.insert(0, str(self.dish_data['price']))
        price_entry.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Label(edit_window, text="Ингредиенты:").pack(pady=(10, 0), padx=10, anchor='w')
        ingredients_text = tk.Text(edit_window, height=5)
        ingredients_text.insert('1.0', self.dish_data['ingredients'])
        ingredients_text.pack(fill='x', padx=10, pady=(0, 10))

        def save_changes():
            new_name = name_entry.get().strip()
            new_price = price_entry.get().strip()
            new_ingredients = ingredients_text.get('1.0', 'end-1c').strip()
            new_status=combobox.get().strip()

            if not new_name or not new_price or not new_ingredients or not new_status:
                messagebox.showwarning("Ошибка", "Все поля должны быть заполнены!")
                return

            try:
                new_price = float(new_price)
            except ValueError:
                messagebox.showwarning("Ошибка", "Цена должна быть числом!")
                return
            if new_price < 0:
                messagebox.showwarning("Ошибка", "Цена должна быть положительной!")
                return
    # Обновляем данные
            self.dish_data['name'] = new_name
            self.dish_data['price'] = new_price
            self.dish_data['ingredients'] = new_ingredients
            self.dish_data['status'] = new_status
    # Обновляем отображение
            self.name_label.config(text=new_name)
            self.price_label.config(text=f"{new_price} ₽")
            self.ingredients_label.config(text=new_ingredients)
            self.status_label.config(text=new_status)
    # Вызываем callback для сохранения
            self.update_callback()
            edit_window.destroy()

        ttk.Button(edit_window, text="Сохранить", command=save_changes).pack(pady=10)

    def confirm_delete(self):
        if messagebox.askyesno("Подтверждение",
                               f"Удалить блюдо '{self.dish_data['name']}'?"):
            self.delete_callback(self.dish_data['id'])
            self.destroy()

class Server:
    def __init__(self, root):
        self.root = root
        self.root.title("Сервер")
        self.root.geometry("1000x700")
    # Настройки подключения
        self.host = '0.0.0.0'
        self.port = 5050
        self.k_host = ''
        self.k_port = 5051
        self.server_socket = None
        self.client_socket = None
        self.listening = False
    # Файл для меню
        self.current_file =  None
    # Файл для истории заказов
        self.current_history_file = None
    # Стили
        self.style = ttk.Style()
        self.style.configure('Nav.TButton', font=('Arial', 10), padding=10, relief='raised')
        self.style.configure('Connection.TFrame', background='#f0f0f0')
    # Данные меню
        self.dishes  = []
        self.next_id  = 1
    # Создание интерфейса
        self.create_widgets()
        if self.current_file is not None: self.load_men_data()
        self.show_section("beg")

    def create_widgets(self):
    # Главный контейнер
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True)
    # Боковая панель навигации
        self.nav_frame = ttk.Frame(self.main_container, width=200, style='Nav.TFrame', relief='raised')
        self.nav_frame.pack(side='left', fill='y')
        self.nav_frame.pack_propagate(False)
    # Кнопки навигации
        ttk.Label(self.nav_frame, text="Menu and orders\nmanager system",
                  font=('Arial', 12, 'bold')).pack(pady=(20, 10))

        self.menu_btn = ttk.Button(
            self.nav_frame, text="🍽️ Меню", style='Nav.TButton',
            command=self.show_menu_section)
        self.menu_btn.pack(fill='x', pady=5, padx=5)

        self.connection_btn = ttk.Button(
            self.nav_frame, text="🔗 Подключение", style='Nav.TButton',
            command=self.show_connection_section)
        self.connection_btn.pack(fill='x', pady=5, padx=5)

        self.order_history_btn = ttk.Button(
            self.nav_frame, text="История", style='Nav.TButton',
            command=self.show_order_history_section)
        self.order_history_btn.pack(fill='x', pady=5, padx=5)

        self.settings_btn = ttk.Button(
            self.nav_frame, text="⚙️ Настройки", style='Nav.TButton',
            command=self.show_settings_section)
        self.settings_btn.pack(fill='x', pady=5, padx=5)
    # Основная область контента
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
    # Фреймы для разных разделов
        self.menu_section = ttk.Frame(self.content_frame)
        self.settings_section = ttk.Frame(self.content_frame)
        self.connection_section = ttk.Frame(self.content_frame, style='Connection.TFrame')
        self.order_history_section = ttk.Frame(self.content_frame)
    # Инициализация разделов
        self.init_menu_section()
        self.init_settings_section()
        self.init_connection_section()
        self.init_order_history_section()

    def init_menu_section(self):
    # Основной фрейм с прокруткой
        self.menu_canvas = tk.Canvas(self.menu_section, relief = 'sunken')
        self.menu_scrollbar = ttk.Scrollbar(self.menu_section, orient='vertical', command=self.menu_canvas.yview)
        self.menu_scrollable_frame = ttk.Frame(self.menu_canvas)

        self.menu_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.menu_canvas.configure(
                scrollregion=self.menu_canvas.bbox("all")
            )
        )
        self.menu_canvas.create_window((0, 0), window=self.menu_scrollable_frame, anchor="nw")
        self.menu_canvas.configure(yscrollcommand=self.menu_scrollbar.set)

        self.menu_canvas.pack(side="left", fill = "both",expand = True)
        self.menu_scrollbar.pack(side="right", fill = "y")
    # Кнопка добавления
        self.add_btn = ttk.Button(
            self.menu_canvas,
            text="+ Добавить блюдо",
            command=self.add_dish)
        self.add_btn.pack(anchor="s",expand = True,fill = "x",side="bottom")

    def update_menu_display(self):
    # Очищаем текущие фреймы
        for widget in self.menu_scrollable_frame.winfo_children():
            widget.destroy()
    # Создаем фреймы для каждого блюда
        for i, dish in enumerate(self.dishes):
            DishFrame(
                self.menu_scrollable_frame,
                dish,
                self.save_data,
                self.delete_dish).grid(row=i, column=0, sticky='ew', pady=5, padx=5)

    def add_dish(self):
    # Диалоговое окно для добавления нового блюда
        add_window = tk.Toplevel(self.root)
        add_window.title("Добавить блюдо")
        add_window.geometry("400x320")

        ttk.Label(add_window, text="Название:").pack(pady=(10, 0), padx=10, anchor='w')
        name_entry = ttk.Entry(add_window)
        name_entry.pack(fill='x', padx=10, pady=(0, 10))

        change_state = ttk.Label(add_window)
        change_state.pack(pady=(10, 0), padx=10, anchor='w')
        ttk.Label(change_state, text="Статус:").pack(side='left')
        states = ["В стоп листе", "Действителен"]
        combobox = ttk.Combobox(change_state, values=states, state="readonly")
        combobox.pack(side='left', padx=5)

        ttk.Label(add_window, text="Цена (₽):").pack(pady=(10, 0), padx=10, anchor='w')
        price_entry = ttk.Entry(add_window)
        price_entry.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Label(add_window, text="Ингредиенты:").pack(pady=(10, 0), padx=10, anchor='w')
        ingredients_text = tk.Text(add_window, height=5)
        ingredients_text.pack(fill='x', padx=10, pady=(0, 10))

        def save_new_dish():
            name = name_entry.get().strip()
            price = price_entry.get().strip()
            ingredients = ingredients_text.get('1.0', 'end-1c').strip()
            status = combobox.get().strip()

            if not name or not price or not ingredients or not status:
                messagebox.showwarning("Ошибка", "Все поля должны быть заполнены!")
                return

            try:
                price = float(price)
            except ValueError:
                messagebox.showwarning("Ошибка", "Цена должна быть числом!")
                return
        # Добавляем новое блюдо
            new_dish = {
                'id': self.next_id,
                'name': name,
                'price': price,
                'ingredients': ingredients,
                'status': status}
            self.dishes.append(new_dish)
            self.next_id += 1
        # Сохраняем и обновляем отображение
            self.save_data()
            add_window.destroy()
            self.update_menu_display()
            messagebox.showinfo("Успех", "Блюдо добавлено!")

        ttk.Button(add_window, text="Добавить", command=save_new_dish).pack(pady=10)

    def save_data(self):
        try:
    # Создаем DataFrame и сохраняем в Excel
            df = pd.DataFrame(self.dishes)
            df.to_excel(self.current_file, index=False)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {str(e)}")

    def delete_dish(self, dish_id):
    # Удаляем блюдо из списка
        self.dishes = [dish for dish in self.dishes if dish['id'] != dish_id]
    # Сохраняем и обновляем отображение
        self.save_data()
        self.update_menu_display()
        messagebox.showinfo("Успех", "Блюдо удалено!")

    def init_settings_section(self):
    # Заголовок раздела настроек
        ttk.Label(
            self.settings_section,
            text="Настройки ресторана",
            font=('Arial', 14, 'bold')
        ).pack(pady=20)
        menu_setting = ttk.LabelFrame(self.settings_section)
        menu_setting.pack(side='left', expand=True,anchor="n")
    # Текущий файл
        ttk.Label(menu_setting, text="Текущий файл меню:").pack(pady=(10, 0))
        if self.current_file is None:
            self.file_label = ttk.Label(menu_setting, text= "Файл не загружен", foreground='red')
        else:
            self.file_label = ttk.Label(menu_setting, text= self.current_file, foreground= 'green')
        self.file_label.pack(pady=(0, 20))
    # Кнопка выбора файла
        ttk.Button(menu_setting, text="Выбрать другой файл", command=self.sel_men_f).pack(pady=10)
    # Кнопка создания нового файла
        ttk.Button(menu_setting, text="Создать новый файл", command=self.create_file_m).pack(pady=10)

        history_setting = ttk.LabelFrame(self.settings_section)
        history_setting.pack(side='left',expand=True, anchor="n")

        ttk.Label(history_setting, text="Текущий файл заказов:").pack(pady=(10, 0))
        if self.current_history_file is None:
            self.file_h_label = ttk.Label(history_setting, text="Файл не загружен", foreground='red')
        else:
            self.file_h_label = ttk.Label(history_setting, text=self.current_history_file, foreground='green')
        self.file_h_label.pack(pady=(0, 20))
        # Кнопка выбора файла
        ttk.Button(history_setting, text="Выбрать другой файл", command=self.sel_his_f).pack(pady=10)
        # Кнопка создания нового файла
        ttk.Button(history_setting, text="Создать новый файл", command=self.create_file_h).pack(pady=10)

    def sel_men_f(self):
        self.select_file("menu")
    def sel_his_f(self):
        self.select_file("his")
    def create_file_m(self):
        self.create_new_file("menu")
    def create_file_h(self):
        self.create_new_file("his")

    def select_file(self, name):
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if file_path:
            if name == "menu":
                self.current_file = file_path
                self.file_label.config(text=self.current_file, foreground= 'green')
                self.load_men_data()
            else:
                self.current_history_file = file_path
                self.file_h_label.config(text=self.current_history_file, foreground='green')
                self.load_order_history()

    def create_new_file(self, name):
        file_path = filedialog.asksaveasfilename(
            title="Создать новый файл меню",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")])
        if file_path:
    # Создаем пустую таблицу
            wb = Workbook()
            ws = wb.active
            if name == "menu": ws.append(["id", "name", "price", "ingredients","status"])
            else: ws.append(["id", "time", "table", "items", "total", "status"])
            wb.save(file_path)
            if name == "menu":
                self.current_file = file_path
                self.file_label.config(text=self.current_file, foreground= 'green')
                self.dishes = []
                self.next_id = 1
                self.update_menu_display()
            else:
                self.current_history_file = file_path
                self.file_h_label.config(text=self.current_history_file, foreground='green')
                self.history = []
                self.nexth_id = 1
                #self.update_menu_display()
            messagebox.showinfo("Успех", f"Новый файл создан: {file_path}")

    def load_men_data(self):
        try:
            if os.path.exists(self.current_file):
    # Читаем данные из Excel
                df = pd.read_excel(self.current_file)
    # Проверяем структуру файла
                if not {'id', 'name', 'price', 'ingredients','status'}.issubset(df.columns):
                    raise ValueError("Неверная структура файла")
    # Преобразуем в список словарей
                self.dishes = df.to_dict('records')
                self.next_id = max(dish['id'] for dish in self.dishes) + 1 if self.dishes else 1
        except Exception as e:
            messagebox.showwarning("Ошибка", f"Не удалось загрузить файл: {str(e)}. Создайте новый.")
            self.current_file = None
            self.file_label.config(text = "Файл не загружен", foreground='red')

        self.update_menu_display()

    def init_connection_section(self):
    # Заголовок раздела
        ttk.Label(
            self.connection_section,
            text="Подключение к другим приложениям",
            font=('Arial', 14, 'bold')
        ).pack(pady=20)

        pos_frame = ttk.Frame(self.connection_section)
        pos_frame.pack(padx=10, pady=5)
    # Фрейм для настроек сервера
        server_frame = ttk.LabelFrame(pos_frame, text="Настройки сервера")
        server_frame.pack(side='left', fill='x', padx=10, pady=5)

        ttk.Label(server_frame, text="IP сервера:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(server_frame, text=f"{self.get_local_ip()}").grid(row=0, column=1, padx=5, pady=5, sticky='we')

        ttk.Label(server_frame, text="Порт сервера:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.port_entry = ttk.Entry(server_frame)
        self.port_entry.insert(0, str(self.port))
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')

        self.toggle_server_btn = ttk.Button(
            server_frame,
            text="Запустить сервер",
            command=self.toggle_server)
        self.toggle_server_btn.grid(row=2, column=0, columnspan=2, pady=5)

        self.server_status = ttk.Label(server_frame, text="Сервер: выключен", foreground='red')
        self.server_status.grid(row=3, column=0, columnspan=2, pady=5)
    #Подключение к кухне
        pod_frame = ttk.LabelFrame(pos_frame, text="Подключение к кухне")
        pod_frame.pack(side='right', fill='x', padx=10, pady=5)

        host_frame = ttk.Frame(pod_frame)
        host_frame.pack(fill='x', padx=20, pady=5)
        ttk.Label(host_frame, text="IP кухни:").pack(side='left')
        self.host_k_entry = ttk.Entry(host_frame)
        self.host_k_entry.insert(0, self.k_host)
        self.host_k_entry.pack(side='left', expand=True, fill='x', padx=5)
    # Настройки порта
        port_frame = ttk.Frame(pod_frame)
        port_frame.pack(fill='x', padx=20, pady=5)
        ttk.Label(port_frame, text="Порт кухни:\n (отличный от сервера)").pack(side='left')
        self.port_k_entry = ttk.Entry(port_frame)
        self.port_k_entry.insert(0, str(self.k_port))
        self.port_k_entry.pack(side='left', expand=True, fill='x', padx=5)

    # Кнопка сохранения настроек
        ttk.Button(
            pod_frame,
            text="Сохранить настройки",
            command=self.save_settings
        ).pack(pady=1, padx=20, fill='x')

        self.connection_status = ttk.Label(
            pod_frame,
            text="Не подключено",
            foreground='red'
        )
        self.connection_status.pack(pady = 5)

    # Лог событий
        log_frame = ttk.LabelFrame(self.connection_section, text="Лог подключений")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=10, state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text['yscrollcommand'] = scrollbar.set

    def get_local_ip(self):
    # Получает локальный IP-адрес устройства в сети
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Не удалось определить"

    def save_settings(self):
    # Сохраняем настройки подключения
        try:
            self.k_host = self.host_k_entry.get()
            self.k_port = int(self.port_k_entry.get())
            self.connection_status.config(text="Настройки сохранены", foreground='green')
        except ValueError:
            self.connection_status.config(text="Неверный порт", foreground='red')
            messagebox.showerror("Ошибка", "Порт должен быть числом!")

    def toggle_server(self):
        if self.listening:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        try:
            self.port = int(self.port_entry.get())

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)

            self.listening = True
            self.toggle_server_btn.config(text="Остановить сервер")
            self.server_status.config(text="Сервер: работает", foreground='green')
            self.log_message(f"Сервер запущен на {self.host}:{self.port}")
    # Запускаем поток для прослушивания подключений
            server_thread = threading.Thread(target=self.listen_for_connections, daemon=True)
            server_thread.start()

        except Exception as e:
            self.log_message(f"Ошибка запуска сервера: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить сервер: {str(e)}")

    def stop_server(self):
        try:
            self.listening = False
            if self.server_socket:
                self.server_socket.close()
            if self.client_socket:
                self.client_socket.close()

            self.toggle_server_btn.config(text="Запустить сервер")
            self.server_status.config(text="Сервер: выключен", foreground='red')
            self.log_message("Сервер остановлен")

        except Exception as e:
            self.log_message(f"Ошибка остановки сервера: {str(e)}")

    def listen_for_connections(self):
    # Обрабатываем входящие подключения"""
        while self.listening:
            try:
                self.client_socket, addr = self.server_socket.accept()
                self.log_message(f"Подключение установлено с {addr}")

                data = self.client_socket.recv(2048).decode()
                if data == "REQUEST_MENU_DATA":
    # Отправляем меню
                    self.send_menu(self.client_socket)
                    self.log_message("Меню отправлено клиенту")

                elif data == "REQUEST_HISTORY_DATA":
                    self.send_history(self.client_socket)
                    self.log_message("История отправлена клиенту")

                elif data == "SEND_ORDER_EXCEL":
                    self.client_socket.send(b"READY")
                    order = self.receive_order(self.client_socket)
                    self.log_message("Получили заказ")
                    self.save_in_history(order)

                self.client_socket.close()

            except Exception as e:
                if self.listening:
                    self.log_message(f"Ошибка: {str(e)}")

    def send_menu(self, client_socket):
        try:
            file_size = len(json.dumps(self.dishes).encode('utf-8'))
            client_socket.sendall(str(file_size).encode())
    # Ждем подтверждения от клиента
            ack = client_socket.recv(1024).decode()
            print(ack)
            if ack != "READY":
                raise Exception("Клиент не готов к получению файла")
            client_socket.send(json.dumps(self.dishes).encode('utf-8'))

        except Exception as e:
            self.log_message(f"Ошибка отправки файла: {str(e)}")
            raise

    def send_history(self, client_socket):
        try:
            history = self.sort_order()
            file_size = len(json.dumps(history).encode('utf-8'))
            client_socket.sendall(str(file_size).encode())
    # Ждем подтверждения от клиента
            ack = client_socket.recv(1024).decode()
            if ack != "READY":
                raise Exception("Клиент не готов к получению файла")
            client_socket.send(json.dumps(history).encode('utf-8'))

        except Exception as e:
            self.log_message(f"Ошибка отправки файла: {str(e)}")
            raise

    def send_order(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.k_host, self.k_port))
                s.sendall(b"SEND_ORDER_DATA")
                response = s.recv(1024).decode()
                if response != "READY": raise Exception("Ошибка подтверждения")
                history = self.sort_order()
                file_size = len(json.dumps(history).encode('utf-8'))
                s.sendall(str(file_size).encode())
    # Ждем подтверждения от клиента
                ack = s.recv(1024).decode()
                if ack != "READY": raise Exception("Клиент не готов к получению файла")
                s.send(json.dumps(history).encode('utf-8'))
        except Exception as e:
            self.log_message(f"Ошибка отправки файла: {str(e)}")

    def sort_order(self):
        history = []
        df = pd.read_excel(self.current_history_file)
        dg = df[df['status'] == 'Готовится']
        for item in dg.to_dict('records'):
            item['items'] = json.loads(item['items'])
            history.append(item)
        return history

    def receive_order(self, client_socket):
        file_size = int(client_socket.recv(1024).decode())
        self.log_message("Получили размер")
        client_socket.send(b"READY")
        # Получаем данные файла
        received_data = b''
        while len(received_data) < file_size:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            received_data += chunk
        # Декодируем
        return json.loads(received_data)

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.config(state='disabled')
        self.log_text.see('end')

    def init_order_history_section(self):
    # Создаем раздел истории заказов
        history_frame = ttk.LabelFrame(self.order_history_section)
        history_frame.pack(fill='both',expand=True, padx=10, pady=5)
    # Делаем таблицу для отображения заказов
        self.orders_tree = ttk.Treeview(
            history_frame,
            columns=('id', 'time', 'table', 'dishes', 'total', 'status'),
            show='headings')
    # Настройка столбцов
        self.orders_tree.heading('id', text='ID')
        self.orders_tree.column('id', width=20, minwidth=20)
        self.orders_tree.heading('time', text='Время')
        self.orders_tree.column('time', width=100, minwidth=100)
        self.orders_tree.heading('table', text='Столик')
        self.orders_tree.column('table', width=60, minwidth=60)
        self.orders_tree.heading('dishes', text='Блюда')
        self.orders_tree.heading('total', text='Сумма')
        self.orders_tree.column('total', width=60, minwidth=60)
        self.orders_tree.heading('status', text='Статус')
        self.orders_tree.column('status', width=100, minwidth=100)

        self.orders_tree.pack(fill='both', expand=True, padx=5, pady=5)
    # Кнопка обновления
        ttk.Button(
            history_frame,
            text="Обновить историю",
            command=self.update_orders_display).pack(pady=5, fill='x')

    def update_orders_display(self):
    # Обновляем отображение истории заказов
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        history = self.load_order_history()
        for order in reversed(history):
            dishes_text = ", ".join([f"{item['name']} x{item['quantity']}" for item in order['items']])
            self.orders_tree.insert('', 'end', values=(
                order['id'],
                order['time'],
                order['table'],
                dishes_text,
                f"{order['total']} ₽",
                order['status']))

    def load_order_history(self):
    # Загружаем историю заказов из Excel
        if os.path.exists(self.current_history_file):
            try:
                df = pd.read_excel(self.current_history_file)
                if not {'time', 'table', 'items', 'total','status', 'id'}.issubset(df.columns):
                    raise ValueError("Неверная структура файла")
                history = []
                self.nexth_id = 0
                for item in df.to_dict('records'):
                    item['items'] = json.loads(item['items'])
                    self.nexth_id = max(self.nexth_id,item['id'])
                    history.append(item)
                self.nexth_id += 1
                return history

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка обработки истории: {str(e)}")
                self.current_history_file = None
                self.file_h_label.config(text="Файл не загружен", foreground='red')
        return []

    def save_in_history(self,order):
        try:
    # Создаем DataFrame и сохраняем в Excel
            df = pd.read_excel(self.current_history_file)
            history = df.to_dict('records')
            if order['status'] == 'Готовится':
                order['id'] = self.nexth_id
                history.append(order)
                df = pd.DataFrame(history)
                self.nexth_id += 1
            else:
                id = order['id']
                df = pd.DataFrame(history)
                df.loc[df['id'] == id, 'status'] = 'Выдан'

            df.to_excel(self.current_history_file, index=False)
            if self.k_host: self.send_order()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {str(e)}")

    def show_connection_section(self):
        self.show_section("con")
    def show_order_history_section(self):
        self.show_section("ord")
    def show_menu_section(self):
        self.show_section("men")
    def show_settings_section(self):
        self.show_section("set")
    def show_section(self,name):
        if name == "beg": self.settings_section.pack(fill='both', expand=True)
        elif (self.current_file is None) or (self.current_history_file is None):
            messagebox.showerror("Внимание", "Для начала загрузите или создайте новые файлы.")
        else:
            if name == "men":
                self.menu_section.pack(fill='both', expand=True)
                self.update_menu_display()
            else: self.menu_section.pack_forget()
            if name == "con": self.connection_section.pack(fill='both', expand=True)
            else: self.connection_section.pack_forget()
            if name == "ord": self.order_history_section.pack(fill='both', expand=True)
            else: self.order_history_section.pack_forget()
            if name == "set": self.settings_section.pack(fill='both', expand=True)
            else: self.settings_section.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = Server(root)
    root.mainloop()
