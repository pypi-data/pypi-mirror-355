'''*************************************************************************************************
Name: utils_cg.py                      Author: Brendan Furey                       Date: 08-Oct-2022

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
|  maincolgroup    | *utils_cg*   |  Simple file-reading and group-counting module, with logging   |
|  testcolgroup    |  colgroup    |  to file. Example of testing impure units, and failing test    |
|------------------|--------------|----------------------------------------------------------------|
|  testtrapit      |  trapit      |  Unit test package with test driver utility, and test script   |
|                  |              |  that uses the utility to test itself                          |
====================================================================================================

This file has general utility functions for pretty printing.

*************************************************************************************************'''

'''*************************************************************************************************

rJust, lJust: Right/left-justify a string or number, using val_just to validate input

*************************************************************************************************'''
def val_just(val, s_width): # string to print, width
    strval = str(val)
    if s_width < len(strval):
        raise ValueError("*_just passed invalid parameters: " + strval + ", " + str(s_width))
    return [strval, ' '*(s_width - len(strval))]

def r_just(val, s_width): # string to print, width
    vals = val_just(val, s_width)
    return vals[1] + vals[0]
 
def l_just(val, s_width): # string to print, width
    vals = val_just(val, s_width)
    return vals[0] + vals[1]

'''*************************************************************************************************

heading: Returns a title with "=" underlining to its length, preceded by a blank line

*************************************************************************************************'''
def heading (title): # heading string
    return '\n' + title + '\n' + "="*len(title)

'''*************************************************************************************************

col_headers: Returns a set of column headers, input as array of value, length/justification tuples

*************************************************************************************************'''
def col_headers (col_names): # array of value, length/justification tuples
    strings = list(map(lambda c: l_just(c[0], -int(c[1])) if int(c[1]) < 0 else r_just(c[0], int(c[1])), col_names))
    lines = ['  '.join(strings)]
    unders = list(map(lambda s: '-'*len(s), strings))
    lines.append('  '.join(unders))
    return lines

'''*************************************************************************************************

line_from_2lis: Returns a line of values, input as array of value, length/justification tuples

*************************************************************************************************'''

def line_from_2lis (values_2lis): # array of value, length/justification tuples
    strings = list(map(lambda v: l_just(v[0], -int(v[1])) if int(v[1]) < 0 else r_just(v[0], int(v[1])), values_2lis))
    return '  '.join(strings)
