FROM kestra/kestra:v1.3.0

USER root

COPY requirements.lock /tmp/requirements.lock
RUN pip3 install --no-cache-dir -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock
