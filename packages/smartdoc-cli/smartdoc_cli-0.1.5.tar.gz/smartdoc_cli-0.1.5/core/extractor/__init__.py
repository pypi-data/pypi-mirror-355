def get_extractor(framework):
    if framework == 'fastapi':
        from .fastapi_extractor import extract_routes
    elif framework == 'flask':
        from .flask_extractor import extract_routes
    elif framework == 'django':
        from .django_extractor import extract_routes
    else:
        raise ValueError("Unsupported framework")
    return extract_routes