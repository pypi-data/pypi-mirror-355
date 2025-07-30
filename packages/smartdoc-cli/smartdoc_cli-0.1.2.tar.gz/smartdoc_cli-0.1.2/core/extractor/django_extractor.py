import os
from collections import defaultdict
import django


def extract_django(module):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_app.settings')
    django.setup()

    from django.urls import get_resolver
    resolver = get_resolver()
    grouped_routes = defaultdict(list)

    for pattern in resolver.url_patterns:
        path = pattern.pattern._route
        callback = pattern.callback
        summary = callback.__doc__ or "No summary provided"
        endpoint = callback.__name__
        docstring = callback.__doc__

        group = path.strip("/").split("/")[0] or "root"

        grouped_routes[group].append({
            "path": path,
            "methods": ["GET"],  # You can enhance this if more info is needed
            "summary": summary,
            "endpoint": endpoint,
            "response_model_schema": None,
            "docstring": docstring.strip() if docstring else None,
        })

    return grouped_routes
