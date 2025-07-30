#
# ****************************************************
# Licensed Materials - Property of HCL.
# (c) Copyright HCL America, Inc. 2025.
# Note to U.S. Government Users *Restricted Rights.
# ****************************************************
#


# This script runs Python build commands and uploads the package using Twine.

param ($PyPI_APIToken)

# Ensure the script stops on errors
$ErrorActionPreference = "Stop"

# Set the script root path
Write-Host "Setting the script root path to $PSScriptRoot..." 
Set-Location -Path $PSScriptRoot

# Delete the dist folder if it exists
$distPath = Join-Path -Path $PSScriptRoot -ChildPath "dist"
if (Test-Path -Path $distPath) {
    Write-Host "Removing existing dist folder..."
    Remove-Item -Path $distPath -Recurse -Force
} else {
    Write-Host "No existing dist folder found."
}

# Run Python build commands
Write-Host "Running Python build command..."
python -m build

# Check if the build was successful
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python build failed. Exiting script."
    exit $LASTEXITCODE
}

# Upload the package using Twine
# Write-Host "Uploading the package using Twine..."
# twine upload dist/*

# # Check if the upload was successful
# if ($LASTEXITCODE -ne 0) {
#     Write-Error "Twine upload failed. Exiting script."
#     exit $LASTEXITCODE
# }

Write-Host "Build and upload completed successfully."