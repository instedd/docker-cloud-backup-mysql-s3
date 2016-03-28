#!/bin/sh

# Check required environment variables
: ${S3_BUCKET:?}
: ${AWS_ACCESS_KEY_ID:?}
: ${AWS_SECRET_ACCESS_KEY:?}

exec /usr/sbin/crond -f
