# Trapit - Python Unit Testing Module
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/mountains.png">

> The Math Function Unit Testing design pattern, implemented in Python

:detective:

This module supports [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html), a design pattern that can be applied in any language, and is here implemented in Python. The module name is derived from 'TRansactional API Testing' (TRAPIT), and the 'unit' should be considered to be a transactional unit. The pattern avoids microtesting, is data-driven, and fully supports multi-scenario testing and refactoring.

The Python Trapit module provides a generic driver program for unit testing, with test data read from an input JSON file, results written to an output JSON file, and all specific test code contained in a callback function passed to the driver function.

Unit test results are formatted by a JavaScript program that takes the JSON output results file as its input, [Trapit - JavaScript Unit Testing/Formatting Utilities Module](https://github.com/BrenPatF/trapit_nodejs_tester), and renders the results in HTML and text formats.

There is also a PowerShell module, [Trapit - PowerShell Unit Testing Utilities Module](https://github.com/BrenPatF/powershell_utils/tree/master/TrapitUtils), with a utility to generate a template for the JSON input file used by the design pattern, based on simple input CSV files.

This blog post, [Unit Testing, Scenarios and Categories: The SCAN Method](https://brenpatf.github.io/2021/10/17/unit-testing-scenarios-and-categories-the-scan-method.html) provides guidance on effective selection of scenarios for unit testing.

There is an extended Usage section below that illustrates the use of the design pattern for Python unit testing by means of two examples.

# In This README...
[&darr; Background](#background)<br />
[&darr; Usage](#usage)<br />
[&darr; API](#api)<br />
[&darr; Installation](#installation)<br />
[&darr; Unit Testing](#unit-testing)<br />
[&darr; Folder Structure](#folder-structure)<br />
[&darr; See Also](#see-also)<br />

## Background
[&uarr; In This README...](#in-this-readme)<br />

I explained the concepts for the unit testing design pattern in relation specifically to database testing in a presentation at the Oracle User Group Ireland Conference in March 2018:

- [The Database API Viewed As A Mathematical Function: Insights into Testing](https://www.slideshare.net/brendanfurey7/database-api-viewed-as-a-mathematical-function-insights-into-testing)

I later named the approach [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html) when I applied it in Javascript and wrote a JavaScript program to format results both in plain text and as HTML pages:
- [Trapit - JavaScript Unit Testing/Formatting Utilities Module](https://github.com/BrenPatF/trapit_nodejs_tester)

The module also allowed for the formatting of results obtained from testing in languages other than JavaScript by means of an intermediate output JSON file. In 2021 I developed a powershell module that included a utility to generate a template for the JSON input scenarios file required by the design pattern:
- [Trapit - PowerShell Unit Testing Utilities Module](https://github.com/BrenPatF/powershell_utils/tree/master/TrapitUtils)

Also in 2021 I developed a systematic approach to the selection of unit test scenarios:
- [Unit Testing, Scenarios and Categories: The SCAN Method](https://brenpatf.github.io/2021/10/17/unit-testing-scenarios-and-categories-the-scan-method.html)

In early 2023 I extended both the the JavaScript results formatter, and the powershell utility to incorporate Category Set as a scenario attribute. Both utilities support use of the design pattern in any language, while the unit testing driver utility is language-specific and is currently available in Powershell, JavaScript, Python and Oracle PL/SQL versions.
## Usage
[&uarr; In This README...](#in-this-readme)<br />
[&darr; General Usage](#general-usage)<br />
[&darr; Example 1 - Hello World](#example-1---hello-world)<br />
[&darr; Example 2 - ColGroup](#example-2---colgroup)<br />

As noted above, the JavaScript module allows for unit testing of JavaScript programs and also the formatting of test results for both JavaScript and non-JavaScript programs. Similarly, the PowerShell module mentioned allows for unit testing of PowerShell programs, and also the generation of the JSON input scenarios file template for testing in any language.

In this section we'll start by describing the steps involved in [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html) at an overview level. This will show how the generic PowerShell and JavaScript utilities fit in alongside the language-specific driver utilities.

Then we'll show how to use the design pattern in unit testing Python programs by means of two simple examples.

### General Usage
[&uarr; Usage](#usage)<br />
[&darr; General Description](#general-description)<br />
[&darr; Unit Testing Process](#unit-testing-process)<br />
[&darr; Unit Test Results](#unit-test-results)<br />

At a high level [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html) involves three main steps:

1. Create an input file containing all test scenarios with input data and expected output data for each scenario
2. Create a results object based on the input file, but with actual outputs merged in, based on calls to the unit under test
3. Use the results object to generate unit test results files formatted in HTML and/or text

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/HLS.png">

#### General Description
[&uarr; General Usage](#general-usage)<br />

The first and third of these steps are supported by generic utilities that can be used in unit testing in any language. The second step uses a language-specific unit test driver utility.

For non-JavaScript programs the results object is materialized using a library package in the relevant language. The diagram below shows how the processing from the input JSON file splits into two distinct steps:
- First, the output results object is created using the external library package which is then written to a JSON file
- Second, a script from the Trapit JavaScript library package is run, passing in the name of the output results JSON file

This creates a subfolder with name based on the unit test title within the file, and also outputs a summary of the results. The processing is split between three code units:
- Test Unit: External library function that drives the unit testing with a callback to a specific wrapper function
- Specific Test Package: This has a 1-line main program to call the library driver function, passing in the callback wrapper function
- Unit Under Test (API): Called by the wrapper function, which converts between its specific inputs and outputs and the generic version used by the library package

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/PFD-Ext.png">

In the first step the external program creates the output results JSON file, while in the second step the file is read into an object by the Trapit library package, which then formats the results.

#### Unit Testing Process
[&uarr; General Usage](#general-usage)<br />
[&darr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file)<br />
[&darr; Step 2: Create Results Object](#step-2-create-results-object)<br />
[&darr; Step 3: Format Results](#step-3-format-results)<br />

This section details the three steps involved in following [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html).

##### Step 1: Create Input Scenarios File
[&uarr; Unit Testing Process](#unit-testing-process)<br />
[&darr; Unit Test Wrapper Function](#unit-test-wrapper-function)<br />
[&darr; Scenario Category ANalysis (SCAN)](#scenario-category-analysis-scan)<br />
[&darr; Creating the Input Scenarios File](#creating-the-input-scenarios-file)<br />

Step 1 requires analysis to determine the extended signature for the unit under test, and to determine appropriate scenarios to test.

It may be useful during the analysis phase to create two diagrams, one for the extended signature:
- JSON Structure Diagram: showing the groups with their fields for input and output

and another for the category sets and categories:
- Category Structure Diagram: showing the category sets identified with their categories

You can see examples of these diagrams later in this document: [JSON Structure Diagram](#unit-test-wrapper-function-2) and [Category Structure Diagram](#scenario-category-analysis-scan-2), and schematic versions in the next two subsections.

###### Unit Test Wrapper Function
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file)<br />

Here is a schematic version of a JSON structure diagram, which in a real instance will  in general have multiple input and output groups, each with multiple fields:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/JSD-Example.png">

Each group in the diagram corresponds to a property within the inp_groups input object or out_groups return value object of the wrapper function, and contains an array of the group records stored as delimited strings.

```py
def purely_wrap_unit(inp_groups): # input groups object
    ...
    return out_groups
}
```

###### Scenario Category ANalysis (SCAN)
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file)<br />

The art of unit testing lies in choosing a set of scenarios that will produce a high degree of confidence in the functioning of the unit under test across the often very large range of possible inputs.

A useful approach can be to think in terms of categories of inputs, where we reduce large ranges to representative categories, an idea I explore in this article:

- [Unit Testing, Scenarios and Categories: The SCAN Method](https://brenpatf.github.io/2021/10/17/unit-testing-scenarios-and-categories-the-scan-method.html)

Here is a schematic version of a category set diagram, which in a real instance will  in general have multiple category sets, each with multiple categories:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/CSD-Example.png">

Each category i-j in the diagram corresponds to a scenario j for category set i.

###### Creating the Input Scenarios File
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file)<br />

The results of the analysis can be summarised in three CSV files which  a PowerShell program uses as inputs to create a template for the JSON file.

The PowerShell API, `Write-UT_Template` creates a template for the JSON file, with the full meta section, and a set of template scenarios having name as scenario key, a category set attribute, and zero or more records with default values for each input and output group. The API takes as inputs three CSV files:
  - `stem`\_inp.csv: list of group, field, values tuples for input
  - `stem`\_out.csv: list of group, field, values tuples for output
  - `stem`\_sce.csv: scenario triplets - (Category set, scenario name, active flag); this file is optional

In the case where a scenarios file is present, each group has zero or more records with field values taken from the group CSV files, with a record for each value column present where at least one value is not null for the group. The template scenario represents a kind of prototype scenario, where records may be manually updated (and added or subtracted) to reflect input and expected output values for the actual scenario being tested.

The API can be run with the following PowerShell in the folder of the CSV files:

###### Format-JSON-Stem.ps1
```powershell
Import-Module TrapitUtils
Write-UT_Template 'stem' '|' 'title'
```
This creates the template JSON file, `stem`\_temp.json based on the CSV files having prefix `stem` and using the field delimiter '|', and including the unit test title passed. The PowerShell API can be used for testing in any language.

The template file is then updated manually with data appropriate to each scenario.

##### Step 2: Create Results Object
[&uarr; Unit Testing Process](#unit-testing-process)<br />

Step 2 requires the writing of a wrapper function that is passed into a unit test library function, test_unit, via the entry point API,  `test_format`. test_unit reads the input JSON file, calls the wrapper function for each scenario, and writes the output JSON file with the actual results merged in along with the expected results.

##### purely_wrap_unit
```py
def purely_wrap_unit(inp_groups): # input groups object
    ...
    return out_groups
}
```

The test driver API,  `test_format`, is language-specific, and this one is for testing Python programs. Equivalents exist under the same GitHub account (BrenPatF) for JavaScript, PowerShell and Oracle PL/SQL at present.

##### Step 3: Format Results
[&uarr; Unit Testing Process](#unit-testing-process)<br />

Step 3 involves formatting the results contained in the JSON output file from step 2, via the JavaScript formatter, and this step can be combined with step 2 for convenience.

- `test_format` is the function from the trapit Python package that calls the main test driver function that contains the wrapper function, then passes the output JSON file name to the JavaScript formatter and outputs a summary of the results. It takes as parameters:

    - `ut_root`: unit test root folder
    - `npm_root`: parent folder of the JavaScript node_modules npm root folder
    - `stem_inp_json`: input JSON file name stem
    - `purely_wrap_unit`: function to process unit test for a single scenario

    with return value:

    - summary of results

##### teststem.py
```powershell
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import trapit
ROOT = os.path.dirname(__file__)
DELIM = '|'
NPM_ROOT = ROOT + '/../../powershell_utils/TrapitUtils'
def purely_wrap_unit(inp_groups): # input groups object
    ...
    return {
        ...
    }
trapit.test_format(ROOT, NPM_ROOT, 'stem', purely_wrap_unit)
```

#### Unit Test Results
[&uarr; General Usage](#general-usage)<br />
[&darr; Unit Test Report - Scenario List](#unit-test-report---scenario-list)<br />
[&darr; Unit Test Report - Scenario Pages](#unit-test-report---scenario-pages)<br />

The script above creates a results subfolder, with results in text and HTML formats, in the script folder, and outputs a summary of the following form:

```
Results summary for file: [MY_PATH]/stem_out.json
=================================================

File:          stem_out.json
Title:         [Title]
Inp Groups:    [#Inp Groups]
Out Groups:    [#Out Groups]
Tests:         [#Tests]
Fails:         [#Fails]
Folder:        [Folder]
```

Within the results subfolder there is a text file containing a list of summary results at scenario level, followed by the detailed results for each scenario. In addition there are files providing the results in HTML format.

##### Unit Test Report - Scenario List
[&uarr; Unit Test Results](#unit-test-results)<br />

The scenario list page lists, for each scenario:

- \# - the scenario index
- Category Set - the category set applying to the scenario
- Scenario - a description of the scenario
- Fails (of N) - the number of groups failing, with N being the total number of groups
- Status - SUCCESS or FAIL

The scenario field is a hyperlink to the individual scenario page.

##### Unit Test Report - Scenario Pages
[&uarr; Unit Test Results](#unit-test-results)<br />

The page for each scenario has the following schematic structure:
```
SCENARIO i: Scenario [Category Set: (category set)]
  INPUTS
    For each input group: [Group name] - a heading line followed by a list of records
      For each field: Field name
      For each record: 1 line per record, with record number followed by:
        For each field: Field value for record
  OUTPUTS
    For each output group: [Group name] - a heading line followed by a list of records
      For each field: Field name
      For each record: 1 line per record, with record number followed by:
        For each field: Field expected value for record
        For each field: Field actual value for record (only if any actual differs from expected)
    Group status - #fails of #records: SUCCESS / FAIL
Scenario status - #fails of #groups: SUCCESS / FAIL
```
### Example 1 - Hello World
[&uarr; Usage](#usage)<br />
[&darr; Example Description](#example-description)<br />
[&darr; Unit Testing Process](#unit-testing-process-1)<br />
[&darr; Unit Test Results](#unit-test-results-1)<br />

The first example is a version of the 'Hello World' program traditionally used as a starting point in learning a new programming language. This is useful as it shows the core structures involved in following the design pattern with a minimalist unit under test.

#### Example Description
[&uarr; Example 1 - Hello World](#example-1---hello-world)<br />

This is a pure function form of Hello World program, returning a value rather than writing to screen itself. It is of course trivial, but has some interest as an edge case with no inputs and extremely simple JSON input structure and test code.

##### helloworld\.py
```py
def hello_world():
    return 'Hello World!'
```
There is a main script that shows how the function might be called outside of unit testing:

##### mainhelloworld\.py
```py
import helloworld as hw
print(hw.hello_world())
```

This can be called from a command window in the examples folder:
```py
$ py helloworld/mainhelloworld.py
```

with output to console:
```
Hello World!
```
#### Unit Testing Process
[&uarr; Example 1 - Hello World](#example-1---hello-world)<br />
[&darr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-1)<br />
[&darr; Step 2: Create Results Object](#step-2-create-results-object-1)<br />
[&darr; Step 3: Format Results](#step-3-format-results-1)<br />

##### Step 1: Create Input Scenarios File
[&uarr; Unit Testing Process](#unit-testing-process-1)<br />
[&darr; Unit Test Wrapper Function](#unit-test-wrapper-function-1)<br />
[&darr; Scenario Category ANalysis (SCAN)](#scenario-category-analysis-scan-1)<br />
[&darr; Creating the Input Scenarios File](#creating-the-input-scenarios-file-1)<br />

###### Unit Test Wrapper Function
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-1)<br />

Here is a diagram of the input and output groups for this example:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/JSD-HW.png">

From the input and output groups depicted we can construct CSV files with flattened group/field structures, and default values added, as follows (with `helloworld_inp.csv` left, `helloworld_out.csv` right):
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/groups - helloworld.png">

###### Scenario Category ANalysis (SCAN)
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-1)<br />

The Category Structure diagram for the Hello World example is of course trivial:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/CSD-HW.png">

It has just one scenario, with its input being void:

|  # | Category Set | Category | Scenario |
|---:|:-------------|:---------|:---------|
|  1 | Global       | No input | No input |

From the scenarios identified we can construct the following CSV file (`helloworld_sce.csv`), taking the category set and scenario columns, and adding an initial value for the active flag:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/scenarios - helloworld.png">

###### Creating the Input Scenarios File
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-1)<br />

The PowerShell API to generate a template JSON file can be run with the following PowerShell script in the folder of the CSV files:

###### Format-JSON-HelloWorld.ps1
```powershell
Import-Module ..\..\powershell_utils\TrapitUtils\TrapitUtils
Write-UT_Template 'helloworld_py' '|' 'Hello World - Python'
```
This creates the template JSON file, helloworld_temp.json, which contains an element for each of the scenarios, with the appropriate category set and active flag. In this case there is a single scenario, with empty input, and a single record in the output group with the default value from the output groups CSV file. Here is the complete file:

##### helloworld_temp.json
```js
{
  "meta": {
    "title": "Hello World - Python",
    "delimiter": "|",
    "inp": {},
    "out": {
      "Group": [
        "Greeting"
      ]
    }
  },
  "scenarios": {
    "No input": {
      "active_yn": "Y",
      "category_set": "Global",
      "inp": {},
      "out": {
        "Group": [
          "Hello World!"
        ]
      }
    }
  }
}
```

##### Step 2: Create Results Object
[&uarr; Unit Testing Process](#unit-testing-process-1)<br />

Step 2 requires the writing of a wrapper function that is passed into a unit test library function, test_unit, via the entry point API,  `test_format`. test_unit reads the input JSON file, calls the wrapper function for each scenario, and writes the output JSON file with the actual results merged in along with the expected results.

Here we use a lambda expression as the wrapper function is so simple:

###### Wrapper Function - Lambda Expression
```python
lambda inp_groups: {'Group': [helloworld.hello_world()]}
```

This lambda expression is included in the script testhelloworld.py and passed as a parameter to test_format.

##### Step 3: Format Results
[&uarr; Unit Testing Process](#unit-testing-process-1)<br />

Step 3 involves formatting the results contained in the JSON output file from step 2, via the JavaScript formatter, and this step can be combined with step 2 for convenience.

- `test_format` is the function from the trapit package that calls the main test driver function, then passes the output JSON file name to the JavaScript formatter and outputs a summary of the results.

###### testhelloworld.py
```python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import trapit, helloworld

trapit.test_format('./helloworld',  '../powershell_utils/TrapitUtils', 'helloworld', lambda inp_groups: {'Group': [helloworld.hello_world()]})
```
This script contains the wrapper function (here a lambda expression), passing it in a call to the trapit library function test_format.

#### Unit Test Results
[&uarr; Example 1 - Hello World](#example-1---hello-world)<br />
[&darr; Unit Test Report - Hello World](#unit-test-report---hello-world)<br />
[&darr; Scenario 1: No input](#scenario-1-no-input)<br />

The unit test script creates a results subfolder, with results in text and HTML formats, in the script folder, and outputs the following summary:

```
Results summary for file: [MY_PATH]/trapit_python_tester/examples/helloworld/helloworld_out.json
================================================================================================

File:          helloworld_out.json
Title:         Hello World - Python
Inp Groups:    0
Out Groups:    2
Tests:         1
Fails:         0
Folder:        hello-world---python
```

##### Unit Test Report - Hello World
[&uarr; Unit Test Results](#unit-test-results-1)<br />

Here we show the scenario-level summary of results for this example, and also show the detail for the only scenario.

You can review the HTML formatted unit test results here:

- [Unit Test Report: Hello World](http://htmlpreview.github.io/?https://github.com/BrenPatF/powershell_utils/blob/master/TrapitUtils/examples/helloworld/hello-world---powershell/hello-world---powershell.html)


This is the summary page in text format.

```
Unit Test Report: Hello World - Python
======================================

      #    Scenario  Fails (of 2)  Status
      ---  --------  ------------  -------
      1    Scenario  0             SUCCESS

Test scenarios: 0 failed of 1: SUCCESS
======================================
Formatted: 7/6/2025, 11:01:46
```

##### Scenario 1: No input
[&uarr; Unit Test Results](#unit-test-results-1)<br />

This is the scenario page in text format, with only one scenario.

```
SCENARIO 1: No input [Category Set: Global] {
=============================================
   INPUTS
   ======
   OUTPUTS
   =======
      GROUP 1: Group {
      ================
            #  Greeting
            -  ------------
            1  Hello World!
      } 0 failed of 1: SUCCESS
      ========================
      GROUP 2: Unhandled Exception: Empty as expected: SUCCESS
      ========================================================
} 0 failed of 2: SUCCESS
========================
```
Note that the second output group, 'Unhandled Exception', is not specified in the CSV file: In fact, this is generated by the test_unit API itself in order to capture any unhandled exception.
### Example 2 - ColGroup
[&uarr; Usage](#usage)<br />
[&darr; Example Description](#example-description-1)<br />
[&darr; Unit Testing Process](#unit-testing-process-2)<br />
[&darr; Unit Test Results](#unit-test-results-2)<br />

The second example, 'ColGroup', is larger and intended to show a wider range of features, but without too much extraneous detail.

#### Example Description
[&uarr; Example 2 - ColGroup](#example-2---colgroup)<br />

This example involves a class with a constructor function that reads in a CSV file and counts instances of distinct values in a given column. The constructor function appends a timestamp and call details to a log file. The class has methods to list the value/count pairs in several orderings.

##### colgroup\.py (skeleton)
```python
import sys, os
from datetime import datetime
from utils_cg import *
...
class ColGroup {
    ...
}
```

There is a main script that shows how the class might be called outside of unit testing:

##### maincolgroup.py
```python
import sys, os
import colgroup as cg

ROOT = os.path.dirname(__file__) + '/'
(input_file, delim, col) = ROOT + 'fantasy_premier_league_player_stats.csv', ',', 6

grp = cg.ColGroup(input_file, delim, col)
grp.pr_list('(as is)', grp.list_as_is())
grp.pr_list('key', grp.sort_by_key())
grp.pr_list('value (lambda)', grp.sort_by_value_lambda())
```
This can be called from a command window in the examples folder:

```python
$ py colgroup/maincolgroup.py
```
with output to console:

```
Counts sorted by (as is)
========================
Team         #apps
-----------  -----
West Brom     1219
Swansea       1180
Blackburn       33
...

Counts sorted by key
====================
Team         #apps
-----------  -----
Arsenal        534
Aston Villa    685
Blackburn       33
...
Counts sorted by value
======================
Team         #apps
-----------  -----
Wolves          31
Blackburn       33
Bolton          37
...
```
and to log file, fantasy_premier_league_player_stats.csv.log:
```
2023-04-10 08:02:43: File [MY_PATH]/trapit_python_tester/examples/colgroup/fantasy_premier_league_player_stats.csv, delimiter ',', column team_name
```

The example illustrates how a wrapper function can handle `impure` features of the unit under test:
- Reading input from file
- Writing output to file

...and also how the JSON input file can allow for nondeterministic outputs giving rise to deterministic test outcomes:
- By using regex matching for strings including timestamps
- By using number range matching and converting timestamps to epochal offsets (number of units of time since a fixed time)

#### Unit Testing Process
[&uarr; Example 2 - ColGroup](#example-2---colgroup)<br />
[&darr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-2)<br />
[&darr; Step 2: Create Results Object](#step-2-create-results-object-2)<br />
[&darr; Step 3: Format Results](#step-3-format-results-2)<br />

##### Step 1: Create Input Scenarios File
[&uarr; Unit Testing Process](#unit-testing-process-2)<br />
[&darr; Unit Test Wrapper Function](#unit-test-wrapper-function-2)<br />
[&darr; Scenario Category ANalysis (SCAN)](#scenario-category-analysis-scan-2)<br />
[&darr; Creating the Input Scenarios File](#creating-the-input-scenarios-file-2)<br />

###### Unit Test Wrapper Function
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-2)<br />

Here is a diagram of the input and output groups for this example:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/JSD-CG.png">

From the input and output groups depicted we can construct CSV files with flattened group/field structures, and default values added, as follows (with `colgrp_inp.csv` left, `colgrp_out.csv` right):
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/groups - colgroup.png">

The value fields shown correspond to a prototype scenario with records per group:

- Input
    - Log: 0
    - Scalars: 1
    - Lines: 4
- Output
    - Log: 1
    - Scalars: 1
    - listAsIs: 1
    - sortByKey: 2
    - sortByValue: 2

A PowerShell utility uses these CSV files, together with one for scenarios, discussed next, to generate a template for the JSON unit testing input file. The utility creates a prototype scenario dataset with a record in each group for each populated value column, that is used for each scenario in the template.

###### Scenario Category ANalysis (SCAN)
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-2)<br />

As noted earlier, a useful approach to scenario selection can be to think in terms of categories of inputs, where we reduce large ranges to representative categories.

###### Generic Category Sets - ColGroup

As explained in the article mentioned earlier, it can be very useful to think in terms of generic category sets that apply in many situations. Multiplicity is relevant here (as it often is):

###### Multiplicity

There are several entities where the generic category set of multiplicity applies, and we should check each of the None / One / Multiple instance categories.

| Code     | Description     |
|:--------:|:----------------|
| None     | No values       |
| One      | One value       |
| Multiple | Multiple values |

Apply to:
<ul>
<li>Lines</li>
<li>File Columns (one or multiple only)</li>
<li>Key Instance (one or multiple only)</li>
<li>Delimiter (one or multiple only)</li>
</ul>

###### Categories and Scenarios - ColGroup

After analysis of the possible scenarios in terms of categories and category sets, we can depict them on a Category Structure diagram:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/CSD-CG.png">

We can tabulate the results of the category analysis, and assign a scenario against each category set/category with a unique description:

|  # | Category Set              | Category            | Scenario                                 |
|---:|:--------------------------|:--------------------|:-----------------------------------------|
|  1 | Lines Multiplicity        | None                | No lines                                 |
|  2 | Lines Multiplicity        | One                 | One line                                 |
|  3 | Lines Multiplicity        | Multiple            | Multiple lines                           |
|  4 | File Column Multiplicity  | One                 | One column in file                       |
|  5 | File Column Multiplicity  | Multiple            | Multiple columns in file                 |
|  6 | Key Instance Multiplicity | One                 | One key instance                         |
|  7 | Key Instance Multiplicity | Multiple            | Multiple key instances                   |
|  8 | Delimiter Multiplicity    | One                 | One delimiter character                  |
|  9 | Delimiter Multiplicity    | Multiple            | Multiple delimiter characters            |
| 10 | Key Size                  | Short               | Short key                                |
| 11 | Key Size                  | Long                | Long key                                 |
| 12 | Log file existence        | No                  | Log file does not exist at time of call  |
| 13 | Log file existence        | Yes                 | Log file exists at time of call          |
| 14 | Key/Value Ordering        | No                  | Order by key differs from order by value |
| 15 | Key/Value Ordering        | Yes                 | Order by key same as order by value      |
| 16 | Errors                    | Mismatch            | Actual/expected mismatch                 |
| 17 | Errors                    | Unhandled Exception | Unhandled Exception                      |

From the scenarios identified we can construct the following CSV file (`colgrp_sce.csv`), taking the category set and scenario columns, and adding an initial value for the active flag:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/scenarios - colgroup.png">

###### Creating the Input Scenarios File
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-2)<br />

The API to generate a template JSON file can be run with the following PowerShell in the folder of the CSV files:

###### Format-JSON-ColGroup.ps1
```powershell
Import-Module ..\..\powershell_utils\TrapitUtils\TrapitUtils
Write-UT_Template 'colgroup_py' '|' 'ColGroup - Python'
```
This creates the template JSON file, colgroup_temp.json, which contains an element for each of the scenarios, with the appropriate category set and active flag, with a single record in each group with default values from the groups CSV files. Here is the "Multiple lines" element:

    "Multiple lines": {
      "active_yn": "Y",
      "category_set": "Lines Multiplicity",
      "inp": {
        "Log": [],
        "Scalars": [
          ",|1|"
        ],
        "Lines": [
          "col_0,col_1,col_2",
          "val_01,val_11,val_21",
          "val_02,val_12,val_22",
          "val_03,val_11,val_23"
        ]
      },
      "out": {
        "Log": [
          "1|IN [0,2000]|LIKE /.*: File .*ut_group.*.csv, delimiter ',', column 1/"
        ],
        "listAsIs": [
          "2"
        ],
        "sortByKey": [
          "val_11|2",
          "val_12|1"
        ],
        "sortByValue": [
          "val_12|1",
          "val_11|2"
        ]
      }
    },

For each scenario element, we need to update the values to reflect the scenario to be tested, in the actual input JSON file, colgroup.json. In the "Multiple lines" scenario above the prototype scenario data can be used as is, but in others it would need to be updated.

##### Step 2: Create Results Object
[&uarr; Unit Testing Process](#unit-testing-process-2)<br />

Step 2 requires the writing of a wrapper function that is passed into a unit test library function, test_unit, via the entry point API,  `test_format`. test_unit reads the input JSON file, calls the wrapper function for each scenario, and writes the output JSON file with the actual results merged in along with the expected results.

###### purely_wrap_unit
```python
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import trapit, colgroup as cg

ROOT = os.path.dirname(__file__) + '\\'
DELIM = '|'
INPUT_JSON,             OUTPUT_JSON,                INPUT_FILE,            LOG_FILE                  = \
ROOT + 'colgroup.json', ROOT + 'colgroup_out.json', ROOT + 'ut_group.csv', ROOT + 'ut_group.csv.log'
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
```

##### Step 3: Format Results
[&uarr; Unit Testing Process](#unit-testing-process-2)<br />

Step 3 involves formatting the results contained in the JSON output file from step 2, via the JavaScript formatter:
- `test_format` is the function from the trapit Python package that calls the main test driver function, then passes the output JSON file name to the JavaScript formatter and outputs a summary of the results.

###### testcolgroup.py (skeleton)

```python
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import trapit, colgroup as cg
ROOT = os.path.dirname(__file__)
DELIM = '|'
INPUT_FILE,            LOG_FILE,                    NPM_ROOT = \
ROOT + '/ut_group.csv', ROOT + '/ut_group.csv.log', ROOT + '/../../powershell_utils/TrapitUtils'
...
def purely_wrap_unit(inp_groups): # input groups object
    ...
    return {
        ...
    }
trapit.test_format(ROOT, NPM_ROOT, 'colgroup', purely_wrap_unit)
```
This script contains the wrapper function, passing it in a call to the trapit library function test_format.

#### Unit Test Results
[&uarr; Example 2 - ColGroup](#example-2---colgroup)<br />
[&darr; Unit Test Report - ColGroup](#unit-test-report---colgroup)<br />

The unit test script creates a results subfolder, with results in text and HTML formats, in the script folder, and outputs the following summary:
```
Results summary for file: [MY_PATH]/trapit_python_tester/examples/colgroup/colgroup_out.json
============================================================================================

File:          colgroup_out.json
Title:         ColGroup - Python
Inp Groups:    3
Out Groups:    5
Tests:         17
Fails:         2
Folder:        colgroup---python
```

##### Unit Test Report - ColGroup
[&uarr; Unit Test Results](#unit-test-results-2)<br />
[&darr; Scenario 16: Actual/expected mismatch [Category Set: Errors]](#scenario-16-actualexpected-mismatch-category-set-errors)<br />

Here we show the scenario-level summary of results for the specific example, and show the detail for one of the failing scenarios.

You can review the HTML formatted unit test results here:

- [Unit Test Report: ColGroup](http://htmlpreview.github.io/?https://github.com/BrenPatF/trapit_python_tester/blob/master/examples/colgroup/colgroup---python/colgroup---python.html)


This is a screenshot of the summary page in HTML format.
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/summary-colgroup.png">

###### Scenario 16: Actual/expected mismatch [Category Set: Errors]
[&uarr; Unit Test Report - ColGroup](#unit-test-report---colgroup)<br />

This scenario is designed to fail, with one of the expected values in group 4 set to 9999 instead of the correct value of 2,  just to show how mismatches are displayed.
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/scenario_16-colgroup.png">
## API
[&uarr; In This README...](#in-this-readme)<br />
[&darr; test_unit](#test_unit)<br />
[&darr; test_format](#test_format)<br />

```py
import trapit
```

### test_unit
[&uarr; API](#api)<br />
```
trapit.test_unit(inp_file, out_file, purely_wrap_unit)
```
Unit tests a unit using [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html) with input data read from a JSON file, and output results written to an output JSON file, with parameters:

- `inp_file`: JSON input file, with input and expected output data
- `out_file`: JSON output file, with input, expected and actual output data
- `purely_wrap_unit`: function to process unit test for a single scenario, passed in from test script, described below

#### purely_wrap_unit
```python
purely_wrap_unit(inp_groups)
```
Processes unit test for a single scenario, taking inputs as an object with input group data, making calls to the unit under test, and returning the actual outputs as an object with output group data, with parameters:

* object containing input groups with group name as key and list of delimited input records as value, of form:
<pre>
    {
        inp_group1: [rec1, rec2,...],
        inp_group2: [rec1, rec2,...],
        ...
    }
</pre>
Return value:

* object containing output groups with group name as key and list of delimited actual output records as value, of form:
<pre>
    {
        out_group1: [rec1, rec2,...],
        out_group2: [rec1, rec2,...],
        ...
    }
</pre>

This function acts as a 'pure' wrapper around calls to the unit under test. It is 'externally pure' in the sense that it is deterministic, and interacts externally only via parameters and return value. Where the unit under test reads inputs from file the wrapper writes them based on its parameters, and where the unit under test writes outputs to file the wrapper reads them and passes them out in its return value. Any file writing is reverted before exit.

test_unit is normally called via the test_format function, but is called directly in unit testing.

### test_format
[&uarr; API](#api)<br />
```
trapit.test_format(ut_root, npm_root, stem_inp_json, purely_wrap_unit)
```

The unit test driver utility function is called as effectively the main function of any specific unit test script. It calls test_unit, then calls the JavaScript formatter, which writes the formatted results files to a subfolder in the script folder, based on the title, returning a summary. It has parameters:

It has the following parameters:

- `ut_root`: unit test root folder
- `npm_root`: parent folder of the JavaScript node_modules npm root folder
- `stem_inp_json`: input JSON file name stem
- `purely_wrap_unit`: function to process unit test for a single scenario, passed in from test script, described in the section above for test_unit

Return value:

- summary of results
## Installation
[&uarr; In This README...](#in-this-readme)<br />
[&darr; Prerequisite Applications](#prerequisite-applications)<br />
[&darr; Python Installation - pip](#python-installation---pip)<br />

### Prerequisite Applications
[&uarr; Installation](#installation)<br />
[&darr; Node.js](#nodejs)<br />
[&darr; Powershell](#powershell)<br />

#### Node.js
[&uarr; Prerequisite Applications](#prerequisite-applications)<br />

The unit test results are formatted using a JavaScript program, which is included as part of the current project. Running the program requires the Node.js application:

- [Node.js Downloads](https://nodejs.org/en/download)

#### Powershell
[&uarr; Prerequisite Applications](#prerequisite-applications)<br />

Powershell is optional, and is used in the project for generating a template for the JSON input file required by [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html):

- [Installing Windows PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/windows-powershell/install/installing-windows-powershell)

### Python Installation - pip
[&uarr; Installation](#installation)<br />

With [python](https://www.python.org/downloads/windows/) installed, run in a powershell or command window:

```py
$ py -m pip install trapit
```
## Unit Testing
[&uarr; In This README...](#in-this-readme)<br />
[&darr; Unit Testing Process](#unit-testing-process-3)<br />
[&darr; Unit Test Results](#unit-test-results-3)<br />

In this section the unit testing API function trapit.test_unit is itself tested using [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html). A 'pure' wrapper function is constructed that takes input parameters and returns a value, and is tested within a loop over scenario records read from a JSON file.

### Unit Testing Process
[&uarr; Unit Testing](#unit-testing)<br />
[&darr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-3)<br />
[&darr; Step 2: Create Results Object](#step-2-create-results-object-3)<br />
[&darr; Step 3: Format Results](#step-3-format-results-3)<br />

This section details the three steps involved in following [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html).

#### Step 1: Create Input Scenarios File
[&uarr; Unit Testing Process](#unit-testing-process-3)<br />
[&darr; Unit Test Wrapper Function](#unit-test-wrapper-function-3)<br />
[&darr; Scenario Category ANalysis (SCAN)](#scenario-category-analysis-scan-3)<br />
[&darr; Creating the Input Scenarios File](#creating-the-input-scenarios-file-3)<br />

##### Unit Test Wrapper Function
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-3)<br />

The signature of the unit under test is:

```powershell
test_unit(inp_file, out_file, purely_wrap_unit)
```
where the parameters are described in the API section above. The diagram below shows the structure of the input and output of the wrapper function.

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/JSD-test_unit.png">

As noted above, the inputs to the unit under test here include a function. This raises the interesting question as to how we can model a function in our test data. In fact the best way to do this seems to be to regard the function as a kind of black box, where we don't care about the interior of the function, but only its behaviour in terms of returning an output from an input. This is why we have the Actual Values group in the input side of the diagram above, as well as on the output side. We can model any deterministic function in our test data simply by specifying input and output sets of values.

As we are using the trapit.test_unit API to test itself, we will have inner and outer levels for the calls and their parameters. The inner-level wrapper function passed in in the call to the unit under test by the outer-level wrapper function therefore needs simply to return the set of Actual Values records for the given scenario. In order for it to know which set to return, the scenarios need to be within readable scope, and we need to know which scenario to use. This is achieved by maintaining arrays containing a list of inner scenarios and a list of inner output groups, along with a nonlocal variable with an index to the current inner scenario that the inner wrapper increments each time it's called. This allows the output array to be extracted from the input parameter from the outer wrapper function.

From the input and output groups depicted we can construct CSV files with flattened group/field structures, and default values added, as follows:

###### trapit_py_inp.csv
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/trapit_py_inp.png">

The value fields shown correspond to a prototype scenario with records per input group:
- Unit Test: 1
- Input Fields: 4
- Output Fields: 4
- Scenarios: 2
- Input Values: 4
- Expected Values: 4
- Actual Values: 4

###### trapit_py_out.csv
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/trapit_py_out.png">

The value fields shown correspond to a prototype scenario with records per output group:
- Unit Test: 1
- Input Fields: 4
- Output Fields: 6
- Scenarios: 2
- Input Values: 4
- Expected Values: 4
- Actual Values: 4

A PowerShell utility uses these CSV files, together with one for scenarios, discussed next, to generate a template for the JSON unit testing input file. The utility creates a prototype scenario dataset with a record in each group for each populated value column, that is used for each scenario in the template.

##### Scenario Category ANalysis (SCAN)
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-3)<br />
[&darr; Generic Category Sets](#generic-category-sets)<br />
[&darr; Categories and Scenarios](#categories-and-scenarios)<br />

The art of unit testing lies in choosing a set of scenarios that will produce a high degree of confidence in the functioning of the unit under test across the often very large range of possible inputs.

A useful approach can be to think in terms of categories of inputs, where we reduce large ranges to representative categories, an idea I explore in this article:

- [Unit Testing, Scenarios and Categories: The SCAN Method](https://brenpatf.github.io/2021/10/17/unit-testing-scenarios-and-categories-the-scan-method.html)

###### Generic Category Sets
[&uarr; Scenario Category ANalysis (SCAN)](#scenario-category-analysis-scan-3)<br />

As explained in the article mentioned above, it can be very useful to think in terms of generic category sets that apply in many situations. Multiplicity is relevant here (as it often is):

###### *Multiplicity*

There are several entities where the generic category set of multiplicity applies, and we should check each of the applicable None / One / Multiple instance categories.

| Code     | Description     |
|:--------:|:----------------|
| None     | No values       |
| One      | One value       |
| Multiple | Multiple values |

Apply to:
<ul>
<li>Input Groups</li>
<li>Output Groups</li>
<li>Input Fields (one or multiple only)</li>
<li>Output Fields (one or multiple only)</li>
<li>Input Records</li>
<li>Output Records</li>
<li>Delimiter Characters (one or multiple characters only)</li>
<li>Scenarios (one or multiple only)</li>
</ul>

###### Categories and Scenarios
[&uarr; Scenario Category ANalysis (SCAN)](#scenario-category-analysis-scan-3)<br />

After analysis of the possible scenarios in terms of categories and category sets, we can depict them on a Category Structure diagram:

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/CSD-test_unit.png">

We can tabulate the results of the category analysis, and assign a scenario against each category set/category with a unique description:

|  # | Category Set               | Category        | Scenario                                                 |
|---:|:---------------------------|:----------------|:-----------------------------------------------------    |
|  1 | Input Group Multiplicity   | None            | No input groups                                          |
|  2 | Input Group Multiplicity   | One             | One input group                                          |
|  3 | Input Group Multiplicity   | Multiple        | Multiple input groups                                    |
|  4 | Output Group Multiplicity  | None            | No output groups                                         |
|  5 | Output Group Multiplicity  | One             | One output group                                         |
|  6 | Output Group Multiplicity  | Multiple        | Multiple output groups                                   |
|  7 | Input Field Multiplicity   | One             | One input group field                                    |
|  8 | Input Field Multiplicity   | Multiple        | Multiple input fields                                    |
|  9 | Output Field Multiplicity  | One             | One output group field                                   |
| 10 | Output Field Multiplicity  | Multiple        | Multiple output fields                                   |
| 11 | Input Record Multiplicity  | None            | No input group records                                   |
| 12 | Input Record Multiplicity  | One             | One input group record                                   |
| 13 | Input Record Multiplicity  | Multiple        | Multiple input group records                             |
| 14 | Output Record Multiplicity | None            | No output group records                                  |
| 15 | Output Record Multiplicity | One             | One output group record                                  |
| 16 | Output Record Multiplicity | Multiple        | Multiple output group records                            |
| 17 | Scenario Multiplicity      | One             | One scenario                                             |
| 18 | Scenario Multiplicity      | Multiple        | Multiple scenarios                                       |
| 19 | Scenario Multiplicity      | Active/Inactive | Active and inactive scenarios                            |
| 21 | Category Set               | Null            | Category sets null                                       |
| 21 | Category Set               | Same            | Multiple category sets with the same value               |
| 22 | Category Set               | Different       | Multiple category sets with null and not null values     |
| 23 | Delimiter Characters       | Delimiter 1     | Delimiter example 1                                      |
| 24 | Delimiter Characters       | Delimiter 2     | Delimiter example 2                                      |
| 25 | Delimiter Characters       | Multiple        | Multicharacter delimiter                                 |
| 26 | Invalidity Type            | Valid           | All records the same                                     |
| 27 | Invalidity Type            | Values mismatch | Same record numbers, value difference                    |
| 28 | Invalidity Type            | #Exp > #Act     | More expected than actual records                        |
| 29 | Invalidity Type            | #Exp < #Act     | More actual than expected records set                    |
| 30 | Unhandled Exception        | Yes             | Unhandled exception                                      |
|  * | Unhandled Exception        | No              | (No unhandled exception)*                                |
|  * | Test Status                | Pass            | (All scenarios pass)*                                    |
| 31 | Test Status                | Fail            | At least one scenario fails                              |

From the scenarios identified we can construct the following CSV file, taking the category set and scenario columns, and adding an initial value for the active flag:

###### trapit_py_sce.csv
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/trapit_py_sce.png">

##### Creating the Input Scenarios File
[&uarr; Step 1: Create Input Scenarios File](#step-1-create-input-scenarios-file-3)<br />

The API to generate a template JSON file can be run with the following PowerShell in the folder of the CSV files:

###### Format-JSON-TrapitPy

```powershell
Import-Module ..\powershell_utils\TrapitUtils\TrapitUtils.psm1
Write-UT_Template 'trapit_py' '|' 'Trapit Python Tester'
```

This creates the template JSON file, trapit_py_temp.json, which contains an element for each of the scenarios, with the appropriate category set and active flag, and a prototype set of input and output records.

In the prototype record sets, each group has zero or more records with field values taken from the group CSV files, with a record for each value column present where at least one value is not null for the group. The template scenario records may be manually updated (and added or subtracted) to reflect input and expected output values for the actual scenario being tested.

#### Step 2: Create Results Object
[&uarr; Unit Testing Process](#unit-testing-process-3)<br />

Step 2 requires the writing of a wrapper function that is passed into a unit test library function, test_unit, via the entry point API,  `test_format`. test_unit reads the input JSON file, calls the wrapper function for each scenario, and writes the output JSON file with the actual results merged in along with the expected results.

The wrapper function has the structure shown in the diagram below, being defined in a driver script followed by a single line calling the test_format API.

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/testtrapit_CSD.png">

##### purely_wrap_unit (skeleton)

```python
def purely_wrap_unit(inp_groups): # input groups object
    def groups_from_group_field_pairs(group_field_lis): # group/field pairs list
        return list(dict.fromkeys([gf.split(DELIM)[0] for gf in group_field_lis]))
    def groups_obj_from_gf_pairs(group_lis,        # groups list
                                 group_field_lis): # group/field pairs list
        obj = {}
        for g in group_lis:
            gf_pairs = filter(lambda gf: gf[:len(g)] == g, group_field_lis)
            obj[g] = [gf[len(g) + 1:] for gf in gf_pairs]
        return obj
    def groups_obj_from_sgf_triples(sce,             # scenario
                                    group_lis,       # groups list
                                    sgf_triple_lis): # scenario/group/field triples list
        this_sce_pairs = list(filter(lambda g: g[:len(sce)] == sce, sgf_triple_lis))
        group_field_lis = [p[len(sce) + 1:] for p in this_sce_pairs]
        return groups_obj_from_gf_pairs(group_lis, group_field_lis)
    def purely_wrap_unit_inner(inp_groups_inner): # input groups object (inner level)
        nonlocal sce_inp_ind
        scenario_inner, exception_yn = sce_inp_lis[sce_inp_ind].split(DELIM)
        sce_inp_ind += 1
        if(exception_yn == 'Y'):
            raise Exception('Exception thrown')
        return groups_obj_from_sgf_triples(scenario_inner, out_group_lis, inp_groups[ACT_VALUES])
    def write_input_json():
        ...
    def get_actuals():
        ...

    out_group_lis, sce_inp_lis = write_input_json()
    sce_inp_ind = 0
    trapit.test_unit(INP_JSON_INNER, OUT_JSON_INNER, purely_wrap_unit_inner)
    return get_actuals()
```

#### Step 3: Format Results
[&uarr; Unit Testing Process](#unit-testing-process-3)<br />

Step 3 involves formatting the results contained in the JSON output file from step 2, via the JavaScript formatter:
- `test_format` is the function from the trapit Python package that calls the main test driver function, then passes the output JSON file name to the JavaScript formatter and outputs a summary of the results.

##### testtrapit.py (skeleton)
```powershell
import sys, os, json, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import trapit

DELIM = '|'
ROOT = os.path.dirname(__file__)
NPM_ROOT,                                  INP_JSON_INNER,                OUT_JSON_INNER                = \
ROOT + '/../powershell_utils/TrapitUtils', ROOT + 'trapit_py_inner.json', ROOT + 'trapit_py_out_inner.json'
def purely_wrap_unit(inp_groups): # input groups object
    ...

trapit.test_format(ROOT, NPM_ROOT, 'trapit_py', purely_wrap_unit)
```
This script contains the wrapper function, passing it in a call to the trapit library function test_format.

### Unit Test Results
[&uarr; Unit Testing](#unit-testing)<br />
[&darr; Unit Test Report - Trapit Python Tester](#unit-test-report---trapit-python-tester)<br />
[&darr; Results for Scenario 18: Multiple scenarios [Category Set: Scenario Multiplicity]](#results-for-scenario-18-multiple-scenarios-category-set-scenario-multiplicity)<br />

The unit test script creates a results subfolder, with results in text and HTML formats, in the script folder, and outputs the following summary:
```
Results summary for file: [MY_PATH]\trapit_python_tester\unit_test/trapit_py_out.json
=====================================================================================
File:          trapit_py_out.json
Title:         Trapit Python Tester
Inp Groups:    7
Out Groups:    8
Tests:         31
Fails:         1
Folder:        trapit-python-tester
```

#### Unit Test Report - Trapit Python Tester
[&uarr; Unit Test Results](#unit-test-results-3)<br />

Here we show the scenario-level summary of results, and show the detail for one of the scenarios, in HTML format.

You can review the HTML formatted unit test results here:

- [Unit Test Report: Trapit Python Tester](http://htmlpreview.github.io/?https://github.com/BrenPatF/trapit_python_tester/blob/master/unit_test/trapit-python-tester/trapit-python-tester.html)

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/summary-trapitpy.png">

#### Results for Scenario 18: Multiple scenarios [Category Set: Scenario Multiplicity]
[&uarr; Unit Test Results](#unit-test-results-3)<br />
[&darr; Input Groups](#input-groups)<br />
[&darr; Output Groups](#output-groups)<br />

##### Input Groups
[&uarr; Results for Scenario 18: Multiple scenarios [Category Set: Scenario Multiplicity]](#results-for-scenario-18-multiple-scenarios-category-set-scenario-multiplicity)<br />
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/scenario_18_inp-trapitpy.png">

##### Output Groups
[&uarr; Results for Scenario 18: Multiple scenarios [Category Set: Scenario Multiplicity]](#results-for-scenario-18-multiple-scenarios-category-set-scenario-multiplicity)<br />
<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/scenario_18_out-trapitpy.png">
## Folder Structure
[&uarr; In This README...](#in-this-readme)<br />

The project folder structure is shown below.

<img src="https://github.com/BrenPatF/trapit_python_tester/raw/master/png/folders-trapit_python_tester.png">

There are four subfolders below the trapit root folder, which has README and module:
- `examples`: Two working Python examples are included in their own subfolders, with both test scripts and a main script that shows how the unit under test would normally be called
- `png`: This holds the image files for the README
- `powershell_utils`: PowerShell packages, with JavaScript Trapit module included in TrapitUtils
- `unit_test`: Root folder for unit testing, with subfolder having the results files

## See Also
[&uarr; In This README...](#in-this-readme)<br />
- [The Math Function Unit Testing Design Pattern](https://brenpatf.github.io/2023/06/05/the-math-function-unit-testing-design-pattern.html)
- [Unit Testing, Scenarios and Categories: The SCAN Method](https://brenpatf.github.io/2021/10/17/unit-testing-scenarios-and-categories-the-scan-method.html)
- [Node.js Downloads](https://nodejs.org/en/download)
- [Trapit - JavaScript Unit Testing/Formatting Utilities Module](https://github.com/BrenPatF/trapit_nodejs_tester)
- [Trapit - PowerShell Unit Testing Utilities Module](https://github.com/BrenPatF/powershell_utils/tree/master/TrapitUtils)
- [Trapit - Python Unit Testing Module - Python Package Index](https://pypi.org/project/trapit/)
- [Trapit - Python Unit Testing Module - GitHub](https://github.com/BrenPatF/trapit_python_tester)

## Software Versions

- Windows 11
- Powershell 7
- npm 6.13.4
- Node.js v12.16.1
- Python 3.13.2

## License
MIT
