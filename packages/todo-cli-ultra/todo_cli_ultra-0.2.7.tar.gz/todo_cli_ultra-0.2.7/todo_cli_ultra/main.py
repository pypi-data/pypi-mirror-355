import typer
from typing_extensions import Annotated
from todo_cli_ultra.utils import save_task, update_tasks, load_task
from rich.console import Console
from rich.table import Table
from todo_cli_ultra.constants import TASKS_FILE, APP_NAME

app = typer.Typer(name=APP_NAME)
console = Console()


@app.callback(invoke_without_command=True)
def initialize(ctx: typer.Context):
    """
    Ensure the tasks file exists before running any command.
    """
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]")


@app.command()
def create(task: str):
    """Create a task

    Args:
        task (str): a string describing your task
    """

    save_task(task)


@app.command()
def update(index: int, task: str):
    """Update your task

    Args:
        index (int): Task ID
        task (str): New Task
    """
    tasks = load_task()
    tasks[index]["content"] = task
    update_tasks(tasks)


@app.command()
def view(
    show_all: Annotated[
        bool,
        typer.Option(
            "--all", "-a", help="Show all tasks including those which are done"
        ),
    ] = False,
):
    """View all your tasks"""
    tasks = load_task()
    if tasks:
        table = Table("Status", "ID", "Task")
        for i, task in enumerate(tasks):
            if not task["done"] or (task["done"] and show_all):
                table.add_row(
                    "[green]Done[/green]"
                    if task["done"]
                    else "[yellow]In Progress[/yellow]",
                    str(i),
                    task["content"],
                )
        console.print(table)
    else:
        console.print("[yellow]No Tasks Found![yellow]")


@app.command()
def delete(index: int):
    """Delete your task

    Args:
        index (int): Task ID
    """
    tasks = load_task()
    del tasks[index]
    update_tasks(tasks)


@app.command()
def done(index: int):
    """Mark Task as Done

    Args:
        index (int): Task ID
    """
    tasks = load_task()
    tasks[index]["done"] = True
    update_tasks(tasks=tasks)


app()
