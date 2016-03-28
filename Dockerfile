FROM alpine:3.3

RUN \
  apk add --update mysql-client python py-pip && \
  pip install awscli python-dockercloud && \
  apk del py-pip && \
  rm -rf /var/cache/apk/*

ENV S3_BUCKET ""
ENV AWS_ACCESS_KEY_ID ""
ENV AWS_SECRET_ACCESS_KEY ""

ADD entrypoint.sh /
ADD backup.py /

CMD ["/entrypoint.sh"]
