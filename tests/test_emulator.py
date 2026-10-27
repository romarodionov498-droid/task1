"""Тесты этапов 1-2."""

import unittest

from emulator import (
    ShellError, ShellExit, debug_lines, execute, parse_args, parse_line,
    read_script, strip_comment,
)


class ParseTest(unittest.TestCase):
    """Проверка разбора строки."""

    def test_command_and_args(self):
        """Команда и аргументы делятся по пробелам."""
        self.assertEqual(parse_line("ls -l  /tmp"), ("ls", ["-l", "/tmp"]))

    def test_empty(self):
        """Пустая строка даёт None."""
        self.assertEqual(parse_line("   "), (None, []))


class ExecuteTest(unittest.TestCase):
    """Проверка выполнения команд."""

    def test_ls_stub(self):
        """ls печатает имя и аргументы."""
        self.assertEqual(execute("ls a b"), "ls a b")

    def test_cd_too_many_args(self):
        """cd с лишними аргументами даёт ошибку."""
        with self.assertRaises(ShellError):
            execute("cd a b")

    def test_unknown(self):
        """Неизвестная команда даёт ошибку."""
        with self.assertRaises(ShellError):
            execute("foo")

    def test_exit(self):
        """exit поднимает ShellExit."""
        with self.assertRaises(ShellExit):
            execute("exit")

    def test_exit_with_args(self):
        """exit с аргументами даёт ошибку."""
        with self.assertRaises(ShellError):
            execute("exit 1")


class ConfigTest(unittest.TestCase):
    """Проверка параметров и скрипта."""

    def test_defaults(self):
        """Без параметров значения равны None."""
        args = parse_args([])
        self.assertIsNone(args.vfs)
        self.assertIsNone(args.script)

    def test_both_params(self):
        """Оба параметра читаются из командной строки."""
        args = parse_args(["--vfs", "data", "--script", "s.txt"])
        self.assertEqual((args.vfs, args.script), ("data", "s.txt"))

    def test_debug_lines(self):
        """Отладочный вывод содержит все параметры."""
        args = parse_args(["--vfs", "data"])
        self.assertEqual(
            debug_lines(args),
            ["[debug] vfs = data", "[debug] script = None"],
        )

    def test_strip_comment(self):
        """Комментарии убираются из строки."""
        self.assertEqual(strip_comment("ls a  # список"), "ls a")
        self.assertEqual(strip_comment("# только комментарий"), "")

    def test_missing_script(self):
        """Отсутствующий скрипт даёт ошибку."""
        with self.assertRaises(ShellError):
            read_script("no_such_file.txt")


if __name__ == "__main__":
    unittest.main()