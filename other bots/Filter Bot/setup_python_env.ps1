# Read the .env file and set environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        
        # Handle PATH specially to append rather than replace
        if ($name -eq "PATH") {
            $existing_path = [Environment]::GetEnvironmentVariable("PATH", "User")
            $new_paths = $value -replace '%PATH%', $existing_path
            [Environment]::SetEnvironmentVariable("PATH", $new_paths, "User")
        } else {
            [Environment]::SetEnvironmentVariable($name, $value, "User")
        }
        
        Write-Host "Set $name environment variable"
    }
}

Write-Host "`nPython environment variables have been set successfully!"
Write-Host "Please restart your terminal for changes to take effect." 