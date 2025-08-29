import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json


class DishOrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Кухня")
        self.root.geometry("1000x700")  # Вертикальный формат
    # Настройки подключения
        self.host = '0.0.0.0'
        self.port = 5051
        self.server_socket = None
        self.client_socket = None
        self.listening = False
    # Загружаем историю заказов
        self.order_history = []
    # Создание интерфейса
        self.create_widgets()
        self.show_settings_section()

        self.style = ttk.Style()
        self.style.configure('Order.TFrame', background='white')

    def create_widgets(self):
    # Главный контейнер
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True)
    # Контейнер для контента
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill='both', expand=True)
    # Создаем разделы
        self.init_order_section()
        self.init_settings_section()
    # Нижняя панель навигации
        self.nav_frame = ttk.Frame(self.main_container, height=40)
        self.nav_frame.pack(fill='x', side='bottom')
    # Кнопки навигации
        self.order_btn = ttk.Button(
            self.nav_frame,
            text="🛒Заказы",
            style='Nav.TButton',
            command=self.show_order_section)
        self.order_btn.pack(side='left', expand=True, fill='x')

        self.settings_btn = ttk.Button(
            self.nav_frame,
            text="⚙️Настройки",
            style='Nav.TButton',
            command=self.show_settings_section)
        self.settings_btn.pack(side='left', expand=True, fill='x')

    def init_order_section(self):
    # Основной фрейм с прокруткой
        self.order_section = ttk.Frame(self.content_frame)
        self.history_canvas = tk.Canvas(self.order_section)
        self.history_scrollbar = ttk.Scrollbar(self.order_section, orient='vertical',
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

    def create_order_frame(self, order,n):
        order_frame = ttk.Frame(self.history_scrollable_frame, style='Order.TFrame', relief='raised')
        order_frame.grid(row=n%3, column=n//3, sticky='nsew', pady=5, padx=5)
    # Заголовок с номером столика и временем
        header_frame = ttk.Frame(order_frame, style='Order.TFrame')
        header_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(header_frame, text=f"Столик №{order['table']}",
            font=('Arial', 15, 'bold'), background='white'
        ).pack(side='left')

        ttk.Label(header_frame, text=order['time'],
            font=('Arial', 12), background='white'
        ).pack(side='right')
    # Список блюд
        dishes_frame = ttk.Frame(order_frame, style='Order.TFrame')
        dishes_frame.pack(fill='x', padx=10, pady=2)

        for item in order['items']:
            dish_frame = ttk.Frame(dishes_frame, style='Order.TFrame')
            dish_frame.pack(fill='x', pady=2)

            ttk.Label(dish_frame, text=f"{item['name']} x {item['quantity']}",
                font=('Arial', 25), background='white'
            ).pack(side='left')

    def update_history_display(self):
    # Очищаем текущие фреймы
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
    # Добавляем только заказы со статусом "Готовится"
        for i, order in enumerate(self.order_history):
            self.create_order_frame(order, i)

    def init_settings_section(self):
        self.connection_section = ttk.Frame(self.content_frame,)
        # Заголовок раздела
        ttk.Label(
            self.connection_section,
            text="Подключение к другим приложениям",
            font=('Arial', 14, 'bold')
        ).pack(pady=20)
        # Фрейм для настроек сервера
        server_frame = ttk.LabelFrame(self.connection_section, text="Настройки сервера")
        server_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(server_frame, text="IP кухни:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(server_frame, text=f"{self.get_local_ip()}").grid(row=0, column=1, padx=5, pady=5, sticky='we')

        ttk.Label(server_frame, text="Порт кухни:\n (отличный от сервера)").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.port_entry = ttk.Entry(server_frame)
        self.port_entry.insert(0, str(self.port))
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')

        self.server_status = ttk.Label(server_frame, text="Кухня: выключена", foreground='red')
        self.server_status.grid(row=2, column=0, columnspan=2, pady=5)

        self.toggle_server_btn = ttk.Button(
            server_frame,
            text="Запустить кухню",
            command=self.toggle_server)
        self.toggle_server_btn.grid(row=3, column=0, columnspan=2, pady=5)

    def toggle_server(self):
        if self.listening:
            self.stop_server()
        else:
            self.start_server()
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

    def start_server(self):
        try:
            self.port = int(self.port_entry.get())

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)

            self.listening = True
            self.toggle_server_btn.config(text="Остановить кухню")
            self.server_status.config(text="Кухня: работает", foreground='green')
    # Запускаем поток для прослушивания подключений
            server_thread = threading.Thread(target=self.listen_for_connections, daemon=True)
            server_thread.start()

        except Exception as e:
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

        except Exception as e:
            messagebox.showwarning("Ошибка", f"{str(e)}")

    def listen_for_connections(self):
    # Обрабатываем входящие подключения"""
        while self.listening:
            try:
                self.client_socket, addr = self.server_socket.accept()

                data = self.client_socket.recv(2048).decode()
                if data == "SEND_ORDER_DATA":
    #Получаем заказы
                    self.client_socket.send(b"READY")
                    # Получаем размер файла
                    file_size = int(self.client_socket.recv(1024).decode())
                    self.client_socket.sendall(b"READY")
                    # Получаем данные файла
                    received_data = b''
                    while len(received_data) < file_size:
                        chunk = self.client_socket.recv(4096)
                        if not chunk:
                            break
                        received_data += chunk
                    # Декодируем
                    self.order_history = json.loads(received_data)
                    self.update_history_display()

                self.client_socket.close()
            except Exception as e:
                messagebox.showwarning("Ошибка", f"{str(e)}")

    def receive_order(self):
    # Получаем файл от сервера
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

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
                self.order_history = json.loads(received_data)

        except Exception as e:
            raise Exception(f"Ошибка получения файла: {e}")

    def show_order_section(self):
        self.connection_section.pack_forget()
        self.order_section.pack(fill='both', expand=True)
        self.update_nav_buttons('order')

    def show_settings_section(self):
        self.order_section.pack_forget()
        self.connection_section.pack(fill='both', expand=True)
        self.update_nav_buttons('settings')

    def update_nav_buttons(self, active_section):
        self.order_btn.state(['!pressed'])
        self.settings_btn.state(['!pressed'])
        if active_section == 'order':
            self.order_btn.state(['pressed'])
        elif active_section == 'settings':
            self.settings_btn.state(['pressed'])

if __name__ == "__main__":
    root = tk.Tk()
    app = DishOrderApp(root)
    root.mainloop()
