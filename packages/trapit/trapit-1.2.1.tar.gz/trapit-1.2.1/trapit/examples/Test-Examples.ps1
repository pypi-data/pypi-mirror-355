$extFolders = (Get-ChildItem -Path $PSScriptRoot -Directory).name
Foreach($f in $extFolders) {
    ''
    ('Running: ' + $f + '\test-' + $f + '...')
    py ($PSScriptRoot + '\' + $f + '\test' + $f + '.py') > ('test-' + $f + '.log')
    cat ('test-' + $f + '.log')
}