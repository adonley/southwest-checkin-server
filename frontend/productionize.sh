#!/usr/bin/env bash

npm run build --prod
docker build -f ./Dockerfile.prod -t adonley/southwest-checkin-frontend .
docker push adonley/southwest-checkin-frontend:latest
