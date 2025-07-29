import logging
import sys
from pathlib import Path

import click
from codetiming import Timer
from fpdf import FPDF

from . import __version__ as app_version

# Setup logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()

# Constants
FORM_FEED = "\f"
LINE_FEED = "\n"
ONE_CM_IN_PT: float = (7200 / 254)
DEFAULT_LEFT_MARGIN = (0.2 * ONE_CM_IN_PT)
DEFAULT_TOP_MARGIN = (0.35 * ONE_CM_IN_PT)
TIMER_TEXT = "{name}: Elapsed time: {:.4f} seconds"


@click.command()
@click.option(
    "--version/--no-version",
    type=bool,
    default=False,
    show_default=False,
    required=True,
    help='Prints the "Text File to PDF" program version and exits.'
)
@click.option(
    "--input-file",
    type=str,
    required=True,
    help="The input text file to convert to PDF format.  The path can be relative or absolute."
)
@click.option(
    "--output-file",
    type=str,
    required=True,
    help="The output PDF file to create.  The path can be relative or absolute."
)
@click.option(
    "--orientation",
    type=click.Choice(['portrait', 'landscape'], case_sensitive=False),
    required=True,
    help="The page orientation to use for the PDF file."
)
@click.option(
    "--unit",
    type=click.Choice(["pt", "mm", "cm", "in"], case_sensitive=False),
    default="mm",
    show_default=True,
    required=True,
    help="The units to use for the PDF."
)
@click.option(
    "--format",
    type=click.Choice(["a3", "a4", "a5", "letter", "legal"], case_sensitive=False),
    default="letter",
    show_default=True,
    required=True,
    help="The page (paper) format for the PDF file."
)
@click.option(
    "--font-name",
    type=click.Choice(['courier', 'helvetica', 'times'], case_sensitive=False),
    default="courier",
    show_default=True,
    required=True,
    help="The font to use in the PDF file."
)
@click.option(
    "--font-size",
    type=int,
    default=9,
    show_default=True,
    required=True,
    help="The font-size to use in the PDF file."
)
@click.option(
    "--left-margin",
    type=float,
    default=DEFAULT_LEFT_MARGIN,
    show_default=True,
    required=True,
    help="The left margin for the PDF - in cm."
)
@click.option(
    "--top-margin",
    type=float,
    default=DEFAULT_TOP_MARGIN,
    show_default=True,
    required=True,
    help="The top margin for the PDF - in cm."
)
def main(version: bool,
         input_file: str,
         output_file: str,
         orientation: str,
         unit: str,
         format: str,
         font_name: str,
         font_size: int,
         left_margin: float,
         top_margin: float):
    if version:
        print(f"Text File to PDF - version: {app_version}")
        return

    with Timer(name=f"Converting text file: '{input_file}' to PDF file: '{output_file}'",
               text=TIMER_TEXT,
               initial_text=True,
               logger=logger.info
               ):
        try:
            text_file_contents = Path(input_file).read_text()

            page_list = text_file_contents.split(FORM_FEED)

            pdf = FPDF(orientation=orientation,
                       unit=unit,
                       format=format
                       )
            pdf.set_margins(left=left_margin, top=top_margin)
            pdf.set_auto_page_break(auto=False)
            pdf.set_font(family=font_name, size=font_size)

            for page in page_list:
                if page != "":
                    pdf.add_page()

                    line_list = page.split("\n")

                    for line in line_list:
                        if line != "":
                            pdf.cell(text=line)
                        pdf.ln()

            pdf.output(name=output_file)

            logger.info(msg=f"Text file: '{input_file}' was successfully converted to PDF file: '{output_file}'")

        except Exception as e:
            logger.error(
                msg=(f"An error occurred while converting the text file: '{input_file}' to a PDF file: '{output_file}'"
                     f"\nError text: {str(e)}"
                     )
            )
            raise


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
