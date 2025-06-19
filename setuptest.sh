apk --no-cache add coreutils py3-pip curl busybox-extras jq && \
apk --no-cache add --virtual build-dependencies build-base python3-dev && \
pip3 install --upgrade  --break-system-packages pip && \
pip3 install  --break-system-packages -r requirements.txt && \
mkdir -p /usr/CHANGEME/ && \
cp src/apikeys.yml /usr/CHANGEME/ && \
apk add git && \
apk del build-dependencies

