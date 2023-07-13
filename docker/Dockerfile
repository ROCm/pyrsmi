# MIT License
# 
# Copyright (c) 2023 Advanced Micro Devices, Inc.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

