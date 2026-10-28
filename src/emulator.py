"""Эмулятор оболочки ОС."""

import argparse
import base64
import getpass
import json
import socket
import tkinter as tk

MAX_CD_ARGS = 1
COMMENT_CHAR = "#"
TYPE_DIR = "dir"
TYPE_FILE = "file"
ENCODING_BASE64 = "base64"
INDENT = "  "


class ShellExit(Exception):
    """Сигнал о том, что пользователь ввёл exit."""


class ShellError(Exception):
    """Ошибка выполнения команды, скрипта или загрузки VFS."""


def make_title():
    """Собрать заголовок окна из реальных данных ОС."""
    return f"Эмулятор - [{getpass.getuser()}@{socket.gethostname()}]"


def parse_line(line):
    """Разделить строку по пробелам на команду и аргументы."""
    parts = line.split()
    if not parts:
        return None, []
    return parts[0], parts[1:]


def build_file(raw, path):
    """Построить файл VFS в памяти; base64 декодируется в байты."""
    content = raw.get("content", "")
    if not isinstance(content, str):
        raise ShellError(f"vfs: {path}: content должен быть строкой")
    encoding = raw.get("encoding")
    if encoding == ENCODING_BASE64:
        try:
            data = base64.b64decode(content, validate=True)
        except ValueError as error:
            raise ShellError(f"vfs: {path}: неверный base64") from error
        return {"type": TYPE_FILE, "data": data, "binary": True}
    if encoding is not None:
        raise ShellError(f"vfs: {path}: неизвестная кодировка {encoding}")
    data = content.encode("utf-8")
    return {"type": TYPE_FILE, "data": data, "binary": False}


def build_dir(raw, path):
    """Построить папку VFS в памяти вместе со всем содержимым."""
    children = raw.get("children", {})
    if not isinstance(children, dict):
        raise ShellError(f"vfs: {path}: children должен быть объектом")
    built = {}
    for name, child in children.items():
        built[name] = build_node(child, f"{path.rstrip('/')}/{name}")
    return {"type": TYPE_DIR, "children": built}


def build_node(raw, path):
    """Проверить узел JSON и построить узел VFS."""
    if not isinstance(raw, dict):
        raise ShellError(f"vfs: {path}: узел должен быть объектом")
    kind = raw.get("type")
    if kind == TYPE_DIR:
        return build_dir(raw, path)
    if kind == TYPE_FILE:
        return build_file(raw, path)
    raise ShellError(f"vfs: {path}: неизвестный тип {kind}")


def load_vfs(path):
    """Загрузить VFS из JSON-файла в память (на диск ничего не пишется)."""
    try:
        with open(path, encoding="utf-8") as file:
            raw = json.load(file)
    except OSError as error:
        message = f"vfs: не удалось открыть файл: {error}"
        raise ShellError(message) from error
    except ValueError as error:
        raise ShellError(f"vfs: неверный JSON: {error}") from error
    root = build_node(raw, "/")
    if root["type"] != TYPE_DIR:
        raise ShellError("vfs: корень должен быть папкой")
    return root


def count_nodes(node):
    """Посчитать папки и файлы внутри папки (сам корень не считается)."""
    dirs = files = 0
    for child in node["children"].values():
        if child["type"] == TYPE_DIR:
            sub_dirs, sub_files = count_nodes(child)
            dirs += 1 + sub_dirs
            files += sub_files
        else:
            files += 1
    return dirs, files


def describe_file(node):
    """Описать файл: тип содержимого и размер в байтах."""
    kind = "двоичный" if node["binary"] else "текст"
    return f" ({kind}, {len(node['data'])} байт)"


def tree_lines(node, depth=0):
    """Построить строки дерева VFS с отступами по уровням."""
    lines = []
    for name in sorted(node["children"]):
        child = node["children"][name]
        indent = INDENT * depth
        if child["type"] == TYPE_DIR:
            lines.append(f"{indent}{name}/")
            lines.extend(tree_lines(child, depth + 1))
        else:
            lines.append(f"{indent}{name}{describe_file(child)}")
    return lines


def cmd_ls(args, _vfs):
    """Заглушка ls: выводит своё имя и аргументы."""
    return " ".join(["ls"] + args)


def cmd_cd(args, _vfs):
    """Заглушка cd: выводит своё имя и аргументы."""
    if len(args) > MAX_CD_ARGS:
        raise ShellError("cd: слишком много аргументов")
    return " ".join(["cd"] + args)


def cmd_exit(args, _vfs):
    """Завершить работу эмулятора."""
    if args:
        raise ShellError("exit: неверные аргументы")
    raise ShellExit


def cmd_vfs(args, vfs):
    """Служебная команда: показать дерево загруженной VFS."""
    if args:
        raise ShellError("vfs: неверные аргументы")
    if vfs is None:
        raise ShellError("vfs: VFS не загружена (укажите --vfs)")
    lines = ["/"] + [INDENT + line for line in tree_lines(vfs)]
    return "\n".join(lines)


COMMANDS = {"ls": cmd_ls, "cd": cmd_cd, "exit": cmd_exit, "vfs": cmd_vfs}


def execute(line, vfs=None):
    """Выполнить введённую строку и вернуть текст ответа."""
    command, args = parse_line(line)
    if command is None:
        return ""
    handler = COMMANDS.get(command)
    if handler is None:
        raise ShellError(f"{command}: команда не найдена")
    return handler(args, vfs)


def parse_args(argv=None):
    """Разобрать параметры командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки ОС")
    parser.add_argument("--vfs", help="путь к JSON-файлу с VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def debug_lines(args):
    """Сформировать отладочный вывод всех заданных параметров."""
    return [f"[debug] {name} = {value}" for name, value in vars(args).items()]


def strip_comment(line):
    """Убрать из строки скрипта комментарий (всё после #)."""
    return line.split(COMMENT_CHAR, 1)[0].strip()


def read_script(path):
    """Прочитать строки стартового скрипта."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().splitlines()
    except OSError as error:
        raise ShellError(f"не удалось открыть скрипт: {error}") from error


class EmulatorApp:
    """Окно эмулятора: поле вывода и строка ввода."""

    def __init__(self, root, args):
        """Создать элементы окна и запланировать запуск."""
        self.root = root
        self.args = args
        self.vfs = None
        root.title(make_title())
        self.output = tk.Text(root, height=20, state="disabled")
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()
        root.after(0, self.start_up)

    def print_line(self, text):
        """Добавить строку в конец поля вывода."""
        self.output.configure(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.configure(state="disabled")

    def start_up(self):
        """Вывести параметры, загрузить VFS и выполнить скрипт."""
        for text in debug_lines(self.args):
            self.print_line(text)
        if self.args.vfs:
            self.load_vfs_option(self.args.vfs)
        if self.args.script:
            self.run_script(self.args.script)

    def load_vfs_option(self, path):
        """Загрузить VFS; при ошибке сообщить и работать без неё."""
        try:
            self.vfs = load_vfs(path)
        except ShellError as error:
            self.print_line(f"Ошибка: {error}")
            return
        dirs, files = count_nodes(self.vfs)
        message = f"[debug] VFS загружена: папок {dirs}, файлов {files}"
        self.print_line(message)

    def run_line(self, line, number=None):
        """Показать строку и выполнить её; False, если был exit."""
        self.print_line(f"$ {line}")
        try:
            result = execute(line, self.vfs)
        except ShellExit:
            self.root.destroy()
            return False
        except ShellError as error:
            prefix = "" if number is None else f"Ошибка в строке {number}: "
            self.print_line(prefix + str(error))
            return True
        if result:
            self.print_line(result)
        return True

    def run_script(self, path):
        """Выполнить стартовый скрипт, пропуская ошибочные строки."""
        try:
            lines = read_script(path)
        except ShellError as error:
            self.print_line(f"Ошибка: {error}")
            return
        for number, raw in enumerate(lines, start=1):
            line = strip_comment(raw)
            if line and not self.run_line(line, number):
                return

    def on_enter(self, _event):
        """Обработать нажатие Enter."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.run_line(line)


def main():
    """Разобрать параметры, создать окно и запустить эмулятор."""
    args = parse_args()
    root = tk.Tk()
    EmulatorApp(root, args)
    root.mainloop()


if __name__ == "__main__":
    main()
