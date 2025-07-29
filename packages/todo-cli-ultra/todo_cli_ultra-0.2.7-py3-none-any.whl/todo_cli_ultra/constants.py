import typer
from pathlib import Path

APP_NAME = "todo-cli-ultra"
app_dir = typer.get_app_dir(APP_NAME)
TASKS_FILE: Path = Path(app_dir) / "todo.json"
