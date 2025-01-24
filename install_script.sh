#!/bin/bash

# Install K3s (lightweight Kubernetes)
curl -sfL https://get.k3s.io | sh -
echo "K3s installed. Verifying installation..."

# Ensure K3s service is running
systemctl status k3s || (echo "K3s is not running, exiting..." && exit 1)

# Fix permissions for the K3s config file so that the current user can read it
# The K3s config file is at /etc/rancher/k3s/k3s.yaml, we will copy it to the user directory
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $USER:$USER $HOME/.kube/config
chmod 644 $HOME/.kube/config
export KUBECONFIG=$HOME/.kube/config
# Verify if kubectl can access the K3s cluster
echo "Verifying kubectl access..."
kubectl get nodes || (echo "K3s cluster not reachable, waiting for 30 seconds..." && sleep 30 && kubectl get nodes)

# Install Helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# Add the Prometheus repo and update it
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus using Helm
helm install prometheus prometheus-community/prometheus

# Wait for Prometheus to be available
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-server

# Get Prometheus IP address
export PROMETHEUS_IP=$(kubectl get svc prometheus-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "PROMETHEUS_IP=${PROMETHEUS_IP}" >> $GITHUB_ENV
echo "Prometheus Server IP: $PROMETHEUS_IP"
