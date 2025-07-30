'''*************************************************************************************************
Name: colgroup.py                      Author: Brendan Furey                       Date: 08-Oct-2022

Component package in the 'Trapit - Python Unit Testing' module, which facilitates unit testing in
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
|  testcolgroup    | *colgroup*   |  to file. Example of testing impure units, and failing test    |
|------------------|--------------|----------------------------------------------------------------|
|  testtrapit      |  trapit      |  Unit test package with test driver utility, and test script   |
|                  |              |  that uses the utility to test itself                          |
====================================================================================================

This file contains a simple file-reading and group-counting module, with logging to file. It
consists of a private function and a public class, ColGroup.

*************************************************************************************************'''
import sys, os
from datetime import datetime
from utils_cg import *
'''*************************************************************************************************

_readList: Private function returns the key-value map of (string, count) read from file

*************************************************************************************************'''
def _readList(file,  # input file name
              delim, # field delimiter
              col):  # 0-based column index
    counter = {}
    with open(file + '.log', 'a') as logfile:
        logfile.write(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') + ": File " + file + \
            ', delimiter \'' +delim + '\', column ' + str(col) + "\n")
    with open(file) as f:
        next(f) # skip header line
        for line in f:
            val = line.rstrip().split (delim)[int(col)]
            counter[val] = counter.get(val, 0) + 1 # +=1 doesn't work
    return counter

class ColGroup:

    '''************************************************************************************************

    __init__: Constructor sets the key-value map of (string, count), via _readList, and the maximum key
              length

    ************************************************************************************************'''
    def __init__(self,       # standard self parameter
                 input_file, # input file name
                 delim,      # field delimiter
                 col):       # 0-based column index
        self.counter = _readList (input_file, delim, col)
        global max_len
        max_len = 0
        if (len(self.counter.keys()) > 0):
            max_len = len(max(self.counter.keys(), key=len))

    '''************************************************************************************************

    pr_list: Prints the key-value list of (string, count) tuples, with sort method in heading

    ************************************************************************************************'''
    def pr_list(self,        # standard self parameter
                sort_by,     # sort method
                key_values): # key-value list of (string, count)
        print(heading ('Counts sorted by '+sort_by))
#        map(print, col_headers([['Team',-max_len], ['#apps',5]]))
        [print(l) for l in col_headers([['Team',-max_len], ['#apps',5]])]
        for k, v in key_values:
            print(line_from_2lis([[k, -max_len], [v, 5]]))
#            print(('{0:<'+str(max_len)+'s}  {1:5d}').format(k, v))

    '''************************************************************************************************

    list_as_is: Returns the key-value list of (string, count) tuples unsorted

    ************************************************************************************************'''
    def list_as_is(self): # standard self parameter
        return [(k, v) for k, v in self.counter.items()]

    '''************************************************************************************************

    sort_by_key: Returns the key-value list of (string, count) tuples sorted by key

    ************************************************************************************************'''
    def sort_by_key(self): # standard self parameter
        return [(k, v) for k, v in sorted(self.counter.items())]

    '''************************************************************************************************

    sort_by_value_lambda: Returns the key-value list of (string, count) tuples sorted by value

    ************************************************************************************************'''
    def sort_by_value_lambda(self): # standard self parameter
        return [(k, v) for k, v in sorted(self.counter.items(), key=lambda item : (item[1],item[0]))]
