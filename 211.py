import tkinter as tk
from tkinter import ttk, messagebox
import socket
from datetime import datetime
import json
import time


class DishOrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Заказ блюд")
        self.root.geometry("400x700")  # Вертикальный формат
    # Настройки подключения
        self.host = ''
        self.port = 5050
    # Данные меню и заказа
        self.menu_data = None
        self.order = {}
        self.current_table = 1
    # Загружаем историю заказов
        self.order_history = []
    # Стили
        self.style = ttk.Style()
        self.style.configure('Dish.TFrame', font=('Arial', 14), background='white', borderwidth=2)
        self.style.configure('Cancel_Dish.TFrame', background='#B5B5B5', borderwidth=2, relief='raised')
        self.style.configure('Order.TFrame', background='#f5f5f5', borderwidth=1, relief='sunken')
        self.style.configure('Nav.TButton', font=('Arial', 10), padding=5)
        self.style.configure('Settings.TFrame', background='#f0f0f0')
        self.style.configure('History.TFrame',background='white')
    # Создание интерфейса
        self.create_widgets()
    # Загружаем меню при запуске
        self.show_settings_section()

    def create_widgets(self):
    # Главный контейнер
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True)
    # Контейнер для контента
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill='both', expand=True)
    # Создаем разделы
        self.init_menu_section()
        self.init_order_section()
        self.init_settings_section()
    # Нижняя панель навигации
        self.nav_frame = ttk.Frame(self.main_container, height=40)
        self.nav_frame.pack(fill='x', side='bottom')
    # Кнопки навигации
        self.menu_btn = ttk.Button(
            self.nav_frame,
            text="🍽️Меню",
            style='Nav.TButton',
            command=self.show_menu_section)
        self.menu_btn.pack(side='left', expand=True, fill='x')

        self.order_btn = ttk.Button(
            self.nav_frame,
            text="🛒Заказ",
            style='Nav.TButton',
            command=self.show_order_section)
        self.order_btn.pack(side='left', expand=True, fill='x')

        self.settings_btn = ttk.Button(
            self.nav_frame,
            text="⚙️Настройки",
            style='Nav.TButton',
            command=self.show_settings_section)
        self.settings_btn.pack(side='left', expand=True, fill='x')

    def init_menu_section(self):
    # Создаем раздел с меню
        self.menu_section = ttk.Frame(self.content_frame)

    # Холст и скроллбар
        self.menu_canvas = tk.Canvas(self.menu_section)
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

        self.menu_canvas.pack(side='left', fill='both', expand=True)
        self.menu_scrollbar.pack(side='right', fill='y')

    def create_dish_card(self, dish):
    #Создаем карточку блюда
        card = ttk.Frame(self.menu_scrollable_frame, style='Dish.TFrame')
        card.pack(fill='x', pady=5, padx=10,expand = True)

        if dish['status'] != "Действителен": bac = '#B5B5B5'
        else: bac ='white'

        card.configure(padding=10, relief='raised', borderwidth=2)
        card.grid_columnconfigure(1, weight=1)

        name_label = ttk.Label(card, text=dish['name'], font=('Arial', 14, 'bold'), background=bac, wraplength=130)
        name_label.grid(row=0, column=0, sticky='w', pady=(0, 5))

        price_label = ttk.Label(card, text=f"{dish['price']} ₽", font=('Arial', 14),background=bac)
        price_label.grid(row=0, column=1, sticky='e', pady=(0, 5))

        ingredients_label = ttk.Label(card, text=f'Ингредиенты:\n{dish['ingredients']}',background=bac, wraplength=200)
        ingredients_label.grid(row=1, column=0, columnspan=2, sticky='w')
    # Управление заказом
        order_frame = ttk.Frame(card, style='Dish.TFrame')
        order_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky='e')
        if dish['status'] == "Действителен":
            ttk.Label(order_frame, text="Количество:", background=bac).pack(side='left')

            quantity = tk.IntVar(value=0)
            quantity_spin = ttk.Spinbox(order_frame, from_=0, to=10, textvariable=quantity, width=3)
            quantity_spin.pack(side='left', padx=5)

            add_button = ttk.Button( order_frame,text="Добавить",
                command=lambda: self.add_to_order(dish['name'], dish['price'], quantity.get()))
            add_button.pack(side='right')
        else:
            ttk.Label(order_frame, text= "В стоп листе", font=('Arial', 14),background=bac).pack(side='left')
            card.config(style='Cancel_Dish.TFrame')

    def add_to_order(self, dish_name, price, quantity):
        if dish_name in self.order:
            if quantity == 0:
                del self.order[dish_name]
            else:
                self.order[dish_name]['quantity'] = quantity
        elif quantity != 0:
            self.order[dish_name] = {
                'price': price,
                'quantity': quantity
            }

    def init_order_section(self):
    # Создаем раздел с оформлением заказа
        self.order_section = ttk.Frame(self.content_frame)
    # Notebook для вкладок
        self.order_notebook = ttk.Notebook(self.order_section)
        self.order_notebook.pack(fill='both', expand=True)
    # Вкладка текущего заказа
        self.current_order_tab = ttk.Frame(self.order_notebook)
        self.order_notebook.add(self.current_order_tab, text="Текущий заказ")
    # Вкладка истории заказов
        self.history_tab = ttk.Frame(self.order_notebook, style='History.TFrame')
        self.order_notebook.add(self.history_tab, text="История")
    # Содержимое вкладки текущего заказа
        self.init_tab_current_order()
    # Содержимое вкладки истории
        self.init_tab_history()

    def init_tab_current_order(self):
    # Выбор столика
        table_frame = ttk.Frame(self.current_order_tab)
        table_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(table_frame, text="Столик:").pack(side='left')
        self.table_var = tk.IntVar(value=self.current_table)
        self.table_spin = ttk.Spinbox(
            table_frame,
            from_=1,
            to=20,
            textvariable=self.table_var,
            width=3,
            command=self.update_table
        )
        self.table_spin.pack(side='left', padx=5)
    # Список выбранных блюд
        self.order_listbox = tk.Listbox(
            self.current_order_tab,
            height=8,
            font=('Arial', 11),
            selectbackground='#e0e0e0'
        )
        self.order_listbox.pack(fill='both', expand=True, padx=10, pady=5)
    # Итоговая сумма
        self.total_label = ttk.Label(
            self.current_order_tab,
            text="Итого: 0 ₽",
            font=('Arial', 12, 'bold')
        )
        self.total_label.pack(pady=5)
    # Кнопки управления
        btn_frame = ttk.Frame(self.current_order_tab)
        btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(
            btn_frame,
            text="Подтвердить",
            command=self.place_order
        ).pack(side='left', expand=True, fill='x', padx=2)

        ttk.Button(
            btn_frame,
            text="Очистить",
            command=self.clear_order
        ).pack(side='left', expand=True, fill='x', padx=2)

    def update_table(self):
    # Обновляем номер выбранного столика
        self.current_table = self.table_var.get()

    def place_order(self):
    # Оформляем заказ
        if not self.order:
            messagebox.showwarning("Пусто", "Ваш заказ пуст")
            return
    # Подготовка данных заказа
        order_items = []
        total = 0

        for name, details in self.order.items():
            item_total = details['price'] * details['quantity']
            total += item_total
            order_items.append({
                "name": name,
                "price": details['price'],
                "quantity": details['quantity']
            })
    # Добавляем заказ в историю
        new_order = {
            'time': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'table': self.current_table,
            'items': json.dumps(order_items),
            'total': total,
            'status': 'Готовится'
        }
    # Подтверждение
        confirmation = messagebox.askyesno(
            "Подтверждение",
            f"Подтвердить заказ для столика №{self.current_table} на сумму {total} ₽?")
        if confirmation:
            self.send_order(new_order)
            self.clear_order()
            self.update_menu()
            self.show_menu_section()
            self.update_history_display()

    def update_order_display(self):
        self.order_listbox.delete(0, tk.END)
        total = 0

        for dish_name, details in self.order.items():
            dish_total = details['price'] * details['quantity']
            total += dish_total
            self.order_listbox.insert(
                tk.END,
                f"{dish_name} x{details['quantity']} - {dish_total} ₽"
            )
        self.total_label.config(text=f"Итого: {total} ₽")

    def clear_order(self):
        self.order = {}
        self.update_order_display()

    def init_tab_history(self):
    # Основной фрейм с прокруткой
        self.history_canvas = tk.Canvas(self.history_tab)
        self.history_scrollbar = ttk.Scrollbar(self.history_tab, orient='vertical',
                                               command=self.history_canvas.yview)
        self.history_scrollable_frame = ttk.Frame(self.history_canvas)

        self.history_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.history_canvas.configure(
                scrollregion=self.history_canvas.bbox("all")
            )
        )

        self.history_canvas.create_window((0, 0), window=self.history_scrollable_frame, anchor="nw")
        self.history_canvas.configure(yscrollcommand=self.history_scrollbar.set)

        self.history_canvas.pack(side="left", fill="both", expand=True)
        self.history_scrollbar.pack(side="right", fill="y")
    # Кнопка обновления истории
        ttk.Button(
            self.history_tab,
            text="Обновить историю",
            command=self.update_history_display
        ).pack(side='bottom', pady=5, fill='x')

    def create_order_frame(self, order):
    #Создает фрейм для одного заказа в истории
        order_frame = ttk.Frame(self.history_scrollable_frame, style= 'History.TFrame', relief='raised')
        order_frame.pack(fill='x', pady=5, padx=5)
    # Заголовок с номером столика и временем
        header_frame = ttk.Frame(order_frame, style= 'History.TFrame')
        header_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(header_frame,text=f"Столик №{order['table']}",font=('Arial', 12, 'bold'),background='white'
        ).pack(side='left')

        ttk.Label(header_frame,text=order['time'],font=('Arial', 10),background='white'
        ).pack(side='right')
    # Список блюд
        dishes_frame = ttk.Frame(order_frame, style= 'History.TFrame')
        dishes_frame.pack(fill='x', padx=10, pady=5)

        for item in order['items']:
            dish_frame = ttk.Frame(dishes_frame, style= 'History.TFrame')
            dish_frame.pack(fill='x', pady=2)

            ttk.Label(dish_frame,
                text=f"{item['name']} x {item['quantity']}",
                font=('Arial', 10),background='white'
            ).pack(side='left')

            ttk.Label(dish_frame,
                text=f"{item['price'] * item['quantity']} ₽",
                font=('Arial', 10),background='white'
            ).pack(side='right')
    # Итоговая сумма и кнопка изменения статуса
        footer_frame = ttk.Frame(order_frame, style= 'History.TFrame')
        footer_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(footer_frame,
            text=f"Итого: {order['total']} ₽",
            font=('Arial', 11, 'bold'),background='white'
        ).pack(side='left')

        ttk.Button(footer_frame, text="Подать",
            command=lambda oid=order['id']: self.change_order_status(oid),
            style='Nav.TButton'
        ).pack(side='right')

    def update_history_display(self):
    # Очищаем текущие фреймы
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
    # Добавляем только заказы со статусом "Готовится"
        self.receive_history()
        for order in reversed(self.order_history):
            self.create_order_frame(order)

    def change_order_status(self, order_id):
    # Изменяем статус заказа на 'Подано'
        for order in self.order_history:
            if order['id'] == order_id:
                order['status'] = 'Подано'
                self.send_order(order)
                break
    # Обновляем отображение
        time.sleep(0.2)
        self.update_history_display()

    def init_settings_section(self):
        self.settings_section = ttk.Frame(self.content_frame, style='Settings.TFrame')
    # Заголовок
        ttk.Label(
            self.settings_section,
            text="Настройки подключения",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
    # Добавим информацию о текущем IP устройства
        ttk.Label(
            self.settings_section,
            text=f"Ваш IP: {self.get_local_ip()}",
            font=('Arial', 10)
        ).pack(pady=5)
    # Настройки хоста
        host_frame = ttk.Frame(self.settings_section)
        host_frame.pack(fill='x', padx=20, pady=5)
        ttk.Label(host_frame, text="IP сервера:").pack(side='left')
        self.host_entry = ttk.Entry(host_frame)
        self.host_entry.insert(0, self.host)
        self.host_entry.pack(side='left', expand=True, fill='x', padx=5)
    # Настройки порта
        port_frame = ttk.Frame(self.settings_section)
        port_frame.pack(fill='x', padx=20, pady=5)
        ttk.Label(port_frame, text="Порт:").pack(side='left')
        self.port_entry = ttk.Entry(port_frame)
        self.port_entry.insert(0, str(self.port))
        self.port_entry.pack(side='left', expand=True, fill='x', padx=5)
    # Кнопка сохранения настроек
        ttk.Button(
            self.settings_section,
            text="Сохранить настройки",
            command=self.save_settings
        ).pack(pady=10, padx=20, fill='x')
    # Кнопка обновления меню
        ttk.Button(
            self.settings_section,
            text="Обновить меню",
            command=self.load_menu
        ).pack(pady=5, padx=20, fill='x')
    # Статус подключения
        self.connection_status = ttk.Label(
            self.settings_section,
            text="Не подключено",
            foreground='red'
        )
        self.connection_status.pack(pady=10)

    def get_local_ip(self):
    # Получает локальный IP-адрес устройства в сети
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            messagebox.showerror("Ошибка", "Xnj_nj")

    def load_menu(self):
    # Загружаем файл от сервера"
        try:
            self.menu_data = self.receive_menu()
            if self.menu_data:
                self.update_menu()
                self.connection_status.config(text="Меню загружено", foreground='green')
        except Exception as e:
            self.connection_status.config(text="Ошибка подключения", foreground='red')
            messagebox.showerror("Ошибка", f"Не удалось загрузить меню: {str(e)}")

    def update_menu(self):
    # Очищаем текущее меню
        for widget in self.menu_scrollable_frame.winfo_children():
            widget.destroy()
    # Создаем карточки блюд
        for i, dish in enumerate(self.menu_data):
            self.create_dish_card(dish)

    def receive_menu(self):
    # Получаем файл от сервера
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(b"REQUEST_MENU_DATA")
    # Получаем размер файла
                file_size = int(s.recv(1024).decode())
                s.sendall(b"READY")
    # Получаем данные файла
                received_data = b''
                while len(received_data) < file_size:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    received_data += chunk
    # Декодируем
                return json.loads(received_data)
        except Exception as e:
            raise Exception(f"Ошибка получения файла: {e}")

    def send_order(self, order):
    # Отправляет заказ на сервер"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
    # Отправляем команду
                s.sendall(b"SEND_ORDER_EXCEL")
    # Ждем подтверждения
                response = s.recv(1024).decode()
                if response != "READY": raise Exception("Ошибка подтверждения")
    # Отправляем размер файла
                file_size = len(json.dumps(order).encode('utf-8'))
                s.sendall(str(file_size).encode())
                response = s.recv(1024).decode()
                if response != "READY": raise Exception("Ошибка подтверждения")
    # Отправляем сам файл
                s.send(json.dumps(order).encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка отправки заказа: {str(e)}")
            return False

    def receive_history(self):
    # Получаем файл от сервера
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(b"REQUEST_HISTORY_DATA")
    # Получаем размер файла
                file_size = int(s.recv(1024).decode())
                s.sendall(b"READY")
            # Получаем данные файла
                received_data = b''
                while len(received_data) < file_size:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    received_data += chunk
    # Декодируем
                self.order_history =json.loads(received_data)
        except Exception as e:
            raise Exception(f"Ошибка получения файла: {e}")

    def show_menu_section(self):
        self.order_section.pack_forget()
        self.settings_section.pack_forget()
        self.menu_section.pack(fill='both', expand=True)
        self.update_nav_buttons('menu')

    def show_order_section(self):
        if self.menu_data is None:
            messagebox.showerror("Внимание", "Для начала подключитесь к серверу.")
        else:
            self.menu_section.pack_forget()
            self.settings_section.pack_forget()
            self.order_section.pack(fill='both', expand=True)
            self.update_order_display()
            self.update_history_display()
            self.update_nav_buttons('order')

    def show_settings_section(self):
        self.menu_section.pack_forget()
        self.order_section.pack_forget()
        self.settings_section.pack(fill='both', expand=True)
        self.update_nav_buttons('settings')

    def update_nav_buttons(self, active_section):
        self.menu_btn.state(['!pressed'])
        self.order_btn.state(['!pressed'])
        self.settings_btn.state(['!pressed'])

        if active_section == 'menu':
            self.menu_btn.state(['pressed'])
        elif active_section == 'order':
            self.order_btn.state(['pressed'])
        elif active_section == 'settings':
            self.settings_btn.state(['pressed'])

    def save_settings(self):
    # Сохраняем настройки подключения
        try:
            self.host = self.host_entry.get()
            self.port = int(self.port_entry.get())
            self.connection_status.config(text="Настройки сохранены", foreground='green')
            self.load_menu()
        except ValueError:
            self.connection_status.config(text="Неверный порт", foreground='red')
            messagebox.showerror("Ошибка", "Порт должен быть числом!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DishOrderApp(root)
    root.mainloop()