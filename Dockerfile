FROM python:3.10-alpine

LABEL maintainer="foo@bar.com"
ARG TZ='Asia/Shanghai'

ARG CHATGPT_ON_WECHAT_VER

ADD ./docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && adduser -D -h /home/noroot -u 1000 -s /bin/bash noroot \
    && chown -R noroot:noroot ${BUILD_PREFIX} \

ENV BUILD_PREFIX=/app

RUN apk add --no-cache \
        bash \
        curl \
        wget \
    && export BUILD_GITHUB_TAG=master \
    && wget -t 3 -T 30 -nv -O wechatgpt-${BUILD_GITHUB_TAG}.tar.gz \
            https://github.com/SVz777/wechatgpt/archive/refs/heads/${BUILD_GITHUB_TAG}.tar.gz \
    && tar -xzf wechatgpt-${BUILD_GITHUB_TAG}.tar.gz \
    && mv wechatgpt-${BUILD_GITHUB_TAG} ${BUILD_PREFIX} \
    && rm wechatgpt-${BUILD_GITHUB_TAG}.tar.gz \
    && cd ${BUILD_PREFIX} \
    && cp config-template.json ${BUILD_PREFIX}/config.json \
    && /usr/local/bin/python -m pip install --no-cache --upgrade pip \
    && pip install --no-cache -r requirements.txt \
    && pip install --no-cache -r requirements-optional.txt \
    && apk del curl wget

WORKDIR ${BUILD_PREFIX}

USER noroot

ENTRYPOINT ["/entrypoint.sh"]