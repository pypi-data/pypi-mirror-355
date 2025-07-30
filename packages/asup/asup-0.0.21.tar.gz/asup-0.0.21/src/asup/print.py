import importlib.resources as pkg_resources
import subprocess
import os

import imgkit
import jinja2

from asup.tasks import Task


def print_task(task: Task):
    with pkg_resources.path("asup", "template.html") as search_path:
        cwdpath = os.path.dirname(search_path)
        templateLoader = jinja2.FileSystemLoader(searchpath=cwdpath)
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "template.html"
        template = templateEnv.get_template(TEMPLATE_FILE)
        templateVars = {
            "header": task.name,
            "content": task.description,
            "footer": "•" * task.priority,
        }
        outputText = template.render(templateVars)
        with open("out.html", "w+") as f:
            f.write(outputText)
        options = {
            "width": 1109,
            "height": 696,
            "disable-smart-width": "",
            "format": "png",
        }
        imgkit.from_file("out.html", "asup.png", options=options)

    subprocess.run(
        [
            "brother_ql",
            "print",
            "-l",
            "62",
            "--red",
            "-r",
            "90",
            "asup.png",
        ],
        check=True,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    os.remove("asup.png")
    os.remove("out.html")


if __name__ == "__main__":
    task = Task(
        name="Example Task",
        description="This is an example task description. 123",
        completed=False,
        priority=3,
    )
    print_task(task)
