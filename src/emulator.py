"""Эмулятор оболочки ОС. Этап 1: REPL."""

import getpass
import socket
import tkinter as tk

MAX_CD_ARGS = 1


class ShellExit(Exception):
    """Сигнал о том, что пользователь ввёл exit."""


def make_title():
    """Собрать заголовок окна из реальных данных ОС."""
    return f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]"


def parse_line(line):
    """Разделить строку по пробелам на команду и аргументы."""
    parts = line.split()
    if not parts:
        return None, []
    return parts[0], parts[1:]


def cmd_ls(args):
    """Заглушка ls: выводит своё имя и аргументы."""
    return " ".join(["ls"] + args)


def cmd_cd(args):
    """Заглушка cd: выводит своё имя и аргументы."""
    if len(args) > MAX_CD_ARGS:
        return "cd: слишком много аргументов"
    return " ".join(["cd"] + args)


def cmd_exit(args):
    """Завершить работу эмулятора."""
    if args:
        return "exit: неверные аргументы"
    raise ShellExit


COMMANDS = {"ls": cmd_ls, "cd": cmd_cd, "exit": cmd_exit}


def execute(line):
    """Выполнить введённую строку и вернуть текст ответа."""
    command, args = parse_line(line)
    if command is None:
        return ""
    handler = COMMANDS.get(command)
    if handler is None:
        return f"{command}: команда не найдена"
    return handler(args)


class EmulatorApp:
    """Окно эмулятора: поле вывода и строка ввода."""

    def __init__(self, root):
        """Создать элементы окна."""
        self.root = root
        root.title(make_title())
        self.output = tk.Text(root, height=20, state="disabled")
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()

    def print_line(self, text):
        """Добавить строку в конец поля вывода."""
        self.output.configure(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.configure(state="disabled")

    def on_enter(self, _event):
        """Обработать нажатие Enter."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.print_line(f"$ {line}")
        try:
            result = execute(line)
        except ShellExit:
            self.root.destroy()
            return
        if result:
            self.print_line(result)


def main():
    """Создать окно и запустить эмулятор."""
    root = tk.Tk()
    EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
