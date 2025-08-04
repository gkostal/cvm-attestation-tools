@rem az aks get-credentials --resource-group gnkaksneu-rg --name gnkaksneu

kubectl delete deployment pygentvm-deployment
kubectl delete deployment pygencvm-deployment

kubectl apply -f pygentvm.yaml
kubectl apply -f pygencvm.yaml
