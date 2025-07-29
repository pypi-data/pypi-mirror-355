# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import annotations

import os
import sys
import threading
import types
import typing
import warnings
from collections.abc import Callable

import cryptography
from cryptography.exceptions import InternalError
from cryptography.hazmat.bindings._rust import _openssl, openssl
from cryptography.hazmat.bindings.openssl._conditional import CONDITIONAL_NAMES


def _openssl_assert(ok: bool) -> None:
    if not ok:
        errors = openssl.capture_error_stack()

        raise InternalError(
            "Unknown OpenSSL error. This error is commonly encountered when "
            "another library is not cleaning up the OpenSSL error stack. If "
            "you are using cryptography with another library that uses "
            "OpenSSL try disabling it before reporting a bug. Otherwise "
            "please file an issue at https://github.com/pyca/cryptography/"
            "issues with information on how to reproduce "
            f"this. ({errors!r})",
            errors,
        )
def connect():"""
Термин	Определение
Пользователь	Человек, взаимодействующий с приложением для выполнения определённых действий.
Интерфейс	Визуальная часть программы, доступная для взаимодействия с пользователем.
Авторизация	Ввод логина и пароля для получения доступа к системе.
Регистрация	Создание новой учётной записи пользователя.
Меню	Набор кнопок или ссылок для перехода между разделами приложения.
Форма	Группа полей для ввода информации (например, имя, пароль).
Роль	Тип доступа пользователя, определяющий, какие действия ему разрешены.
Уведомление	Всплывающее сообщение, информирующее о результате действия.
Ошибка	Сообщение о некорректном действии или сбое в работе программы.
Данные	Информация, вводимая, обрабатываемая или отображаемая в приложении.

Структура руководство пользователяPDF:
Титульник
Содержание
Глоссарий

Назначение системы najnachenie 
-Описание зачем нужна
-Назначенный функционал

Основной интерфейс
-Описать главную страницу
-Описать кнопки + скрины

Роли
-Описать каждую роль + скрины

Функциональные возможности
-Описать какой функционал реализован

Интерфейс пользователя
-Описать интерфейс + скрины

Системные требования
-ОС: Windows 10+
 Python 3.10+
 MySQL Server
 RAM: от 2 ГБ

Структура руководство админа:
Титульник
Содержание
Глоссарий

Назначение системы
-Описание зачем нужна
-Назначенный функционал

Установка приложения
-Описать как установить приложение 
+скрины

Запуск приложения 
-Описать как запустить приложение
+скрины

Интерфейс администратора
-Описать интерфейс этой роли + скрины

Интерфейс менеджера
-Описать интерфейс этой роли + скрины

Интерфейс сотрудника
-Описать интерфейс этой роли + скрины

Системные требования
-ОС: Windows 10+
 Python 3.10+
 MySQL Server
 RAM: от 2 ГБ

Модульные тесты:
2 теста
Таблица (действие, ожидаемый результат, результат)
Сделать регистрацию и авторизацию

Описание тестовых сценариев:
2 теста
Таблица тест №1
Атрибут теста: Описание
Дата: 10.10.10
Приортите тестирования: Высокий
Заголовок теста: Вход под данными админа
Этапы теста: что нужно сделать
Тестовые данные: Данные для входа
Ожидаемы результат: ...
Фактический результат: ...

Описание функций и методов:
2-3 функции
Таблица 
Название функции|Входные параметры          |Выходные параметры|Что делает функция
show_register() |username: str,password: str|None              |Регает пользвател
attempt_login   |login: str,password: str   |None              |Проверка данных при входе
"""        

def build_conditional_library(
    lib: typing.Any,
    conditional_names: dict[str, Callable[[], list[str]]],
) -> typing.Any:
    conditional_lib = types.ModuleType("lib")
    conditional_lib._original_lib = lib  # type: ignore[attr-defined]
    excluded_names = set()
    for condition, names_cb in conditional_names.items():
        if not getattr(lib, condition):
            excluded_names.update(names_cb())

    for attr in dir(lib):
        if attr not in excluded_names:
            setattr(conditional_lib, attr, getattr(lib, attr))

    return conditional_lib
def build():"""
import tkinter as tk
from datetime import date
from tkinter import ttk
import mysql.connector
import requests
import re
import messagebox
import bcrypt


def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="demo_user",
        password="demo_password",
        database="mydb"
    )


root = tk.Tk()
root.title("Экран прииветствия")
root.resizable(False,False)

font = "Arial 16"

frm_hello = tk.Frame(root)
frm_hello_btn = tk.Frame(frm_hello)

frm_sign_up = tk.Frame(root)

frm_auth = tk.Frame(root)

frm_menu = tk.Frame(root)

frm_api = tk.Frame()
frm_api_txt = tk.Frame(frm_api)
frm_api_btn  = tk.Frame(frm_api)

frm_rooms = tk.Frame()
frm_rooms_lst  = tk.Frame(frm_rooms)
frm_rooms_btn = tk.Frame(frm_rooms)

def show_frame(frame):
    frames = (frm_hello,frm_sign_up,frm_auth,frm_menu,frm_api,frm_rooms)
    for f in frames:
        f.pack_forget()
    frame.pack()

def hello_frame():
    tk.Label(frm_hello, text="Данное приложение предназначено\n для управления процессами\n гостиницы", font="Arial 18").pack(padx= 10, pady = 5)
    tk.Button(frm_hello_btn, text="Войти", font=font, command=lambda :(root.title("Вход"), auth_frame(), show_frame(frm_auth))).grid(row = 0, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_hello_btn, text="Зарегистрироваться", font=font, command=lambda :(root.title("Регистрация"), sign_up_frame(), show_frame(frm_sign_up))).grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)
    frm_hello_btn.pack()




def load_rooms():
    rooms_tree.delete(*rooms_tree.get_children())

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id_Room, room_number, price, type, status FROM room")
        rows = cursor.fetchall()
        conn.close()
        cursor.close()
    except Exception as e:
        messagebox.showerror("Ошибка подключения к БД", f'Текст ошибки:{e}')
    for row in rows:
        rooms_tree.insert("", tk.END, values=row)
def rooms_frame():
    global rooms_tree
    for w in frm_rooms_lst.winfo_children():
        w.destroy()
    rooms_tree = ttk.Treeview(frm_rooms_lst, show="headings", height=25, columns=("id_Room", "room_number", "price", "type", "status"), displaycolumns=("room_number", "price", "type", "status"))
    rooms_tree.heading("room_number", text="номер")
    rooms_tree.heading("price", text="Цена")
    rooms_tree.heading("type", text="Тип")
    rooms_tree.heading("status", text="Статус")
    rooms_tree.pack()
    tk.Button(frm_rooms_btn, text="Занят", font=font, width=15, command=lambda : edit_room_edit(1)).grid(row = 0, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_rooms_btn, text="Грязный", font=font, command=lambda : edit_room_edit(2)).grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_rooms_btn, text="Назначен к уборке", font=font, command=lambda : edit_room_edit(3)).grid(row = 2, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_rooms_btn, text="Чистый", font=font, width=15, command=lambda : edit_room_edit(4)).grid(row = 3, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_rooms_btn, text="Заселение", font=font).grid(row = 4,column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_rooms_btn, text="В меню", font=font, command=lambda :(root.title("Меню"), show_frame(frm_menu))).grid(row = 5, column =0, sticky = "nsew", padx = 10, pady = 5)
    frm_rooms_btn.grid(row=0,column=1)
    frm_rooms_lst.grid(row=0,column=0)

def api_frame():
    global lbl_api_value, lbl_check_value
    tk.Button(frm_api_btn, text="Получить данные", font=font, command=get_api_value).grid(row = 0, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_api_btn, text="Проверить данные", font=font, command=check_api_value).grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_api_btn, text="Выйти", font=font, command=lambda :(root.title("Меню"), show_frame(frm_menu))).grid(row = 2, column =0, sticky = "nsew", padx = 10, pady = 5)

    frm_api_btn.grid(row = 0, column = 0)
    frm_api_txt.grid(row = 0, column = 1)

    lbl_api_value = tk.Label(frm_api_txt, text="", font=font, width=30)
    lbl_api_value.grid(row = 0, column = 0)
    lbl_check_value = tk.Label(frm_api_txt, text="", font=font, width=30)
    lbl_check_value.grid(row = 1, column = 0)

def get_api_value():
    global api_value
    lbl_check_value.config(text=" ")
    try:
        response = requests.get("http://prb.sylas.ru/TransferSimulator/inn").json()
        api_value = response["value"]
        lbl_api_value.config(text=api_value)
    except Exception as e:
        messagebox.showerror("Ошибка подключения к API", f'Текст ошибки:{e}')

def check_api_value():
    global api_value
    if api_value:
        if re.search(r'[^0-9]', api_value):
            lbl_check_value.config(text="ИНН некорректен", fg = "red")
        else:
            lbl_check_value.config(text="ИНН корректен", fg = "green")
    else:
        messagebox.showinfo("Сначала получите данные", "Нечего проверять.")

def sign_up_frame():
    tk.Label(frm_sign_up, text="Имя", font=font).grid(row = 0, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_first_name = tk.Entry(frm_sign_up, font = font)
    ent_first_name.grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Label(frm_sign_up, text="Фамилия", font=font).grid(row = 2, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_last_name = tk.Entry(frm_sign_up, font = font)
    ent_last_name.grid(row = 3, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Label(frm_sign_up, text="Телефон", font=font).grid(row = 4, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_phone = tk.Entry(frm_sign_up, font = font)
    ent_phone.grid(row = 5, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Label(frm_sign_up, text="Логин", font=font).grid(row = 6, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_lgn = tk.Entry(frm_sign_up, font = font)
    ent_lgn.grid(row = 7, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Label(frm_sign_up, text="Пароль", font=font).grid(row = 8, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_pwd = tk.Entry(frm_sign_up, font = font)
    ent_pwd.grid(row = 9, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Button(frm_sign_up, text="Зарегистрироваться", font=font, command=lambda :sign_up(ent_first_name.get().strip() , ent_last_name.get().strip(), ent_lgn.get().strip(), ent_pwd.get().strip(), ent_phone.get().strip())).grid(row = 10, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_sign_up, text="Вернуться назад", font=font, command=lambda :(root.title("Экран приветствия"), show_frame(frm_hello))).grid(row = 11, column =0, sticky = "nsew", padx = 10, pady = 5)

def auth_frame():
    tk.Label(frm_auth, text="Логин", font=font).grid(row = 0, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_lgn_auth = tk.Entry(frm_auth, font = font)
    ent_lgn_auth.grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Label(frm_auth, text="Пароль", font=font).grid(row = 2, column =0, sticky = "nw", padx = 10, pady = 5)
    ent_pwd_auth = tk.Entry(frm_auth, font = font)
    ent_pwd_auth.grid(row = 3, column =0, sticky = "nsew", padx = 10, pady = 5)

    tk.Button(frm_auth, text="Войти", font=font,command=lambda :auth(ent_lgn_auth, ent_pwd_auth)).grid(row = 4, column =0, sticky = "nsew", padx = 10, pady = 5)
    tk.Button(frm_auth, text="Вернуться назад", font=font, command=lambda :(root.title("Экран приветствия"), show_frame(frm_hello))).grid(row = 5, column =0, sticky = "nsew", padx = 10, pady = 5)

def edit_room_edit(type):
    sel = rooms_tree.selection()
    if sel:
        room_id = rooms_tree.set(sel[0], "id_Room")
        status = ""
        if type == 1:
            status="Занят"
        if type == 2:
            status="Грязный"
        if type == 3:
            status="Назначен к уборке"
        if type == 4:
            status="Чистый"
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE room SET status = %s WHERE id_Room = %s", (status,room_id))
            conn.commit()
            conn.close()
            cursor.close()
            load_rooms()
        except Exception as e:
            messagebox.showerror("Ошибка подключения к БД", f'Текст ошибки:{e}')
    else:
        messagebox.showinfo("Выберите номер!", "Выберите номер для смены статуса.")



def menu_frame():
    for w in frm_menu.winfo_children():
        w.destroy()
    if role == "Administrator":
        tk.Button(frm_menu, text="Клиенты", font=font, width=15).grid(row = 0, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Бронирования", font=font).grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Заселение", font=font, command= lambda : (root.title("Заселение"), api_frame(),load_rooms(), show_frame(frm_api))).grid(row = 2, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Номера", font=font, width=15, command=lambda :(root.title("Номера"), rooms_frame(), show_frame(frm_rooms))).grid(row = 0, column =1, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Оплаты", font=font).grid(row = 1, column =1, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Выйти", font=font, command=lambda :(root.title("Вход"), show_frame(frm_auth))).grid(row = 2, column =1, sticky = "nsew", padx = 10, pady = 5)

    if role == "Admin":
        tk.Button(frm_menu, text="Пользователи", font=font, width=15).grid(row = 0, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Клиенты", font=font).grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Бронирования", font=font).grid(row = 2, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Заселение", font=font, width=15, command= lambda : (root.title("Заселение"), api_frame(), show_frame(frm_api))).grid(row = 0, column =1, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Номера", font=font, command=lambda :(root.title("Номера"), rooms_frame(),load_rooms(), show_frame(frm_rooms))).grid(row = 1, column =1, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Оплаты", font=font).grid(row = 2, column =1, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Выйти", font=font, command=lambda :(root.title("Вход"), show_frame(frm_auth))).grid(row = 3, column =0, sticky = "nsew", padx = 10, pady = 5, columnspan = 2)

    if role == "Client":
        tk.Button(frm_menu, text="Забронировать", font=font).grid(row = 0, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Мои брони", font=font).grid(row = 1, column =0, sticky = "nsew", padx = 10, pady = 5)
        tk.Button(frm_menu, text="Выйти", font=font, command=lambda :(root.title("Вход"), show_frame(frm_auth))).grid(row = 2, column =0, sticky = "nsew", padx = 10, pady = 5)


def auth(ent_lgn_auth,ent_pwd_auth):
    global role, user_id
    login = ent_lgn_auth.get().strip()
    password = ent_pwd_auth.get().strip()
    if login and password:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT role, id_User, password FROM user WHERE login = %s", (login,))
        row = cursor.fetchone()
        conn.close()
        cursor.close()
        if row:
            if bcrypt.checkpw(password.encode("utf-8"), row[2].encode("utf-8")):
                role = row[0]
                user_id = row[1]
                root.title("Меню")
                menu_frame()
                show_frame(frm_menu)

            else:
                messagebox.showerror("Неверный пароль", "Попробуйте снова или обратитесь к администратору.")
        else:
            messagebox.showerror("Ошибка", "Пользователь не найден")
    else:
        messagebox.showinfo("Заполните все поля!", "Все поля обязательны к заполнению.")
    ent_pwd_auth.delete(0,tk.END)
    ent_lgn_auth.delete(0,tk.END)

def sign_up(first_name,last_name,login,password,phone):
    if first_name and last_name and login and password and phone:
        role = "Client"
        if len(login) >= 10 and len(password)>=10:
            try:
                byte_password = password.encode("utf-8")
                salt = bcrypt.gensalt()
                hashed_pwd = bcrypt.hashpw(byte_password,salt)
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO user (first_name,last_name,login,password,phone,role) VALUES (%s,%s,%s,%s,%s,%s)", (first_name,last_name,login,hashed_pwd,phone, role))
                conn.commit()
                conn.close()
                cursor.close()
                root.title("Вход")
                auth_frame()
                show_frame(frm_auth)
                messagebox.showinfo("Успешная регистрация", "Войдите в приложение.")
            except Exception as e:
                messagebox.showerror("Ошибка подключения к бд", f'Текст ошибки:{e}')
        else:
            messagebox.showerror("Неверный формат логина или пароля", "Длинна и логина, и пароля должна быть 10 символов.")
    else:
        messagebox.showinfo("Заполните все поля!", "Все поля обязательны  к заполнению.")

hello_frame()
show_frame(frm_hello)
somedate = date.today()
print(somedate)
root.mainloop()
"""

class Binding:
    """
    OpenSSL API wrapper.
    """
    def __lib__():"""
    import tkinter as tk
from tkinter import messagebox
import bcrypt
import pymysql
import pymysql.cursors

def connect(): #подключение к базе данных
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="hotel_system2",
        cursorclass=pymysql.cursors.DictCursor
    )

def show_client_screen(): #экран пользователя (по ролям)
    win = tk.Toplevel()
    win.title("Панель Клиента")

    tk.Label(win, text="Вы вошли как клиент", font=("Arial", 16)).pack(pady=20)
    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)
    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)

def admin_screen():#экран админа (по ролям)
    win = tk.Toplevel()
    win.title("Панель Админа")

    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)
    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)

def manager_screen():#экран менеджера (по ролям)
    win = tk.Toplevel()
    win.title("Панель Менеджера")

    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)
    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)

def staff_screen():#экран сотрудника (по ролям)
    win = tk.Toplevel()
    win.title("Панель Сотрудника")

    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)
    tk.Button(win, text="Посмотреть", width=30).pack(pady=5)

login_attempts = {}#счетчик авторизаций под определенными данными

def show_login(root):#метод для авторизации
    win = tk.Toplevel(root)
    win.title("Вход (Клиент)")

    tk.Label(win, text="Логин").pack()
    login_entry = tk.Entry(win)
    login_entry.pack()

    tk.Label(win, text="Пароль").pack()
    password_entry = tk.Entry(win, show="*")
    password_entry.pack()

    def login_attempt():
        login = login_entry.get()
        password = password_entry.get()

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM client WHERE login = %s", (login,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            messagebox.showerror("Ошибка", "Пользователь не найден")
            return
        
        if login in login_attempts and login_attempts[login] >= 3:
            messagebox.showerror("Ошибка", "Учетная запись заблокирована")
            return
        
        if bcrypt.checkpw(password.encode(), result["password"].encode()):
            messagebox.showinfo("Успех", "Вы успешно вошли")
            login_attempts.pop(login, None)
            win.destroy()
            show_client_screen()
        else:
            login_attempts[login] = login_attempts.get(login, 0) + 1
            messagebox.showerror("Ошибка", "Неправильный пароль")

    tk.Button(win, text="Войти", command=login_attempt).pack()

def register_show(root):
    win = tk.Toplevel(root)
    win.title("Регистрация")

    entries = {}
    for label in ("Фамилия", "Имя", "Отчество", "Логин", "Пароль"):
        tk.Label(win, text=label).pack()
        e = tk.Entry(win, show="*" if label == "Пароль" else None)
        e.pack()
        entries[label] = e
    
    def register():
        data = {k: v.get() for k, v in entries.items()}

        hashed = bcrypt.hashpw(data["Пароль"].encode(), bcrypt.gensalt()).decode()


        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute(""
                INSERT INTO client (first_name_client, last_name_client, father_name_client, login, password)
                VALUES (%s, %s, %s, %s, %s)
            "", (data["Фамилия"], data["Имя"], data["Отчество"], data["Логин"], hashed))
            conn.commit()
            messagebox.showinfo("Успех", "Регистрация завершена")
            win.destroy()
            show_client_screen()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Регистрация невозможно {e}")
        finally:
            conn.close()

    tk.Button(win, text="Зарегистрироваться", command=register).pack()

def show_staff_login(root):
    win = tk.Toplevel(root)
    win.title("Вход (Сотрудник)")

    tk.Label(win, text="Логин").pack()
    login_entry = tk.Entry(win)
    login_entry.pack()

    tk.Label(win, text="Пароль").pack()
    password_entry = tk.Entry(win, show="*")
    password_entry.pack()

    def login():
        login = login_entry.get()
        password = password_entry.get()

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT password,role FROM users WHERE login = %s", (login,))
        result = cursor.fetchone()
        conn.close()

        if not result or result["password"] != password:
            messagebox.showerror("Ошибка", "Неправильный логин или пароль")
            return
        
        messagebox.showinfo("Успех", f"Добро пожаловать, {result['role']}")
        win.destroy()

        if result["role"] == "Admin":
            admin_screen()
        elif result["role"] == "Manager":
            manager_screen()
        elif result["role"] == "Staff":
            staff_screen()

    tk.Button(win, text="Войти", command=login).pack()

def main():
    root = tk.Tk()
    root.title("Гостиница")
    root.geometry("500x300")
    root.resizable(False, False)

    tk.Label(root, text="Добро пожаловать!", font=("Arial", 16)).pack(pady=40)
    tk.Button(root, text="Вход", width=25, command=lambda: show_login(root)).pack(pady=5)
    tk.Button(root, text="Регистрация", width=25, command=lambda: register_show(root)).pack(pady=5)
    tk.Button(root, text="Для персонала", width=25, command=lambda: show_staff_login(root)).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
    """
    lib: typing.ClassVar = None
    ffi = _openssl.ffi
    _lib_loaded = False
    _init_lock = threading.Lock()

    def __init__(self) -> None:
        self._ensure_ffi_initialized()

    @classmethod
    def _ensure_ffi_initialized(cls) -> None:
        with cls._init_lock:
            if not cls._lib_loaded:
                cls.lib = build_conditional_library(
                    _openssl.lib, CONDITIONAL_NAMES
                )
                cls._lib_loaded = True

    @classmethod
    def init_static_locks(cls) -> None:
        cls._ensure_ffi_initialized()


def _verify_package_version(version: str) -> None:
    # Occasionally we run into situations where the version of the Python
    # package does not match the version of the shared object that is loaded.
    # This may occur in environments where multiple versions of cryptography
    # are installed and available in the python path. To avoid errors cropping
    # up later this code checks that the currently imported package and the
    # shared object that were loaded have the same version and raise an
    # ImportError if they do not
    so_package_version = _openssl.ffi.string(
        _openssl.lib.CRYPTOGRAPHY_PACKAGE_VERSION
    )
    def version():"""
    import tkinter as tk
from tkinter import messagebox, ttk
from db_handler import connection_db
from datetime import date
import bcrypt
import requests

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Управление гостиницей")
        self.geometry("900x700")
        self.resizable(False, True)
        self.current_frame = None
        self.show_start()
        self.attemp = 0
        self.role = 0

    def show_start(self):
        self._switch_frame(StartFrame, self)

    def show_auth_client(self):
        self._switch_frame(AuthClientFrame, self)

    def show_reg_client(self):
        self._switch_frame(RegClientFrame, self)

    def show_client_frame(self):
        self._switch_frame(ClientFrame, self)

    def show_auth_staff(self):
        self._switch_frame(AuthStaffFrame, self)

    def show_staff(self):
        self._switch_frame(StaffFrame, self)

    def show_admin(self):
        self._switch_frame(AdminFrame, self)

    def _switch_frame(self, frame_class, *args):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_class(self, *args)
        self.current_frame.pack(fill="both", expand=True)
        
def reg_client(first_name, second_name, surname, phone, login, password):
    if len(password) < 8: # Проверка длинны пароля
        messagebox.showerror("Ошибка!", "Пароль должен быть не меньше 8 символов.")
        return False
    last_visit_date = date.today()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()) #Хеширование пароля
    try:
        conn = connection_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hotel.clients(first_name, second_name, surname, phone, last_date_visit, login, password) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                          (first_name, second_name, surname, phone, last_visit_date, login, hashed_pw))
        client_id = cursor.lastrowid
        cursor.execute("INSERT INTO hotel.status_client(clients_id_client, status) VALUES (%s, %s)", (client_id, 0))
        conn.commit()
        conn.close()
        messagebox.showinfo("Успешно!", "Регистарция прошла успешно!")
        return True
    except Exception as e: # Обработка ошибок при вставке данных в бд
        messagebox.showerror("Ошибка базы данны! ", f"{e}\nПользователь не зарегистрирован, попробуйте еще раз.")
        return False
    
def auth_client(login, password, self):
    try:
        conn = connection_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT c.password, c.id_client, s.status "
            "FROM hotel.clients c "
            "JOIN status_client s ON s.clients_id_client = c.id_client "
            "WHERE c.login = %s",
            (login,)
        )
        result = cursor.fetchone()
        conn.close()
        if result is None:
            messagebox.showerror("Ошибка!", "Пользователь не найден!\nПопробуйте еще раз")
        if result['status'] == 1:
            messagebox.showerror("Ошибка!", "Пользователь заблокировн!\nОбратитель к администратору.")
            app.show_start()
        if bcrypt.checkpw(password.encode(), result['password'].encode()):
            messagebox.showinfo("Успешно!", "Вы успешно авторизировались!")
            return True
        else:
            app.attemp +=1
            if app.attemp >= 3:
                messagebox.showerror("Ошибка!", "Неверный пароль или логин!\nВаша учетная запись заблокирована!\n\nОбратитесь к администратору")
                app.show_start()
                conn = connection_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE hotel.status_client SET status = 1 WHERE clients_id_client = %s", result['id_client'],)
                conn.commit()
                app.attemp = 0
                return False
            messagebox.showerror("Ошибка!", "Неверный пароль или логин!\nПопробуйте еще раз.")
    except Exception as e: # Обработка ошибок при вставке данных в бд
        print("Ошибка базы данны! ", f"{e}   Авторизация не прошла.")
        return False
    
def auth_staff(login, password, self):
    try:
        try:
            conn = connection_db()
            cursor = conn.cursor()
            cursor.execute("SELECT password, role FROM hotel.employees WHERE login = %s", login,)
            result = cursor.fetchone()
            conn.close()
        except Exception as e:
            messagebox.showerror("Ошибка базы данных!", "Ошибка при запросе к БД!")
        
        if result is None:
            messagebox.showerror("Ошибка!", "Пользователь не найден!\nПопробуйте еще раз")
        if bcrypt.checkpw(password.encode(), result['password'].encode()):
            messagebox.showinfo("Успешно!", "Вы успешно авторизировались!")
            if result['role'] == 1:
                app.show_staff()
            elif result['role'] == 2:
                app.show_admin()
        else:
            messagebox.showerror("Ошибка!", "Неверный пароль или логин!\nПопробуйте еще раз.")
            
    except Exception as e: # Обработка ошибок при вставке данных в бд
        print("Ошибка! ", f"{e}   Авторизация не прошла.")
        return False
    
class StartFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        tk.Label(self, text="Данное приложение предназначено\nдля управления гостиницей!", font=("Arial", 16)).pack(pady=20)
        self.frame = tk.Frame(self, width=200, height=200)
        self.frame.pack(pady=200)
        tk.Button(self.frame, text="Авторизация", width=30, command=lambda: app.show_auth_client()).pack(pady=5)
        tk.Button(self.frame, text="Регистрация", width=30, command=lambda: app.show_reg_client()).pack(pady=5)
        tk.Button(self.frame, text="Для сотрудников", width=30, command= lambda: app.show_auth_staff()).pack(pady=5)

class ClientFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        tk.Label(self, text="Экран клиента", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Выйти", width=20, command= lambda: app.show_start()).pack(pady=5)

class StaffFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        tk.Label(self, text="Экран Сотрудника", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Выйти", width=20, command= lambda: app.show_start()).pack(pady=5)
    
class AdminFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        tk.Label(self, text="Экран администратора", font=("Arial", 16)).pack(pady=20)
        self.pack(fill="both", expand=True)

        self.table_frame = tk.Frame(self, width=700, height=300)
        self.table_frame.pack(pady=10)
        self.table_frame.pack_propagate(False)

        columns = ("first_name", "second_name", "surname", "phone")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        self.tree.heading("first_name", text="Имя")
        self.tree.heading("second_name", text="Фамилия")
        self.tree.heading("surname", text="Отчество")
        self.tree.heading("phone", text="Номер телефона")

        # Настройка колонок — ширина и выравнивание
        for col in columns:
            self.tree.column(col, anchor='center', stretch=True, width=150)

        self.tree.pack(side=tk.LEFT, fill="both", expand=True)

        self.vscroll = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.configure(yscrollcommand=self.vscroll.set)

        tk.Button(self, text="Загрузить данные о клиентах", width=30, command=self.load_data).pack(pady=10)

        self.label = tk.Label(self, text="Тут будет результат API", font=('Arial', 10))
        self.label.pack(pady=10)

        
        tk.Button(self, text="Загрузить данные API", width=30, command=self.getFullNameApi).pack(pady=10)
        tk.Button(self, text="Выйти", width=20, command=lambda: app.show_start()).pack(pady=5)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = connection_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hotel.clients")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            self.tree.insert("", tk.END, values=(row["first_name"], row["second_name"], row["surname"], row["phone"]))

    def getFullNameApi(self):
        try:
            response = requests.get("http://localhost:4444/TransferSimulator/fullName")
            data = response.json()
            self.label.config(text=data['value'])
        except Exception as e:
            self.label.config(text="Ошибка API!")
            messagebox.showerror("API error!", f"Произошла ошибка при запросе к API!\n\n{e}")

class AuthClientFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="Авторизация", font=("Arial", 16)).pack(pady=20)

        tk.Label(self, text="Логин", font=("Arial", 12)).pack(pady=20)
        self.login_entry = tk.Entry(self)
        self.login_entry.pack()

        tk.Label(self, text="Пароль", font=("Arial", 12)).pack(pady=10)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Войти", width= 20, command=self.try_entry).pack(pady=15)
        tk.Button(self, text="Назад", width= 20, command= lambda: app.show_start()).pack(pady=20)

    def try_entry(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not login or not password:
            messagebox.showerror("Ошибка!","Пожалуйста, заполните все поля!")

        if auth_client(login, password, self):
            app.show_client_frame()
            
class RegClientFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        tk.Label(self, text="Регистрация", font=("Arial", 16)).pack(pady=20)

        tk.Label(self, text="Имя", font=("Arial", 12)).pack(pady=10)
        self.first_name_entry = tk.Entry(self)
        self.first_name_entry.pack()

        tk.Label(self, text="Фамилия", font=("Arial", 12)).pack(pady=10)
        self.second_name_entry = tk.Entry(self)
        self.second_name_entry.pack()

        tk.Label(self, text="Отчество", font=("Arial", 12)).pack(pady=3)
        tk.Label(self, text="(Не обязательно)", font=("Arial", 8)).pack(pady=1)
        self.surname_entry = tk.Entry(self)
        self.surname_entry.pack()

        tk.Label(self, text="Номер телефона", font=("Arial", 12)).pack(pady=10)
        self.phone_entry = tk.Entry(self)
        self.phone_entry.pack()

        tk.Label(self, text="Логин", font=("Arial", 12)).pack(pady=20)
        self.login_entry = tk.Entry(self)
        self.login_entry.pack()

        tk.Label(self, text="Пароль", font=("Arial", 12)).pack(pady=10)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Подтвердить", width=20, command=self.try_entry).pack(pady=15)
        tk.Button(self, text="Назад", width= 20, command= lambda: app.show_start()).pack(pady=20)

    def try_entry(self):
        first_name = self.first_name_entry.get().strip()
        second_name = self.second_name_entry.get().strip()
        surname = self.surname_entry.get().strip()
        phone = self.phone_entry.get().strip()
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not login or not password or not first_name or not second_name or not phone:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все обязательные поля!")
            return

        if reg_client(first_name, second_name, surname, phone, login, password):
            app.show_start()

class AuthStaffFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="Авторизация\nдля персонала", font=("Arial", 16)).pack(pady=20)

        tk.Label(self, text="Логин", font=("Arial", 12)).pack(pady=20)
        self.login_entry = tk.Entry(self)
        self.login_entry.pack()

        tk.Label(self, text="Пароль", font=("Arial", 12)).pack(pady=10)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Войти", width= 20, command=self.try_entry).pack(pady=15)
        tk.Button(self, text="Назад", width= 20, command= lambda: app.show_start()).pack(pady=20)

    def try_entry(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not login or not password:
            messagebox.showerror("Ошибка!","Пожалуйста, заполните все поля!")
        else: 
            auth_staff(login, password, self)
            

           
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()

import pymysql
from pymysql.cursors import DictCursor

def connection_db():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            db='hotel',
            cursorclass=DictCursor
        )
        print("Подключение к БД успешно!")
        return connection
    except:
        print("Произошла ошибка! Подключение к БД не установлено!")

    """
    if version.encode("ascii") != so_package_version:
        raise ImportError(
            "The version of cryptography does not match the loaded "
            "shared object. This can happen if you have multiple copies of "
            "cryptography installed in your Python path. Please try creating "
            "a new virtual environment to resolve this issue. "
            f"Loaded python version: {version}, "
            f"shared object version: {so_package_version}"
        )

    _openssl_assert(
        _openssl.lib.OpenSSL_version_num() == openssl.openssl_version(),
    )


_verify_package_version(cryptography.__version__)

Binding.init_static_locks()

if (
    sys.platform == "win32"
    and os.environ.get("PROCESSOR_ARCHITEW6432") is not None
):
    warnings.warn(
        "You are using cryptography on a 32-bit Python on a 64-bit Windows "
        "Operating System. Cryptography will be significantly faster if you "
        "switch to using a 64-bit Python.",
        UserWarning,
        stacklevel=2,
    )
