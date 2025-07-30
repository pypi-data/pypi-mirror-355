import importlib
from typing import Any
from fastapi import Response


def dict_to_ft_component(d):
    children_raw = d.get("_children", ())
    if isinstance(children_raw, str):
        children_raw = (children_raw,)
    children = tuple(
        dict_to_ft_component(c) if isinstance(c, dict) else c for c in children_raw
    )
    # TODO: cache this somehow
    module = importlib.import_module(d["_module"])
    obj = getattr(module, d["_name"])
    return obj(*children, **d.get("_attrs", {}))


class TagResponse(Response):
    """Custom response class to handle fastapi_tags.tags.Tags."""

    media_type = "text/html; charset=utf-8"

    def is_htmx(request=None):
        "Check if the request is an HTMX request"
        return request and "hx-request" in request.headers

    def render(self, content: Any) -> bytes:
        """Render Tag elements to bytes of HTML."""
        if isinstance(content, dict):
            content = dict_to_ft_component(content)
        return content.render().encode("utf-8")
