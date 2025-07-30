import json


def generate_markdown(grouped_routes):
    md = "# 📘 API Documentation\n\n"
    for group_name, routes in grouped_routes.items():
        md += f"## {group_name.capitalize()} Endpoints\n\n"
        for route in routes:
            md += f"### `{route['path']}`\n"
            md += f"- **Methods**: {', '.join(route['methods'])}\n"
            md += f"- **Summary**: {route['summary']}\n"
            md += f"- **Endpoint**: `{route['endpoint']}`\n"
            if route.get("response_model_schema"):
                md += "- **Response Model Schema**:\n"
                md += "```json\n"
                try:
                    parsed = json.loads(route['response_model_schema']) \
                        if isinstance(route['response_model_schema'], str) \
                        else route['response_model_schema']
                    md += json.dumps(parsed, indent=2)
                except Exception:
                    md += route['response_model_schema']
                md += "\n```\n"
            if route.get("docstring"):
                md += f"- **Docstring**: {route['docstring']}\n"
            md += "\n---\n\n"
    return md
