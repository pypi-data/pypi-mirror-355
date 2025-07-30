from typing import Sequence

from docutils import nodes
from docutils.nodes import Node


def get_task_name(identifier: str, task_type: str) -> str:
    if task_type == "ppfmethod":
        # ppfmethods are all named `run` so use the module name as task name.
        return identifier.split(".")[-2]
    return identifier.split(".")[-1]


def field(name: str, body: Node) -> Node:
    return nodes.field(
        "",
        nodes.field_name(text=name),
        nodes.field_body("", body),
    )


def field_term(name: str, is_required: bool) -> nodes.term:
    if not is_required:
        return nodes.term(text=name)

    return nodes.term("", name, nodes.strong("", "*", classes=["ewokssphinx-required"]))


def simple_inputs(
    required_input_names: Sequence[str], optional_input_names: Sequence[str]
) -> nodes.definition_list_item:
    input_definition_list = nodes.definition_list()

    for input_name in required_input_names:
        input_definition_list.append(
            nodes.definition_list_item(
                "",
                field_term(input_name, True),
                nodes.definition(),
            ),
        )

    for input_name in optional_input_names:
        input_definition_list.append(
            nodes.definition_list_item(
                "",
                field_term(input_name, False),
                nodes.definition(),
            ),
        )

    return nodes.definition_list_item(
        "",
        nodes.term(text="Inputs:", classes=["field-odd"]),
        nodes.definition("", input_definition_list),
        classes=["field-list"],
    )


def simple_outputs(outputs: Sequence[str]) -> nodes.definition_list_item:
    output_definition_list = nodes.definition_list()

    for output_name in outputs:
        output_definition_list.append(
            nodes.definition_list_item(
                "",
                field_term(output_name, False),
                nodes.definition(),
            ),
        )

    return nodes.definition_list_item(
        "",
        nodes.term(text="Outputs:", classes=["field-even"]),
        nodes.definition("", output_definition_list),
        classes=["field-list"],
    )
