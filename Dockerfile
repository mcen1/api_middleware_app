FROM alpine:3.21.3
LABEL org.opencontainers.image.base.name="docker.io/library/alpine:latest"
LABEL org.opencontainers.image.authors="CHANGEME@CHANGEME.com"
LABEL org.opencontainers.image.description="API layer for running automations"

RUN mkdir -p /usr/CHANGEME

WORKDIR /usr/CHANGEME

COPY ./src/ /usr/CHANGEME/
COPY ./requirements.txt /usr/CHANGEME/requirements.txt
COPY automation_endpoint_config.yml /usr/CHANGEME/automation_endpoint_config.yml
COPY ./templates/ /usr/CHANGEME/templates/
COPY ./ssl/ca-cert.pem /usr/local/share/ca-certificates/my-cert.crt
COPY openssl.cnf /etc/openssl.cnf
COPY apkpackages1.txt /root/apkpackages1.txt
COPY apkpackages2.txt /root/apkpackages2.txt
ENV OPENSSL_CONF=/etc/openssl.cnf


RUN cat /usr/local/share/ca-certificates/my-cert.crt >> /etc/ssl/certs/ca-certificates.crt && \
    apk --no-cache add $(cat /root/apkpackages1.txt) && \
    apk --no-cache add --virtual $(cat /root/apkpackages2.txt) && \
    curl -k https://CHANGEMEhub.CHANGEME/contentserved/public/paloaltofiledeleter.sh > /badfiledeleter.sh && \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt && \
    apk add git && \
    apk del build-dependencies && \
    addgroup -S notroot && \
    adduser -u 15000 -S notroot -G notroot && \
    chown -R notroot:notroot /usr/CHANGEME/ && \
    rm -rf /usr/share/git-core/templates/hooks/pre-receive.sample && \
    ls -la && \
    sh /badfiledeleter.sh && \
    chmod ugo+x /usr/CHANGEME/containerstartup.sh && \
    ls -la /usr/CHANGEME/routers/v1/automation/


WORKDIR /usr/CHANGEME/

EXPOSE 8000

USER notroot

HEALTHCHECK --interval=5m --timeout=30s \
  CMD /bin/sh /usr/CHANGEME/health.sh

CMD ["/bin/sh", "-c", "/usr/CHANGEME/containerstartup.sh"]
