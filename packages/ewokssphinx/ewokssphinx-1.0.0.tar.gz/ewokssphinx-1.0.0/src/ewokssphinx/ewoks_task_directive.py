import inspect

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from ewokscore.task_discovery import discover_tasks_from_modules
from sphinx.util.docutils import SphinxDirective

from .pydantic_utils import pydantic_inputs
from .utils import field, get_task_name, simple_inputs, simple_outputs


def _task_type_option(argument):
    return directives.choice(argument, ("class", "method", "ppfmethod"))


class EwoksTaskDirective(SphinxDirective):
    required_arguments = 1
    option_spec = {
        "task-type": _task_type_option,
        "ignore-import-error": directives.flag,
    }

    def run(self):
        module_pattern = self.arguments[0]
        task_type = self.options.get("task-type")
        ignore_import_error = "ignore-import-error" in self.options

        def parse_doc(text) -> list[Node]:
            # Clean up indentation from docstrings so that Sphinx properly parses them
            return self.parse_text_to_nodes(inspect.cleandoc(text))

        results = []
        for task in discover_tasks_from_modules(
            module_pattern,
            task_type=task_type,
            raise_import_failure=not ignore_import_error,
        ):

            task_name = get_task_name(task["task_identifier"], task["task_type"])
            task_section = nodes.section(ids=[task_name], classes=["ewokssphinx-task"])

            task_section += nodes.title(text=task_name)
            if task["description"]:
                task_section += parse_doc(task["description"])

            task_section += nodes.field_list(
                "",
                field("Identifier", nodes.literal(text=task["task_identifier"])),
                field("Task type", nodes.Text(task["task_type"])),
            )

            # Force the field list to be compound so that Sphinx does not attach the "simple" CSS class
            io_definition = nodes.container(
                "",
            )

            input_model = task.get("input_model")
            if input_model is None:
                io_definition.append(
                    simple_inputs(
                        required_input_names=task["required_input_names"],
                        optional_input_names=task["optional_input_names"],
                    )
                )
            else:
                io_definition.append(pydantic_inputs(input_model, parse_doc=parse_doc))

            io_definition.append(simple_outputs(outputs=task["output_names"]))

            task_section.append(
                nodes.definition_list(
                    "", io_definition, classes=["ewokssphinx-field-list"]
                )
            )

            results.append(task_section)
        return results
