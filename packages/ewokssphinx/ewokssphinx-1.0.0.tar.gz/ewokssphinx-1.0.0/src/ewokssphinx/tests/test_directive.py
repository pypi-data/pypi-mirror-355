import pytest
from sphinx.testing import restructuredtext

from .conftest import assert_task_nodes


def _assert_class_task_nodes(nodes):
    assert_task_nodes(
        nodes,
        identifier="ewokssphinx.tests.dummy_tasks.MyTask",
        doc="""My task documentation""",
        task_type="class",
        required_inputs=["a", "b", "c"],
        optional_inputs=["d", "e"],
        outputs=["error", "result"],
    )


def _assert_method_nodes(nodes):
    assert_task_nodes(
        nodes[0],
        identifier="ewokssphinx.tests.dummy_tasks.my_other_task",
        doc=None,
        task_type="method",
        required_inputs=["f", "g"],
        optional_inputs=["h"],
        outputs=["return_value"],
    )

    assert_task_nodes(
        nodes[1],
        identifier="ewokssphinx.tests.dummy_tasks.run",
        doc="""Run task documentation""",
        task_type="method",
        required_inputs=["i"],
        optional_inputs=["j", "k"],
        outputs=["return_value"],
    )


def _assert_ppfmethod_nodes(nodes):
    assert_task_nodes(
        nodes,
        identifier="ewokssphinx.tests.dummy_tasks.run",
        doc="""Run task documentation""",
        task_type="ppfmethod",
        required_inputs=["i"],
        optional_inputs=["j", "k"],
        outputs=["return_value"],
    )


def test_ewokstasks(app):
    parsed_nodes = restructuredtext.parse(
        app, ".. ewokstasks:: ewokssphinx.tests.dummy_tasks"
    )

    assert len(parsed_nodes) == 4
    _assert_class_task_nodes(parsed_nodes[0])
    _assert_ppfmethod_nodes(parsed_nodes[1])
    _assert_method_nodes(parsed_nodes[2:])


def test_ewokstasks_class(app):
    parsed_nodes = restructuredtext.parse(
        app,
        """.. ewokstasks:: ewokssphinx.tests.dummy_tasks
              :task-type: class
        """,
    )

    assert len(parsed_nodes) == 4
    _assert_class_task_nodes(parsed_nodes)


def test_ewokstasks_method(app):
    parsed_nodes = restructuredtext.parse(
        app,
        """.. ewokstasks:: ewokssphinx.tests.dummy_tasks
              :task-type: method
        """,
    )

    assert len(parsed_nodes) == 2
    _assert_method_nodes(parsed_nodes)


def test_ewokstasks_ppfmethod(app):
    parsed_nodes = restructuredtext.parse(
        app,
        """.. ewokstasks:: ewokssphinx.tests.dummy_tasks
              :task-type: ppfmethod
        """,
    )

    assert len(parsed_nodes) == 4
    _assert_ppfmethod_nodes(parsed_nodes)


def test_ewokstasks_raised_import_error(app):
    with pytest.raises(ImportError):
        restructuredtext.parse(
            app,
            """.. ewokstasks:: not_existing
            """,
        )


def test_ewokstasks_ignore_import_error(app):
    parsed_nodes = restructuredtext.parse(
        app,
        """.. ewokstasks:: not_existing
            :ignore-import-error:
        """,
    )

    assert len(parsed_nodes) == 0
