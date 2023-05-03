##############################################################
# Dockerfile for building pyamdsmi, a Python binding of
# AMD-SMI, System Management Interface for AMD GPUs
#
# BUILD: docker build --network=host --file docker/Dockerfile --tag pyamdsmi .
# RUN: docker run ... -p 8888:8888 pyamdsmi
##############################################################
FROM python:3.8

ENV DEBIAN_FRONTEND noninteractive

ADD ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    rm -rf ~/.cache/pip

ADD ./pyrsmi /app/pyrsmi
ADD ./setup.py /app/
ADD ./setup.cfg /app/
ADD ./README.md /app/
ADD ./PKG-INFO /app/
ADD ./MANIFEST.in /app/
# ADD ./help_query_gpu.txt /app/
ADD docker/entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

ENV HOME=/app
ENV APP_HOME=/app

WORKDIR /app

EXPOSE 8888
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/bash"]

