from textual.app import App, ComposeResult
from textual.widgets import Tree, Label
from tasks import get_entire_tree, walk_tree


class TreeApp(App):
    tree = None

    def compose(self) -> ComposeResult:
        self.tree = get_entire_tree()
        yield self.tree

    def on_tree_node_highlighted(self, event) -> None:
        node = event.node
        print(node)
        for n in walk_tree(self.tree):
            if n == node:
                n.set_label(f"Selected: {n.label}")
            else:
                if str(n.label).startswith("Selected: "):
                    n.set_label(str(n.label).replace("Selected: ", ""))


if __name__ == "__main__":
    app = TreeApp()
    app.run()
