"""
Implementation of all of the individual 'twill' commands available through
twill-sh.
"""

import sys
from twill import logconfig
import mechanize
from mechanize._headersutil import is_html
from lxml.html.soupparser import fromstring
import collections

logger = logconfig.logger

# export:
__all__ = ['get_browser',
           'reset_browser',
           'extend_with',
           'exit',
           'go',
           'reload',
           'url',
           'code',
           'follow',
           'find',
           'notfind',
           'back',
           'show',
           'echo',
           'save_html',
           'sleep',
           'agent',
           'showforms',
           'showlinks',
           'showhistory',
           'submit',
           'formvalue',
           'fv',
           'formaction',
           'fa',
           'formclear',
           'formfile',
           'getinput',
           'getpassword',
           'save_cookies',
           'load_cookies',
           'clear_cookies',
           'show_cookies',
           'add_auth',
           'run',
           'runfile',
           'setglobal',
           'setlocal',
           'debug',
           'title',
           'exit',
           'config',
           'tidy_ok',
           'redirect_output',
           'reset_output',
           'redirect_error',
           'reset_error',
           'add_extra_header',
           'show_extra_headers',
           'clear_extra_headers',
           'info'
           ]

import re, getpass, time

from .browser import TwillBrowser

from .errors import TwillException, TwillAssertionError
from . import utils
from .utils import set_form_control_value, run_tidy
from .namespaces import get_twill_glocals
        
browser = TwillBrowser()

def get_browser():
    return browser

def reset_browser():
    """
    >> reset_browser

    Reset the browser completely.
    """
    global browser
    browser._browser.close()
    browser = TwillBrowser()

    global _options
    _options = {}
    _options.update(_orig_options)

###

def exit(code="0"):
    """
    exit [<code>]

    Exits twill, with the given exit code (defaults to 0, "no error").
    """
    raise SystemExit(int(code))

def go(url):
    """
    >> go <url>
    
    Visit the URL given.
    """
    browser.go(url)
    return browser.get_url()

def reload():
    """
    >> reload
    
    Reload the current URL.
    """
    browser.reload()
    return browser.get_url()

def code(should_be):
    """
    >> code <int>
    
    Check to make sure the response code for the last page is as given.
    """
    should_be = int(should_be)
    if browser.get_code() != int(should_be):
        raise TwillAssertionError("code is %s != %s" % (browser.get_code(),
                                                        should_be))

def tidy_ok():
    """
    >> tidy_ok

    Assert that 'tidy' produces no warnings or errors when run on the current
    page.

    If 'tidy' cannot be run, will fail silently (unless 'tidy_should_exist'
    option is true; see 'config' command).
    """
    page = browser.get_html()
    if page is None:
        raise TwillAssertionError("not viewing HTML!")
        
    (clean_page, errors) = run_tidy(page)
    if clean_page is None:              # tidy doesn't exist...
        if _options.get('tidy_should_exist'):
            raise TwillAssertionError("cannot run 'tidy'")
    elif errors:
        raise TwillAssertionError("tidy errors:\n====\n%s\n====\n" % (errors,))

    # page is fine.

def url(should_be):
    """
    >> url <regexp>

    Check to make sure that the current URL matches the regexp.  The local
    variable __match__ is set to the matching part of the URL.
    """
    regexp = re.compile(should_be)
    current_url = browser.get_url()

    m = None
    if current_url is not None:
        m = regexp.search(current_url)
    else:
        current_url = ''

    if not m:
        raise TwillAssertionError("""\
current url is '%s';
does not match '%s'
""" % (current_url, should_be,))

    if m.groups():
        match_str = m.group(1)
    else:
        match_str = m.group(0)

    global_dict, local_dict = get_twill_glocals()
    local_dict['__match__'] = match_str
    return match_str

def follow(what):
    """
    >> follow <regexp>
    
    Find the first matching link on the page & visit it.
    """
    regexp = re.compile(what)
    link = browser.find_link(regexp)

    if link:
        browser.follow_link(link)
        return browser.get_url()

    raise TwillAssertionError("no links match to '%s'" % (what,))

def _parseFindFlags(flags):
    KNOWN_FLAGS = {
        'i': re.IGNORECASE,
        'm': re.MULTILINE,
        's': re.DOTALL,
        }
    finalFlags = 0
    for char in flags:
        try:
            finalFlags |= KNOWN_FLAGS[char]
        except IndexError:
            raise TwillAssertionError("unknown 'find' flag %r" % char)
    return finalFlags

def find(what, flags=''):
    """
    >> find <regexp> [<flags>]
    
    Succeed if the regular expression is on the page.  Sets the local
    variable __match__ to the matching text.

    Flags is a string consisting of the following characters:

    * i: ignorecase
    * m: multiline
    * s: dotall
    * x: uses XPath

    For explanations of these, please see the Python re module
    documentation.
    """
    page = browser.get_html()
    _, local_dict = get_twill_glocals()
    if 'x' not in flags:
        regexp = re.compile(what, _parseFindFlags(flags))

        m = regexp.search(page)
        if not m:
            raise TwillAssertionError("no match to '%s'" % (what,))

        if m.groups():
            match_str = m.group(1)
        else:
            match_str = m.group(0)

        local_dict['__match__'] = match_str
    else:
        tree = fromstring(page)
        elements = tree.xpath(what)
        if not elements:
            raise TwillAssertionError("no element to path '%s'" % (what,))

        local_dict['__match__'] = str(elements[0])

def notfind(what, flags=''):
    """
    >> notfind <regexp> [<flags>]
    
    Fail if the regular expression is on the page.
    """
    try:
        find(what, flags)
    except TwillAssertionError:
        pass
    else:
        raise TwillAssertionError("match to '%s'" % (what,))
    

def back():
    """
    >> back
    
    Return to the previous page.
    """
    browser.back()
    return browser.get_url()

def show():
    """
    >> show
    
    Show the HTML for the current page.
    """
    html = browser.get_html()
    print(html)
    return html

def echo(*strs):
    """
    >> echo <list> <of> <strings>
    
    Echo the arguments to the screen.
    """
    strs = list(map(str, strs))
    s = " ".join(strs)
    print(s)

def save_html(filename=None):
    """
    >> save_html [<filename>]
    
    Save the HTML for the current page into <filename>.  If no filename
    given, construct the filename from the URL.
    """
    html = browser.get_html()
    if html is None:
        logger.warning("No page to save.")
        return

    if filename is None:
        url = browser.get_url()
        url = url.split('?')[0]
        filename = url.split('/')[-1]
        if filename is "":
            filename = 'index.html'

        logger.info("(Using filename '%s')", filename)

    f = open(filename, 'w')
    f.write(html)
    f.close()

def sleep(interval=1):
    """
    >> sleep [<interval>]

    Sleep for the specified amount of time.
    If no interval is given, sleep for 1 second.
    """
    time.sleep(float(interval))

_agent_map = dict(
    ie5='Mozilla/4.0 (compatible; MSIE 5.0; Windows NT 5.1)',
    ie55='Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.1)',
    ie6='Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
    moz17='Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7) Gecko/20040616',
    opera7='Opera/7.0 (Windows NT 5.1; U) [en]',
    konq32='Mozilla/5.0 (compatible; Konqueror/3.2.3; Linux 2.4.14; X11; i686)',
    saf11='Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/100 (KHTML, like Gecko) Safari/100',
    aol9='Mozilla/4.0 (compatible; MSIE 5.5; AOL 9.0; Windows NT 5.1)',)

def agent(what):
    """
    >> agent <agent>
    
    Set the agent string (identifying the browser brand).

    Some convenient shortcuts:
      ie5, ie55, ie6, moz17, opera7, konq32, saf11, aol9.
    """
    what = what.strip()
    agent = _agent_map.get(what, what)
    browser.set_agent_string(agent)

def submit(submit_button=None):
    """
    >> submit [<buttonspec>]
    
    Submit the current form (the one last clicked on) by clicking on the
    n'th submission button.  If no "buttonspec" is given, submit the current
    form by using the last clicked submit button.

    The form to submit is the last form clicked on with a 'formvalue' command.

    The button used to submit is chosen based on 'buttonspec'.  If 'buttonspec'
    is given, it's matched against buttons using the same rules that
    'formvalue' uses.  If 'buttonspec' is not given, submit uses the last
    submit button clicked on by 'formvalue'.  If none can be found,
    submit submits the form with no submit button clicked.
    """
    browser.submit(submit_button)

def showforms():
    """
    >> showforms
    
    Show all of the forms on the current page.
    """
    browser.showforms()
    return browser._browser.forms()

def showlinks():
    """
    >> showlinks
    
    Show all of the links on the current page.
    """
    browser.showlinks()
    return browser._browser.links()

def showhistory():
    """
    >> showhistory

    Show the browser history (what URLs were visited).
    """
    browser.showhistory()
    return browser._browser._history
    
def formclear(formname):
    """
    >> formclear <formname>
    
    Run 'clear' on all of the controls in this form.
    """
    form = browser.get_form(formname)
    for control in form.controls:
        if control.readonly:
            continue

        control.clear()

def formvalue(formname, fieldname, value):
    """
    >> formvalue <formname> <field> <value>

    Set value of a form field.

    There are some ambiguities in the way formvalue deals with lists:
    'formvalue' will *add* the given value to a list of multiple selection,
    for lists that allow it.

    Forms are matched against 'formname' as follows:
      1. regexp match to actual form name;
      2. if 'formname' is an integer, it's tried as an index.

    Form controls are matched against 'fieldname' as follows:
      1. unique exact match to control name;
      2. unique regexp match to control name;
      3. if fieldname is an integer, it's tried as an index;
      4. unique & exact match to submit-button values.

    Formvalue ignores read-only fields completely; if they're readonly,
    nothing is done, unless the config options ('config' command) are
    changed.

    'formvalue' is available as 'fv' as well.
    """
    form = browser.get_form(formname)
    if not form:
        raise TwillAssertionError("no matching forms!")

    control = browser.get_form_field(form, fieldname)

    browser.clicked(form, control)

    if control.readonly and _options['readonly_controls_writeable']:
        logger.info('forcing read-only form field to writeable')
        control.readonly = False
        
    if control.readonly or isinstance(control, mechanize.IgnoreControl):
        logger.info('form field is read-only or ignorable; nothing done.')
        return

    if isinstance(control, mechanize.FileControl):
        raise TwillException('form field is for file upload; use "formfile" instead')

    set_form_control_value(control, value)

fv = formvalue

def formaction(formname, action):
    """
    >> formaction <formname> <action_url>

    Sets action parameter on form to action_url
    """
    form = browser.get_form(formname)
    form.action = action

fa = formaction

def formfile(formname, fieldname, filename, content_type=None):
    """
    >> formfile <form> <field> <filename> [ <content_type> ]

    Upload a file via an "upload file" form field.
    """
    import os.path
    filename = filename.replace('/', os.path.sep)

    form = browser.get_form(formname)
    control = browser.get_form_field(form, fieldname)

    if not control.is_of_kind('file'):
        raise TwillException('ERROR: field is not a file upload field!')

    browser.clicked(form, control)
    fp = open(filename, 'rb')
    control.add_file(fp, content_type, filename)

    logger.info('\nAdded file "%s" to file upload field "%s"\n',
            filename, control.name)

def extend_with(module_name):
    """
    >> extend_with <module>
    
    Import contents of given module.
    """
    global_dict, local_dict = get_twill_glocals()

    exec("from %s import *" % (module_name,), global_dict)

    ### now add the commands into the commands available for the shell,
    ### and print out some nice stuff about what the extension module does.

    import sys
    mod = sys.modules.get(module_name)

    ###

    import twill.shell, twill.parse
    
    fnlist = getattr(mod, '__all__', None)
    if fnlist is None:
        fnlist = [ fn for fn in dir(mod) if isinstance(getattr(mod, fn), collections.Callable) ]

    for command in fnlist:
        fn = getattr(mod, command)
        twill.shell.add_command(command, fn.__doc__)
        twill.parse.command_list.append(command)

    ###
    
    logger.info("Imported extension module '%s'.", module_name)
    logger.info("(at %s)\n", mod.__file__)

    if twill.shell.interactive:
        if mod.__doc__:
            logger.info("Description:\n\n%s\n", mod.__doc__.strip())
        else:
            if fnlist:
                logger.info('New commands:\n')
                for name in fnlist:
                    logger.info('\t %s', name)

                logger.info('')

def getinput(prompt):
    """
    >> getinput <prompt>
    Get input, store it in '__input__'.
    """
    _, local_dict = get_twill_glocals()

    inp = input(prompt)

    local_dict['__input__'] = inp
    return inp

def getpassword(prompt):
    """
    >> getpassword <prompt>
    
    Get a password ("invisible input"), store it in '__password__'.
    """
    _, local_dict = get_twill_glocals()

    inp = getpass.getpass(prompt)

    local_dict['__password__'] = inp
    return inp

def save_cookies(filename):
    """
    >> save_cookies <filename>

    Save all of the current cookies to the given file.
    """
    browser.save_cookies(filename)

def load_cookies(filename):
    """
    >> load_cookies <filename>

    Clear the cookie jar and load cookies from the given file.
    """
    browser.load_cookies(filename)

def clear_cookies():
    """
    >> clear_cookies

    Clear the cookie jar.
    """
    browser.clear_cookies()

def show_cookies():
    """
    >> show_cookies

    Show all of the cookies in the cookie jar.
    """
    browser.show_cookies()

def add_auth(realm, uri, user, passwd):
    """
    >> add_auth <realm> <uri> <user> <passwd>

    Add HTTP Basic Authentication information for the given realm/uri.
    """
    # swap around the type of HTTPPasswordMgr and
    # HTTPPasswordMgrWithDefaultRealm depending on if with_default_realm 
    # is on or not.
    if _options['with_default_realm']:
        realm = None

        if browser.creds.__class__ == mechanize.HTTPPasswordMgr:
            passwds = browser.creds.passwd
            browser.creds = mechanize.HTTPPasswordMgrWithDefaultRealm()
            browser.creds.passwd = passwds
            logger.info('Changed to using HTTPPasswordMgrWithDefaultRealm')
    else:
        if browser.creds.__class__ == mechanize.HTTPPasswordMgrWithDefaultRealm:
            passwds = browser.creds.passwd
            browser.creds = mechanize.HTTPPasswordMgr()
            browser.creds.passwd = passwds
            logger.info('Changed to using HTTPPasswordMgr')

    browser.creds.add_password(realm, uri, user, passwd)

    logger.info("Added auth info: realm '%s' / URI '%s' / user '%s'",
            realm, uri, user)

def debug(what, level):
    """
    >> debug <what> <level>

    <what> can be:
       * http (any level >= 1), to display the HTTP transactions.
       * commands (any level >= 1), to display the commands being executed.
       * equiv-refresh (any level >= 1) to display HTTP-EQUIV refresh handling.
    """
    from . import parse

    try:
        level = int(level)
    except ValueError:
        flag = utils.make_boolean(level)
        if flag:
            level = 1
        else:
            level = 0

    logger.debug('DEBUG: setting %s debugging to level %d', what, level)
    
    if what == "http":
        browser._browser.set_debug_http(level)
    elif what == 'equiv-refresh':
        if level:
            utils._debug_print_refresh = True
        else:
            utils._debug_print_refresh = False
    elif what == 'commands':
        if level:
            parse.debug_print_commands(True)
        else:
            parse.debug_print_commands(False)
    else:
        raise TwillException('unknown debugging type: "%s"' % (what,))

def run(cmd):
    """
    >> run <command>

    <command> can be any valid python command; 'exec' is used to run it.
    """
    # @CTB: use pyparsing to grok the command?  make sure that quoting works...
    
    # execute command.
    global_dict, local_dict = get_twill_glocals()
    
    from . import commands

    # set __url__
    local_dict['__cmd__'] = cmd
    local_dict['__url__'] = commands.browser.get_url()

    exec(cmd, global_dict, local_dict)

def runfile(*files):
    """
    >> runfile <file1> [ <file2> ... ]

    """
    from . import parse
    global_dict, local_dict = get_twill_glocals()

    for f in files:
        parse.execute_file(f, no_reset=True)

def setglobal(name, value):
    """
    setglobal <name> <value>

    Sets the variable <name> to the value <value> in the global namespace.
    """
    global_dict, local_dict = get_twill_glocals()
    global_dict[name] = value

def setlocal(name, value):
    """
    setlocal <name> <value>

    Sets the variable <name> to the value <value> in the local namespace.
    """
    global_dict, local_dict = get_twill_glocals()
    local_dict[name] = value

def title(what):
    """
    >> title <regexp>
    
    Succeed if the regular expression is in the page title.
    """
    regexp = re.compile(what)
    title = browser.get_title()

    logger.info("title is '%s'.", title)

    m = regexp.search(title)
    if not m:
        raise TwillAssertionError("title does not contain '%s'" % (what,))

    if m.groups():
        match_str = m.group(1)
    else:
        match_str = m.group(0)

    global_dict, local_dict = get_twill_glocals()
    local_dict['__match__'] = match_str
    return match_str

def redirect_output(filename):
    """
    >> redirect_output <filename>

    Append all twill output to the given file.
    """
    import twill
    fp = open(filename, 'a')
    twill.set_output(fp)

def reset_output():
    """
    >> reset_output

    Reset twill output to go to the screen.
    """
    import twill
    twill.set_output(None)

def redirect_error(filename):
    """
    >> redirect_error <filename>

    Append all twill error output to the given file.
    """
    import twill
    fp = open(filename, 'a')
    twill.set_errout(fp)

def reset_error():
    """
    >> reset_error
    
    Reset twill error output to go to the screen.
    """
    import twill
    twill.set_errout(None)

def add_extra_header(header_key, header_value):
    """
    >> add_header <name> <value>

    Add an HTTP header to each HTTP request.  See 'show_extra_headers' and
    'clear_extra_headers'.
    """
    browser._browser.addheaders += [(header_key, header_value)]

def show_extra_headers():
    """
    >> show_extra_headers

    Show any extra headers being added to each HTTP request.
    """
    l = browser._browser.addheaders

    if l:
        print('The following HTTP headers are added to each request:')
    
        for k, v in l:
            print(('  "%s" = "%s"' % (k, v,)))
            
        print()
    else:
        print('** no extra HTTP headers **')

def clear_extra_headers():
    """
    >> clear_extra_headers

    Remove all user-defined HTTP headers.  See 'add_extra_header' and
    'show_extra_headers'.
    """
    browser._browser.addheaders = []

### options

_orig_options = dict(readonly_controls_writeable=False,
                     use_tidy=True,
                     require_tidy=False,
                     use_BeautifulSoup=True,
                     require_BeautifulSoup=False,
                     allow_parse_errors=True,
                     with_default_realm=False,
                     acknowledge_equiv_refresh=True
                     )

_options = {}
_options.update(_orig_options)           # make a copy

def config(key=None, value=None):
    """
    >> config [<key> [<int value>]]

    Configure/report various options.  If no <value> is given, report
    the current key value; if no <key> given, report current settings.

    So far:

     * 'acknowledge_equiv_refresh', default 1 -- follow HTTP-EQUIV=REFRESH
     * 'readonly_controls_writeable', default 0 -- make ro controls writeable
     * 'require_tidy', default 0 -- *require* that tidy be installed
     * 'use_BeautifulSoup', default 1 -- use the BeautifulSoup parser
     * 'use_tidy', default 1 -- use tidy, if it's installed
     * 'with_default_realm', default 0 -- use a default realm for HTTP AUTH

    Deprecated:
     * 'allow_parse_errors' has been removed.
    """
    from . import utils
    
    if key is None:
        keys = list(_options.keys())
        keys.sort()

        logger.info('current configuration:')
        for k in keys:
            logger.info('\t%s : %s', k, _options[k])
        logger.info('')
    else:
        v = _options.get(key)
        if v is None:
            logger.error('*** no such configuration key %s', key)
            logger.error('valid keys are:', ";".join(list(_options.keys())))
            raise TwillException('no such configuration key: %s' % (key,))
        elif value is None:
            logger.info('')
            logger.info('key %s: value %s', key, v)
            logger.info('')
        else:
            value = utils.make_boolean(value)
            _options[key] = value
            if key == 'acknowledge_equiv_refresh':
	            browser.set_handle_equiv(value)

def info():
    """
    >> info

    Report information on current page.
    """
    current_url = browser.get_url()
    if current_url is None:
        logger.warning("We're not on a page!")
        return
    
    content_type = browser._browser._response.info().getheaders("content-type")
    check_html = is_html(content_type, current_url)

    code = browser.get_code()


    logger.info('\nPage information:')
    logger.info('\tURL: %s', current_url)
    logger.info('\tHTTP code: %s', code)
    m = ['\tContent type: ', content_type[0]]
    if check_html:
        m.append('(HTML)')
    logger.info("".join(m))
    if check_html:
        title = browser.get_title()
        logger.info('\tPage title: %s', title)

        forms = browser.get_all_forms()
        if len(forms):
            logger.info('\tThis page contains %d form(s)', len(forms))
            
    logger.info('')
