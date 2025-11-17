#!/bin/bash
#
# Check IPFS connectivity and configuration
#

set -e

echo "Checking IPFS configuration..."

# Check if IPFS is running
if ! curl -s http://localhost:5001/api/v0/id > /dev/null; then
    echo "❌ IPFS daemon is not running"
    echo "   Start with: ipfs daemon"
    exit 1
fi

echo "✅ IPFS daemon is running"

# Check IPFS ID
IPFS_ID=$(curl -s http://localhost:5001/api/v0/id | grep -o '"ID":"[^"]*' | cut -d'"' -f4)
echo "   Node ID: ${IPFS_ID}"

# Check IPFS version
IPFS_VERSION=$(ipfs version --number)
echo "   Version: ${IPFS_VERSION}"

# Check pubsub
echo ""
echo "Checking IPFS Pubsub..."
PUBSUB_TOPICS=$(curl -s http://localhost:5001/api/v0/pubsub/ls | jq -r '.[]' 2>/dev/null || echo "[]")
if [ "$PUBSUB_TOPICS" != "[]" ]; then
    echo "✅ Subscribed topics:"
    echo "$PUBSUB_TOPICS" | jq -r '.[]' || echo "$PUBSUB_TOPICS"
else
    echo "ℹ️  No active subscriptions"
fi

# Check IPNS keys
echo ""
echo "Checking IPNS keys..."
IPNS_KEYS=$(curl -s http://localhost:5001/api/v0/key/list | jq -r '.Keys[].Name' 2>/dev/null || echo "")
if [ -n "$IPNS_KEYS" ]; then
    echo "✅ IPNS keys:"
    echo "$IPNS_KEYS"
else
    echo "ℹ️  No IPNS keys found (will be created on first use)"
fi

echo ""
echo "IPFS check complete!"

