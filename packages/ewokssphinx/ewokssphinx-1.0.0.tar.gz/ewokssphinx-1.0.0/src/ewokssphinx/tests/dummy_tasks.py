from ewokscore import Task


class MyTask(
    Task,
    input_names=["a", "b", "c"],
    optional_input_names=["d", "e"],
    output_names=["result", "error"],
):
    """My task documentation"""

    def run(self):
        pass


def my_other_task(f, g, h=None):
    pass


def run(i, j=None, k=None):
    """Run task documentation"""

    pass


class _HiddenTask(
    Task,
    input_names=["one"],
    optional_input_names=["two", "three"],
    output_names=["result", "error"],
):
    def run(self):
        pass
