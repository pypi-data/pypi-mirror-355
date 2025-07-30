from xhtml2pdf import pisa


def generate_pdf(html_content, output_filename):
    with open(output_filename, "w+b") as result_file:
        pisa.CreatePDF(html_content, dest=result_file)
