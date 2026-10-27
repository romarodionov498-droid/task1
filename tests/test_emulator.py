"""Тесты этапа 1."""

import unittest

from emulator import ShellExit, execute, parse_line


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
        self.assertIn("слишком много", execute("cd a b"))

    def test_unknown(self):
        """Неизвестная команда даёт ошибку."""
        self.assertIn("не найдена", execute("foo"))

    def test_exit(self):
        """exit поднимает ShellExit."""
        with self.assertRaises(ShellExit):
            execute("exit")

    def test_exit_with_args(self):
        """exit с аргументами даёт ошибку."""
        self.assertIn("неверные", execute("exit 1"))


if __name__ == "__main__":
    unittest.main()