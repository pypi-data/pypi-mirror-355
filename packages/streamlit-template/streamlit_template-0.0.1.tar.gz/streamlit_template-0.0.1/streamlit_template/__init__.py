import os
from importlib.metadata import version as _version

import jinja2
import streamlit.components.v1 as components

environment = jinja2.Environment()


_RELEASE = "STREAMLIT_COMMUNITY_DEVELOPMENT" not in os.environ

if not _RELEASE:
    _st_template = components.declare_component(
        "st_template",
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _st_template = components.declare_component(
        "st_template",
        path=build_dir,
    )


def print_version():
    """Show the installed version of the Streamlit Template package."""
    version = _version("streamlit-template")
    print(f"Streamlit Template, version {version}")


def st_template(
    html,
    on_change=None,
    key=None,
):
    """
    Render a custom component using only html in your streamlit app

    Parameters
    ----------
    body : str
        The body to be rendered

    Returns
    -------
    result : str or None
        Whatever you make the template return
    """

    result = _st_template(
        body=body,
        on_change=on_change,
        key=key,
    )
    return result

class Template():
    def __init__(self, template, style=None, on_change=None):
        self.template = environment.from_string(template)
        self.on_change = on_change
        self.style = style
        
    def render(self, *args, on_change=None, key=None, **kwargs):
        body = self.template.render(*args, **kwargs)
        return _st_template(
            body=body,
            style=self.style,
            on_change=on_change or self.on_change,
            key=key
        )
