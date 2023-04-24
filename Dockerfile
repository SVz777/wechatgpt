FROM python:3.10-alpine

LABEL maintainer="foo@bar.com"
ARG TZ='Asia/Shanghai'

RUN apk add --no-cache \
        bash \
        curl \
        wget \
    && /usr/local/bin/python -m pip install --no-cache --upgrade pip \
    && pip install --no-cache -r requirements.txt \
    && pip install --no-cache -r requirements-optional.txt \
    && apk del curl wget

ENV BUILD_PREFIX=/app
COPY . ${BUILD_PREFIX}\
WORKDIR ${BUILD_PREFIX}

ADD ./docker/entrypoint.sh /entrypoint.sh

RUN cp config-template.json ${BUILD_PREFIX}/config.json \
    && chmod +x /entrypoint.sh \
    && adduser -D -h /home/noroot -u 1000 -s /bin/bash noroot \
    && chown -R noroot:noroot ${BUILD_PREFIX}


USER noroot

ENTRYPOINT ["/entrypoint.sh"]
