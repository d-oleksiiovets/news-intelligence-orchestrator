import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# def setup_logger(level=logging.INFO):
#     logger = logging.getLogger()
#     logger.setLevel(level)

#     if logger.hasHandlers():
#         logger.handlers.clear()

#     console_handler = RichHandler(
#         rich_tracebacks=True,
#         show_time=True,
#         show_level=True,
#         show_path=False,
#         markup=True,
#         log_time_format="[%X]"
#     )

#     console_handler.setFormatter(logging.Formatter("%(message)s"))
#     logger.addHandler(console_handler)

#     file_handler = logging.FileHandler("app.log", encoding="utf-8")
#     file_handler.setFormatter(logging.Formatter(
#         "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
#     ))

#     logger.addHandler(file_handler)

#     return logger

def setup_logger(level=logging.INFO):
    # Берем именно корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # ПОЛНОСТЬЮ очищаем все существующие обработчики (удаляем то, что добавил Alembic)
    while root_logger.handlers:
        root_logger.removeHandler(root_logger.handlers[0])

    # Принудительно создаем консоль
    console = Console(force_terminal=True, markup=True)

    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_level=False, # Скрываем стандартный уровень, раз у нас свои плашки
        show_path=False,
        markup=True
    )
    
    # Форматтер оставляем пустым для Rich, он сам всё сделает
    root_logger.addHandler(console_handler)

    # Файловый лог
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root_logger.addHandler(file_handler)

    return root_logger

logger = setup_logger()

class StatusLog:
    @staticmethod
    def success(msg: str):
        logger.info(f"[bold green]  DONE  [/] {msg}")

    @staticmethod
    def fail(msg: str):
        logger.error(f"[bold red]  FAIL  [/] {msg}")

    @staticmethod
    def info(msg: str):
        logger.info(f"[bold cyan]  INFO  [/] {msg}")
        
    @staticmethod
    def skip(msg: str):
        logger.info(f"[bold gold3]  SKIP  [/] {msg}")