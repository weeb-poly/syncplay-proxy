#!/bin/sh

# kubectl create secret tls syncplay-tls-secret \
#   "--cert=${SYNCPLAY_TLS_PATH}/fullchain.pem" \
#   "--key=${SYNCPLAY_TLS_PATH}/privkey.pem" \
#   --dry-run -o yaml | kubectl apply -f -
# kubectl label secret syncplay-tls-secret app=syncplay

kubectl rollout restart deployment/syncplay-proxy
