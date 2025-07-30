from collections import defaultdict


def extract_flask(app):
    grouped_routes = defaultdict(list)

    for rule in app.url_map.iter_rules():
        path = rule.rule
        methods = list(rule.methods - {'HEAD', 'OPTIONS'})
        endpoint = rule.endpoint
        view_func = app.view_functions.get(endpoint)
        summary = view_func.__doc__ or "No summary provided"
        docstring = view_func.__doc__

        group = path.strip("/").split("/")[0] or "root"

        grouped_routes[group].append({
            "path": path,
            "methods": methods,
            "summary": summary,
            "endpoint": endpoint,
            "response_model_schema": None,
            "docstring": docstring.strip() if docstring else None,
        })

    return grouped_routes