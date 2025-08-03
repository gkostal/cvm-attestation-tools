@rem docker login
@rem az login --scope https://management.core.windows.net//.default
@rem  az login --use-device-code --scope https://management.core.windows.net//.default

call az acr login --name gnkdev

docker tag python-web-api-slim  gnkdev.azurecr.io/python-web-api-slim:latest
docker push gnkdev.azurecr.io/python-web-api-slim:latest
