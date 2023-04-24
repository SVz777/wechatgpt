FROM python:3.10-alpine

LABEL maintainer="svz@svz.life"
ARG TZ='Asia/Shanghai'

RUN apk add --no-cache \
        bash \
        curl \
        wget \
    && /usr/local/bin/python -m pip install --no-cache --upgrade pip \
    && apk add --no-cache tzdata \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    echo "Asia/Shanghai" > /etc/timezone \
    apk del tzdata

ENV BUILD_PREFIX=/app
COPY . ${BUILD_PREFIX}
WORKDIR ${BUILD_PREFIX}

RUN pip install --no-cache -r requirements.txt \
    && pip install --no-cache -r requirements-optional.txt \
    && apk del curl wget \
    && cp config-template.json ${BUILD_PREFIX}/config.json \
    && cp ./docker/entrypoint.sh /entrypoint.sh \
    && chmod +x /entrypoint.sh \
    && chown -R nobody:nobody ${BUILD_PREFIX}

USER nobody

ENTRYPOINT ["/entrypoint.sh"]
