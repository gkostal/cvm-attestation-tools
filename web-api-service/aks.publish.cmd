@rem az aks get-credentials --resource-group gnkaksneu-rg --name gnkaksneu

@rem kubectl delete deployment gentvm-deployment
kubectl delete deployment pygencvm-deployment

@rem kubectl apply -f gentvm.yaml
kubectl apply -f pygencvm.yaml
