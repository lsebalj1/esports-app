#!/bin/sh
set -e

ENDPOINT="http://dynamodb-local:8000"

echo "Waiting for DynamoDB Local..."
until aws dynamodb list-tables --endpoint-url $ENDPOINT > /dev/null 2>&1; do
  sleep 2
done
echo "DynamoDB ready. Creating tables..."

# Users 
aws dynamodb create-table \
  --endpoint-url $ENDPOINT \
  --table-name Users \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=email,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes '[{
    "IndexName": "email-index",
    "KeySchema": [{"AttributeName":"email","KeyType":"HASH"}],
    "Projection": {"ProjectionType":"ALL"}
  }]' 2>/dev/null || echo "Users already exists"v

# Tournaments
aws dynamodb create-table \
  --endpoint-url $ENDPOINT \
  --table-name Tournaments \
  --attribute-definitions \
    AttributeName=tournament_id,AttributeType=S \
    AttributeName=status,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema AttributeName=tournament_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes '[{
    "IndexName": "status-index",
    "KeySchema": [
      {"AttributeName":"status","KeyType":"HASH"},
      {"AttributeName":"created_at","KeyType":"RANGE"}
    ],
    "Projection": {"ProjectionType":"ALL"}
  }]' 2>/dev/null || echo "Tournaments already exists"