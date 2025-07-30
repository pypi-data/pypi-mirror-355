def generate_html(md_content, output_basename):
    html = f"""<html>
<head>
    <title>API Docs</title>
</head>
<body>
    <h1>📘 API Documentation</h1>
    <pre>{md_content}</pre>
</body>
</html>
"""
    with open(f"{output_basename}.html", "w", encoding="utf-8") as f:
        f.write(html)

