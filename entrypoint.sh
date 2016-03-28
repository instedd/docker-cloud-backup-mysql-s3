#!/bin/sh

# Check required environment variables
: ${S3_BUCKET:?}
: ${AWS_ACCESS_KEY_ID:?}
: ${AWS_SECRET_ACCESS_KEY:?}
: ${DOCKERCLOUD_AUTH?"Give 'Full Access' API role to this service"}

exec /usr/sbin/crond -f
