# Add Python to the PATH environment variable
$pythonPath = "C:\Users\user\AppData\Local\Programs\Python\Python313"
$pythonScripts = "C:\Users\user\AppData\Local\Programs\Python\Python313\Scripts"

# Check if paths exist before adding
if (Test-Path $pythonPath) {
    $env:Path = "$pythonPath;$pythonScripts;" + $env:Path
    
    # Set Python environment variables
    $env:PYTHON_HOME = $pythonPath
    $env:PYTHONPATH = "$pythonPath\Lib;$pythonPath\DLLs"
    
    # Add Python alias
    Set-Alias -Name python -Value "$pythonPath\python.exe"
    
    Write-Host "Python environment variables and alias set successfully!"
} else {
    Write-Host "Python path not found at: $pythonPath"
} 