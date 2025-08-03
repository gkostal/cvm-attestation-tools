@echo off

rem Create a long running development container using Docker

rem Check if container already exists
docker container inspect web-api-dev >nul 2>&1

IF %ERRORLEVEL% EQU 0 (
    echo Container 'web-api-dev' already exists.
    echo Starting the container...
    docker start -ai web-api-dev
) ELSE (
    echo Creating and starting 'web-api-dev' container...
    docker run -dit ^
        --name web-api-dev ^
        --restart unless-stopped ^
        -p 5000:5000 ^
        web-api-dev-with-tools
)
