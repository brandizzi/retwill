import twill.commands
from . import twilltestlib

def test():
    url = twilltestlib.get_url()

    twilltestlib.execute_twill_script('test-headers.twill', initial_url=url)
