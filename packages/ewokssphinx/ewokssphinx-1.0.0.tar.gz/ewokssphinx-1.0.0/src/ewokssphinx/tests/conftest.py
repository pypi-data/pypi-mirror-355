from typing import Type

import pytest
from docutils import nodes
from docutils.nodes import Node
from sphinx.testing.util import SphinxTestApp

from ewokssphinx.utils import get_task_name


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    srcdir = tmp_path_factory.mktemp("root")
    with open(srcdir / "conf.py", "w") as conf:
        conf.write('extensions = ["ewokssphinx"]')
    app = SphinxTestApp(
        "html", srcdir=srcdir, docutils_conf="[readers]\ndocinfo_xform: no"
    )

    return app


def assert_node(node, cls: Type[Node], text: str | None = None):
    assert isinstance(node, cls)
    if text is not None:
        assert node.astext() == text


def assert_field_node(node, name: str, value: str):
    assert isinstance(node, nodes.field)
    assert_node(node[0], nodes.field_name, name)
    assert_node(node[1], nodes.field_body, value)


def assert_simple_inputs(input_list, required_inputs, optional_inputs):
    input_term, input_definition = input_list
    assert_node(input_term, nodes.term, "Inputs:")
    assert_node(input_definition, nodes.definition)

    n_required = len(required_inputs)
    for i in range(n_required):
        assert_node(input_definition[0][i][0], nodes.term, f"{required_inputs[i]}*")

    n_optional = len(optional_inputs)
    for i in range(n_optional):
        assert_node(
            input_definition[0][n_required + i][0], nodes.term, optional_inputs[i]
        )


def assert_simple_outputs(output_list, outputs):
    output_term, output_definition = output_list
    assert_node(output_term, nodes.term, "Outputs:")
    assert_node(output_definition, nodes.definition)

    for i, output_name in enumerate(outputs):
        assert_node(output_definition[0][i][0], nodes.term, output_name)


def assert_task_nodes(
    parsed_nodes, identifier, doc, task_type, required_inputs, optional_inputs, outputs
):
    assert_task_preamble(parsed_nodes, identifier, doc, task_type)
    definition_list_node = parsed_nodes[-1]
    container_node = definition_list_node[0]
    input_list = container_node[0]
    assert_simple_inputs(
        input_list,
        required_inputs=required_inputs,
        optional_inputs=optional_inputs,
    )
    output_list = container_node[1]
    assert_simple_outputs(output_list, outputs=outputs)


def assert_task_preamble(parsed_nodes, identifier, doc, task_type):
    name = get_task_name(identifier, task_type)
    assert_node(parsed_nodes[0], nodes.title, name)
    if doc is not None:
        assert_node(parsed_nodes[1], nodes.paragraph, doc)
        field_list_nodes = parsed_nodes[2]
    else:
        field_list_nodes = parsed_nodes[1]
    assert_node(field_list_nodes, nodes.field_list)
    assert_field_node(field_list_nodes[0], name="Identifier", value=identifier)
    assert_field_node(field_list_nodes[1], name="Task type", value=task_type)
