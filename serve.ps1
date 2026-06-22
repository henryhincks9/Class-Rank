# Run this from the project root folder.
# Requires Python 3 and Flask installed.

# Ensure a strong Flask secret key is available in this PowerShell session.
if (-not $env:FLASK_SECRET_KEY -or $env:FLASK_SECRET_KEY -eq "dev-secret-key") {
	$generated = [System.Convert]::ToBase64String((New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes(32))
	# Use a URL-safe version
	$generated = $generated.Replace('+','-').Replace('/','_').TrimEnd('=')
	$env:FLASK_SECRET_KEY = $generated
	Write-Output "FLASK_SECRET_KEY not set (or using default). Generated temporary secret for this session."
}

python server.py
