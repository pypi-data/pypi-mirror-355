import importlib.resources as pkg_resources
import subprocess
import os

from html2image import Html2Image
import jinja2

from asup.tasks import Task


def print_task(task: Task):
    hti = Html2Image(size=(1109, 696))
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
        os.chdir(cwdpath)

        outputText = template.render(templateVars)
        with open("out.html", "w+") as f:
            f.write(outputText)

    hti.screenshot(
        url="file://out.html",
        save_as="asup.png",
    )
    # subprocess.run(
    #     [
    #         "brother_ql",
    #         "print",
    #         "-l",
    #         "62",
    #         "--red",
    #         "-r",
    #         "90",
    #         "asup.png",
    #     ],
    #     check=True,
    # )
    # os.remove(cwd + "/asup.png")
    # os.remove("/tmp/out.html")


if __name__ == "__main__":
    task = Task(
        name="Example Task",
        description="This is an example task description. 123",
        completed=False,
        priority=3,
    )
    print_task(task)
