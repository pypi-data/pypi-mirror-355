import sys
import os
import click
from importlib import import_module

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.extractor.flask_extractor import extract_flask
from core.extractor.fastapi_extractor import extract_fastapi
from core.extractor.django_extractor import extract_django
from core.html import generate_html
from core.markdown import generate_markdown
from core.pdf import generate_pdf


@click.group()
def cli():
    """SmartDoc CLI for generating API documentation."""
    pass


@click.command(name="generate")
@click.option(
    "--app", "-a",
    required=True,
    help="App module path (e.g., sample_app.main)"
)
@click.option(
    "--framework", "-f",
    required=True,
    type=click.Choice(["fastapi", "django", "flask"]),
    help="Framework used in the app"
)
@click.option(
    "--output", "-o",
    default="api_docs.md",
    help="Output markdown filename"
)
@click.option(
    "--html", is_flag=True,
    help="Also generate an HTML file"
)
@click.option(
    "--pdf", is_flag=True,
    help="Also generate a PDF file"
)
@click.option(
    "--django-settings",
    help="Django settings module",
    default=None
)
def generate(app, framework, output, html, pdf, django_settings):
    """Generate API documentation."""
    print(f"Loading app: {app} using {framework}")
    module = import_module(app.replace("/", ".").rstrip(".py"))

    if framework == "fastapi":
        app_instance = getattr(module, "app", None)
        if not app_instance:
            print("Could not find FastAPI `app` in the given module.")
            sys.exit(1)
        routes = extract_fastapi(app_instance)

    elif framework == "django":
        if django_settings:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", django_settings)
            import django
            django.setup()
        routes = extract_django(module)

    elif framework == "flask":
        app_instance = getattr(module, "app", None)
        if not app_instance:
            print("Could not find Flask `app` in the given module.")
            sys.exit(1)
        routes = extract_flask(app_instance)

    else:
        print("Unsupported framework.")
        sys.exit(1)

    print("Routes extracted successfully.")
    md_content = generate_markdown(routes)

    with open(output, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown written to {output}")

    if html:
        generate_html(md_content, output.replace(".md", ""))
        print(f"HTML written to {output.replace('.md', '.html')}")

    if pdf:
        generate_pdf(md_content, output.replace(".md", ""))
        print(f"PDF written to {output.replace('.md', '.pdf')}")


cli.add_command(generate)

if __name__ == "__main__":
    cli()
