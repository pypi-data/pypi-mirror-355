from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.osutil import copyfile

from .ewoks_task_directive import EwoksTaskDirective


def copy_css(app, exception):
    if app.builder.name != "html" or exception:
        return
    static_dir = Path(app.builder.outdir) / "_static"
    copyfile(Path(__file__).parent / "ewokssphinx.css", static_dir / "ewokssphinx.css")


def setup(app: Sphinx):
    app.add_directive("ewokstasks", EwoksTaskDirective)

    app.add_css_file("ewokssphinx.css")
    app.connect("build-finished", copy_css)
