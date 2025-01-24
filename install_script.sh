#! /bin/bash

curl -sfL https://get.k3s.io | sh -
echo "K3s installed. Verifying installation..."
kubectl get nodes

curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-server

# get prometeus ip address
export PROMETHEUS_IP=$(kubectl get svc prometheus-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "PROMETHEUS_IP=${PROMETHEUS_IP}" >> $GITHUB_ENV
echo "Prometheus Server IP: $PROMETHEUS_IP"


