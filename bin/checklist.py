import json
from pathlib import Path

import typer
from dotenv import load_dotenv

from tools import constants
from tools.dev_formatter_task import DEVFormatterTask

TASKS = {"dev": DEVFormatterTask}


def main(article_path: Path = typer.Argument(..., exists=True)):
    """Run an article through the checklist."""
    if article_path.suffix != ".md":
        typer.echo("The provided article path is not a Markdown file.")
        raise typer.Exit(code=1)

    load_dotenv()

    checklist = Checklist(article_path)
    checklist.load(TASKS.keys())

    for item in checklist:
        if checklist.is_complete(item):
            typer.echo(f"Skipping complete item: {item}")
            continue

        task = TASKS[item]()
        response = typer.confirm(task.prompt, default=True)
        if response:
            typer.echo(task.start)
            status = task.handle(article_path=article_path)
            if status:
                typer.echo("Task completed.")
                checklist.complete(item)

    checklist.write()


class Checklist:
    """A container to track which checklist items are processed."""

    checklists_dir = constants.root / "checklists"

    def __init__(self, article_path):
        self.article_path = article_path
        self.items = {}

    def __iter__(self):
        return iter(self.items.keys())

    @property
    def path(self):
        article_path = str(
            self.article_path.relative_to("content").with_suffix(".json")
        )
        article_path = article_path.replace("/", "_")
        return self.checklists_dir / article_path

    def load(self, checklist_items):
        try:
            with self.path.open() as f:
                self.items = json.load(f)
        except FileNotFoundError:
            self.items = {item: False for item in checklist_items}

    def is_complete(self, item):
        return self.items[item]

    def complete(self, item):
        self.items[item] = True

    def write(self):
        """Store the checklist for any future use."""
        with self.path.open("w") as f:
            json.dump(self.items, f, sort_keys=True, indent=2)
