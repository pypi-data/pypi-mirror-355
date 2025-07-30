$examplesDir = $PSScriptRoot
$examples = @('colgroup', 'helloworld')

sl $examplesDir
Foreach($e in $examples) {
    $prog = $e + '\main' + $e + '.py'
    "Executing:  py $prog at " + (Date -format "dd-MMM-yy HH:mm:ss")
    py $prog
}
