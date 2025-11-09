#!/bin/bash

# Test script for Koozie Agent endpoints
# Make sure the server is running before executing this script

BASE_URL="${BASE_URL:-http://localhost:8080}"

echo "Testing Koozie Agent endpoints..."
echo "Base URL: $BASE_URL"
echo ""

# Test health endpoint
echo "1. Testing /health endpoint..."
curl -s "$BASE_URL/health" | jq .
echo ""
echo ""

# Test sync chat endpoint
echo "2. Testing /chat/sync endpoint..."
curl -s -X POST "$BASE_URL/chat/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is a Koozie?"
  }' | jq .
echo ""
echo ""

# Test streaming chat endpoint
echo "3. Testing /chat endpoint (streaming)..."
curl -sN -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about your pens."
  }'
echo ""
echo ""

echo "Tests completed!"

