from docutils import nodes
from sphinx.testing import restructuredtext

from .conftest import assert_node, assert_simple_outputs, assert_task_preamble


def test_ewokstasks_with_pydantic_input_model(app):
    parsed_nodes = restructuredtext.parse(
        app,
        """.. ewokstasks:: ewokssphinx.tests.dummy_tasks_pydantic
              :task-type: class
        """,
    )

    assert len(parsed_nodes) == 4
    assert_task_preamble(
        parsed_nodes,
        "ewokssphinx.tests.dummy_tasks_pydantic.FindLocation",
        """Finds a location given the GPS coordinates""",
        "class",
    )
    definition_list_node = parsed_nodes[-1]
    container_node = definition_list_node[0]
    input_list = container_node[0]
    input_term, input_definition = input_list

    assert_node(input_term, nodes.term, "Inputs:")
    assert_node(input_definition, nodes.definition)

    assert_node(input_definition[0][0][0], nodes.term, "latitude* : int")
    assert_node(input_definition[0][1][0], nodes.term, "longitude* : float")
    assert_node(input_definition[0][2][0], nodes.term, "planet : str= Earth")

    longitude_definition = input_definition[0][1][1]
    assert_node(longitude_definition, nodes.definition)
    assert_node(longitude_definition[0][0], nodes.Text, "Longitude of the GPS point. ")
    assert_node(longitude_definition[0][1], nodes.strong, "In degrees.")

    output_list = container_node[1]
    assert_simple_outputs(output_list, outputs=["error", "location"])
