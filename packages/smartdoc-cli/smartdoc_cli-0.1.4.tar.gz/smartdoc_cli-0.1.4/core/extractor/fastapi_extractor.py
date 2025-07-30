from collections import defaultdict
from fastapi.routing import APIRoute


def extract_fastapi(app):
    grouped_routes = defaultdict(list)

    for route in app.routes:
        if isinstance(route, APIRoute):
            path = route.path
            methods = list(route.methods)
            summary = route.summary or "No summary provided"
            endpoint = route.endpoint.__name__
            response_model = route.response_model
            docstring = route.endpoint.__doc__

            schema = None
            if response_model:
                try:
                    schema = response_model.schema()
                except Exception:
                    schema = None

            group = path.strip("/").split("/")[0] or "root"

            grouped_routes[group].append({
                "path": path,
                "methods": methods,
                "summary": summary,
                "endpoint": endpoint,
                "response_model_schema": schema,
                "docstring": docstring.strip() if docstring else None,
            })

    return grouped_routes
