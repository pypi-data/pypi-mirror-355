'''*************************************************************************************************
Name: trapit.py                        Author: Brendan Furey                       Date: 08-Oct-2022

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
|  testcolgroup    |  colgroup    |  to file. Example of testing impure units, and failing test    |
|------------------|--------------|----------------------------------------------------------------|
|  testtrapit      | *trapit*     |  Unit test package with test driver utility, and test script   |
|                  |              |  that uses the utility to test itself                          |
====================================================================================================

This file contains the trapit entry point function test_unit
*************************************************************************************************'''
import json, traceback

INP, OUT, EXP, ACT = 'inp', 'out', 'exp', 'act'
DELIM, EXCEPTION_GRP = '|',  'Unhandled Exception'

'''*************************************************************************************************

 _out_groups: Local function embeds input expected and acttual lists of values by group with 'exp'
                 and 'act' key objects

*************************************************************************************************'''
def _out_groups(exp_obj,  # expected value object with lists keyed by group name
                act_obj): # actual value object with lists keyed by group name

    exp_act_obj = {}
    for o in exp_obj:
        exp_act_obj[o] = {
            EXP : exp_obj[o],
            ACT : act_obj[o]
        }
    return exp_act_obj

'''*************************************************************************************************

 callPWU: Local function embeds input expected and actual lists of values by group with 'exp'
                 and 'act' key objects

*************************************************************************************************'''
def callPWU(delimiter, inp, out, purely_wrap_unit):

    act_obj = {}
    try:
        act_obj = purely_wrap_unit(inp)
        act_obj[EXCEPTION_GRP] = []
    except Exception as e:
        for o in out:
            act_obj[o] = []
        act_obj[EXCEPTION_GRP] = [f"{str(e)}{delimiter}{traceback.format_exc()}"]
    return act_obj

'''*************************************************************************************************

test_unit: Unit test driver function, called like this from a script that defines the function 
           purely_wrap_unit:

                test_unit(INP_JSON, OUT_JSON, purely_wrap_unit}

           This function reads metadata and scenario data from an input JSON file, calls a wrapper
           function passed as a parameter within a loop over scenarios, and writes an output JSON
           file based on the input file but with the actual outputs merged in. This can then be
           processed using the npm Trapit package to produce formatted test results.

           The driver function calls two functions:

           - purely_wrap_unit is a function passed in from the client unit tester that returns an 
           object with result output groups consisting of lists of delimited strings. It has two 
           parameters: (i) inp_groups: input groups object; (ii) sce: scenario (usually unused)
           - _out_groups is a local function that takes an input scenario object and the output from
           the function above and returns the complete output scenario with groups containing both
           expected and actual result lists
*************************************************************************************************'''
def test_unit(inp_file,          # input JSON file name
              out_file,          # output JSON file name
              purely_wrap_unit): # unit test wrapper function

    with open(inp_file, encoding='utf-8') as inp_f:
        inp_json_obj = json.loads(inp_f.read())
    
    meta, inp_scenarios = inp_json_obj['meta'], inp_json_obj['scenarios']
    out_scenarios = {}
    for s in inp_scenarios:
        if inp_scenarios[s].get('active_yn', 'Y') != 'N':
            out = inp_scenarios[s][OUT]
            out[EXCEPTION_GRP] = []
            out_scenarios[s] = {
                'category_set': inp_scenarios[s].get('category_set', ''),
                INP : inp_scenarios[s][INP],
                OUT : _out_groups(out, callPWU(meta.get('delimiter', '|'), inp_scenarios[s][INP], inp_scenarios[s][OUT], purely_wrap_unit))
            }
    meta[OUT][EXCEPTION_GRP] = ['Message', 'Stack']
    out_json_obj = {'meta': meta, 'scenarios': out_scenarios}
    with open(out_file, 'w') as out_f:
        json.dump(out_json_obj, out_f, indent=4)

def heading (title): # heading string
    return '\n' + title + '\n' + "="*len(title)

def test_format(ut_root,           # unit test root folder
                npm_root,          # parent folder of the JavaScript node_modules npm root folder
                stem_inp_json,     # input JSON file name stem
                purely_wrap_unit): # unit test wrapper function
    import subprocess
    inp_json = ut_root + '/' + stem_inp_json + '.json'
    out_json = ut_root + '/' + stem_inp_json + '_out.json'

    test_unit(inp_json, out_json, purely_wrap_unit)
    print(heading ('Results summary for file: ' + out_json))
    try:
        script = npm_root + '/node_modules/trapit/externals/format-external-file.js'
        result = subprocess.run(['node', script, out_json], check=True, capture_output=True, text=True)
        print(result.stdout)  # Print the output from the Node.js script
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")
