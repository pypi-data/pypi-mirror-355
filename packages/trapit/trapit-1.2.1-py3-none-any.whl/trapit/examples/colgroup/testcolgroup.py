'''*************************************************************************************************
Name: testcolgroup.py                  Author: Brendan Furey                       Date: 08-Oct-2022

Component script in the 'Trapit - Python Unit Testing' module, which facilitates unit testing in
Oracle PL/SQL following 'The Math Function Unit Testing design pattern', as described here: 

    https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html

GitHub project for Python:

    https://github.com/BrenPatF/trapit_python_tester

At the heart of the design pattern there is a language-specific unit testing driver function. This
function reads an input JSON scenarios file, then loops over the scenarios making calls to a
function passed in as a parameter from the calling script. The passed function acts as a 'pure'
wrapper around calls to the unit under test. It is 'externally pure' in the sense that it is
deterministic, and interacts externally only via parameters and return value. Where the unit under
test reads inputs from file the wrapper writes them based on its parameters, and where the unit
under test writes outputs to file the wrapper reads them and passes them out in its return value.
Any file writing is reverted before exit.

The driver function accumulates the output scenarios containing both expected and actual results
in an object, from which a JavaScript function writes the results in HTML and text formats.

In testing of non-JavaScript programs, the results object is written to a JSON file to be passed
to the JavaScript formatter. In Python, the entry-point API, test_format, calls test_unit to write
the JSON file, then calls the JavaScript formatter, format-external-file.js.

The table shows the driver scripts for the relevant package: There are two examples of use, with
main and test drivers, and a test driver for the test_unit function.
====================================================================================================
|  Main/Test       |  Unit Module |  Notes                                                         |
|==================================================================================================|
|  mainhelloworld  |              |  Hello World program implemented as a pure function to allow   |
|  testhelloworld  |  helloworld  |  for unit testing as a simple edge case                        |
|------------------|--------------|----------------------------------------------------------------|
|  maincolgroup    |  utils_cg    |  Simple file-reading and group-counting module, with logging   |
| *testcolgroup*   |  colgroup    |  to file. Example of testing impure units, and failing test    |
|------------------|--------------|----------------------------------------------------------------|
|  testtrapit      |  trapit      |  Unit test package with test driver utility, and test script   |
|                  |              |  that uses the utility to test itself                          |
====================================================================================================

This file is a unit test script for a simple file-reading and group-counting module, with logging to 
file. Note that this example has two deliberate errors to show how these are handled.

To run from root folder:

$ py examples/colgroup/testcolgroup.py

*************************************************************************************************'''
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import trapit, colgroup as cg

ROOT = os.path.dirname(__file__)
DELIM = '|'

INPUT_FILE,            LOG_FILE,                    NPM_ROOT = \
ROOT + '/ut_group.csv', ROOT + '/ut_group.csv.log', ROOT + '/../../powershell_utils/TrapitUtils'

GRP_LOG,   GRP_SCA,   GRP_LIN, GRP_LAI,    GRP_SBK,     GRP_SBV       = \
'Log',     'Scalars', 'Lines', 'listAsIs', 'sortByKey', 'sortByValue'

def from_CSV(csv,  # string of delimited values
             col): # 0-based column index
    return csv.split(DELIM)[col]
def join_tuple(t): # 2-tuple
    return t[0] + DELIM + str(t[1])

def setup(inp): # input groups object
    with open(INPUT_FILE, 'w') as infile:
        infile.write('\n'.join(inp[GRP_LIN]))
    if (len(inp[GRP_LOG]) > 0):
        with open(LOG_FILE, 'w') as logfile:
            logfile.write('\n'.join(inp[GRP_LOG]) + '\n')
    return cg.ColGroup(INPUT_FILE, from_CSV(inp[GRP_SCA][0], 0), from_CSV(inp[GRP_SCA][0], 1))

def teardown():
    os.remove(INPUT_FILE)
    os.remove(LOG_FILE)

def purely_wrap_unit(inp_groups): # input groups object
    if (from_CSV(inp_groups[GRP_SCA][0], 2) == 'Y'):
        raise Exception('Error thrown')

    col_group   = setup(inp_groups)
    with open(LOG_FILE, 'r') as logfile:
        logstr = logfile.read()
    lines_array = logstr.split('\n')
    lastLine   = lines_array[len(lines_array) - 2]
    text       = lastLine
    date       = lastLine[0:19]
    logDate    = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    now        = datetime.now()
    diffDate   = (now - logDate).microseconds / 1000

    teardown()
    return {
        GRP_LOG : [str((len(lines_array) - 1)) + DELIM + str(diffDate) + DELIM + text.replace("\\", "-")],
        GRP_LAI : [str(len(col_group.list_as_is()))],
        GRP_SBK : list(map(join_tuple, col_group.sort_by_key())),
        GRP_SBV : list(map(join_tuple, col_group.sort_by_value_lambda()))
    }
trapit.test_format(ROOT,  NPM_ROOT, 'colgroup', purely_wrap_unit)
