#!/bin/bash

# This script deploys the application to Azure Container Apps

# Variables - change these as needed
RESOURCE_GROUP="hackrx-rg"
LOCATION="eastus"
ACR_NAME="hackrxregistry"
APP_NAME="hackrx-rag"
IMAGE_NAME="hackrx-rag:latest"

# Create resource group if it doesn't exist
echo "Creating resource group $RESOURCE_GROUP..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry (ACR) if it doesn't exist
echo "Creating Azure Container Registry $ACR_NAME..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# Build and push the Docker image to ACR
echo "Building and pushing the Docker image to ACR..."
az acr build --registry $ACR_NAME --image $IMAGE_NAME .

# Create Azure Container App Environment if it doesn't exist
echo "Creating Container App Environment..."
az containerapp env create \
  --name hackrx-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create a Managed Identity for the Container App
echo "Creating Managed Identity..."
IDENTITY_NAME="hackrx-identity"
az identity create --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP
IDENTITY_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)

# Deploy the container app
echo "Deploying Container App $APP_NAME..."
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment hackrx-env \
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME" \
  --registry-server "$ACR_NAME.azurecr.io" \
  --target-port 8000 \
  --ingress external \
  --user-assigned $IDENTITY_ID \
  --min-replicas 1 \
  --max-replicas 5 \
  --cpu 1 \
  --memory 2Gi \
  --env-vars "ENABLE_AUTH=true" "LOG_LEVEL=INFO"

echo "Deployment completed!"
echo "Your app is available at: $(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)"
