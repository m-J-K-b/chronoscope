@echo off
:: Batch script to build a Docker image using variables from an .env file

:: Check if the .env file exists
if not exist .env (
    echo .env file not found
    exit /b 1
)

:: Load variables from the .env file
for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr /r /v "^#\|^$"') do (
    set %%a=%%b
)

:: Check if IMAGE_NAME is set
if "%IMAGE_NAME%" == "" (
    echo IMAGE_NAME is not set in the .env file
    exit /b 1
)

:: Build the Docker image
docker build -t %IMAGE_NAME% .

