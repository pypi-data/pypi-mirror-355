import importlib
from collections.abc import Callable
from typing import Any

from docutils import nodes
from docutils.nodes import Node
from ewokscore.model import BaseInputModel
from pydantic.fields import FieldInfo
from sphinx.util.typing import stringify_annotation

from .utils import field_term


def _import_model(input_model_qual_name: str) -> type[BaseInputModel]:
    module_name, _, model_name = input_model_qual_name.rpartition(".")

    mod = importlib.import_module(module_name)

    return getattr(mod, model_name)


def _pydantic_field_term(name: str, field_info: FieldInfo) -> nodes.term:
    node_term = field_term(name, field_info.is_required())

    if field_info.annotation is not None:
        node_term += [
            nodes.Text(" : "),
            nodes.literal(text=stringify_annotation(field_info.annotation)),
        ]

    if not field_info.is_required():
        node_term.append(
            nodes.literal(
                text=f"= {field_info.default}", classes=["ewokssphinx-default"]
            )
        )

    return node_term


def _example_list(examples: list[Any]) -> nodes.container:
    example_list = nodes.bullet_list()
    for example in examples:
        example_list.append(nodes.list_item("", nodes.Text(repr(example))))

    return nodes.container(
        "",
        nodes.Text("Examples:"),
        example_list,
        classes=["ewokssphinx-examples"],
    )


def pydantic_inputs(
    input_model_qual_name: str, parse_doc: Callable[[str], list[Node]]
) -> nodes.definition_list_item:
    model = _import_model(input_model_qual_name)

    field_names = sorted(
        model.model_fields.keys(),
        key=lambda name: model.model_fields[name].is_required(),
        reverse=True,
    )

    input_definition_list = nodes.definition_list()
    for field_name in field_names:
        field_info = model.model_fields[field_name]

        node_definition = nodes.definition()
        if field_info.description is not None:
            node_definition += parse_doc(field_info.description)

        if field_info.examples:
            node_definition.append(_example_list(field_info.examples))

        input_definition_list.append(
            nodes.definition_list_item(
                "",
                _pydantic_field_term(field_name, field_info),
                node_definition,
            )
        )

    return nodes.definition_list_item(
        "",
        nodes.term(text="Inputs:", classes=["field-odd"]),
        nodes.definition("", input_definition_list),
        classes=["field-list"],
    )
