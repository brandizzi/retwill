from . import twilltestlib
import mechanize
from .mechanize_parse_file import parse_file
from io import StringIO

def test_form_parse():
    content = "&rsaquo;"
    fp = StringIO(content)

    # latin-1...
    parse_file(fp, "<test-encoding.py fp>", encoding='latin-1',
						backwards_compat=False)
