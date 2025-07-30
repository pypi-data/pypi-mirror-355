from textual.containers import HorizontalScroll
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    TextArea,
)
from textual.app import App, ComposeResult
from asup.tasks import (
    get_entire_tree,
    ensure_config_exists,
    serialize_tree,
    write_json,
    Task,
    TaskList,
)


class BaseScreen(Screen):
    tree = None
    editor = None
    selected_node = None

    BINDINGS = [
        ("c", "create", "Create task"),
        ("x", "create_list", "Create List"),
        ("d", "delete", "Delete task"),
    ]

    def action_create(self) -> None:
        if self.selected_node:
            if self.selected_node.allow_expand:
                new_node = self.selected_node.add_leaf(
                    "New Task +",
                    data=Task(
                        name="New Task +",
                        description="Fill me in",
                        completed=False,
                        priority=1,
                    ),
                )
            else:
                new_node = self.selected_node.parent.add_leaf(
                    "New Task +",
                    data=Task(
                        name="New Task +",
                        description="Fill me in",
                        completed=False,
                        priority=1,
                    ),
                )
            self.tree.refresh()
            self.tree.focus(new_node)
            self.editor.text = f"{new_node.label}\n\n{new_node.data.description}"
            self.selected_node = new_node
            print(f"Created new node: {new_node.label}")
        else:
            print("No node selected to create a new task under.")

    def action_create_list(self) -> None:
        if self.selected_node:
            if self.selected_node.allow_expand:
                new_node = self.selected_node.add(
                    "New List",
                    expand=True,
                    data=TaskList(name="New List"),
                )
            else:
                new_node = self.selected_node.parent.add(
                    "New List",
                    expand=True,
                    data=TaskList(name="New List"),
                )
            self.tree.refresh()
            self.tree.focus(new_node)
            self.editor.text = f"{new_node.label}\n\n"
            self.selected_node = new_node
            print(f"Created new list: {new_node.label}")
        else:
            print("No node selected to create a new list under.")

    def action_delete(self) -> None:
        if self.selected_node and self.selected_node != self.tree.root:
            parent = self.selected_node.parent
            if parent:
                node_to_select = (
                    self.selected_node.previous_sibling
                    or self.selected_node.next_sibling
                    or parent
                )
                self.selected_node.remove()
                self.tree.refresh()
                self.editor.text = ""
                print(f"Deleted node: {self.selected_node.label}")
                self.tree.select_node(node_to_select)
            else:
                print("Cannot delete the root node.")
        else:
            print("No node selected or trying to delete the root node.")

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with HorizontalScroll(can_focus=False):
            self.tree = get_entire_tree()
            yield self.tree
            self.tree.root.expand()
            self.editor = TextArea(id="editor", show_line_numbers=True)
            yield self.editor
        yield Footer(id="Footer")

    def on_tree_node_highlighted(self, event) -> None:
        self.selected_node = event.node
        node = event.node
        if node == self.tree.root:
            self.editor.disabled = True
            self.editor.text = "Root node selected, nothing to edit."
        else:
            self.editor.disabled = False
            if node.data.type == "task":
                self.editor.text = f"{node.label}\n\n{node.data['description']}"
            else:
                self.editor.text = f"{node.label}"

    def on_text_area_changed(self):
        if self.editor.disabled:
            return
        node = self.selected_node
        if node:
            lines = self.editor.text.splitlines()
            if not lines or not lines[0].strip():
                label = ""
            else:
                label = lines[0]
            node.set_label(label)
            self.selected_node.data.name = label
            if node.data.type == "task":
                desc = self.editor.text.splitlines()[1:]
                for line in desc:
                    if line.strip() == "":
                        desc.remove(line)
                node.data["description"] = "\n".join(desc)
                print(f"Updated node {node.label} with new description.")
        else:
            print("No node found for the editor.")
        # TODO turn on/off to write to file
        print(serialize_tree(self.tree))
        # write_json(serialize_tree(self.tree)[0]["items"])


class Asup(App):
    AUTO_FOCUS = "#task_tree"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def on_ready(self) -> None:
        self.push_screen(BaseScreen())

    def action_quit(self) -> None:
        self.exit()
