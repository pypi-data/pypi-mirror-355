import os
import django
from collections import defaultdict
from django.urls.resolvers import URLPattern, URLResolver


def extract_django(module: str):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", module)
    django.setup()

    from django.urls import get_resolver
    from rest_framework.views import APIView

    grouped_routes = defaultdict(list)
    seen_paths = set()

    def normalize_path(pattern):
        if hasattr(pattern, "_route"):
            return pattern._route
        elif hasattr(pattern, "pattern"):
            return str(pattern.pattern)
        else:
            return str(pattern)

    def extract_methods_from_callback(callback):
        methods = []
        # DRF class-based view
        if hasattr(callback, "cls"):
            cls = callback.cls
            if hasattr(cls, "http_method_names"):
                methods = [
                    m.upper() for m in cls.http_method_names
                    if hasattr(cls, m)
                ]
        elif hasattr(callback, "view_class"):  # Generic Django class view
            cls = callback.view_class
            if hasattr(cls, "http_method_names"):
                methods = [
                    m.upper() for m in cls.http_method_names
                    if hasattr(cls, m)
                ]
        else:
            methods = ["GET"]  # fallback for FBV
        return sorted(set(methods))

    def traverse(urlpatterns, prefix=""):
        for entry in urlpatterns:
            if isinstance(entry, URLResolver):
                traverse(entry.url_patterns, prefix + normalize_path(entry.pattern))
            elif isinstance(entry, URLPattern):
                try:
                    raw_path = prefix + normalize_path(entry.pattern)
                    path = raw_path.replace("^", "").replace("$", "")
                    if path in seen_paths:
                        continue
                    seen_paths.add(path)

                    callback = entry.callback
                    endpoint = (
                        callback.view_class.__name__
                        if hasattr(callback, "view_class")
                        else callback.__name__
                    )
                    doc = callback.__doc__
                    docstring = doc.strip() if doc else None
                    summary = (
                        doc.strip().split("\n")[0]
                        if doc and len(doc.strip().split("\n")) > 0
                        else "No summary provided"
                    )
                    methods = extract_methods_from_callback(callback)

                    group = path.strip("/").split("/")[0] or "root"

                    grouped_routes[group].append(
                        {
                            "path": f"/{path}",
                            "methods": methods,
                            "summary": summary,
                            "endpoint": endpoint,
                            "docstring": docstring,
                        }
                    )
                except Exception as e:
                    print(f"⚠️ Error processing pattern {entry}: {e}")

    resolver = get_resolver()
    traverse(resolver.url_patterns)

    return grouped_routes
