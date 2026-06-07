#!/bin/sh
set -e

: "${API_ID:?API_ID is not set}"
: "${API_HASH:?API_HASH is not set}"

./telegram-bot-api --local --api-id="$API_ID" --api-hash="$API_HASH" --http-port=8731 --verbosity=3