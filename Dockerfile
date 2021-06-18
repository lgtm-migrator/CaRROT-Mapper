FROM python:3.8-slim
LABEL authors="Roberto Santos"

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN apt-get update && \
    apt-get install -y \
        vim \
        htop \
        wait-for-it \
        binutils \
        gettext \
        libpq-dev \
        gcc

RUN addgroup -q django && \
    adduser --quiet --ingroup django --disabled-password django

COPY ./requirements.txt /requirements.txt

COPY ./entrypoint.sh /entrypoint.sh

RUN chmod u+x /entrypoint.sh

RUN chown -R django:django /entrypoint.sh

COPY ./api /api

WORKDIR /api

USER django

ENV PATH=/home/django/.local/bin:$PATH

RUN pip install -r /requirements.txt --no-cache-dir

USER root
RUN apt-get install graphviz -y

COPY --chown=django:django co-connect-tools/ /coconnect/

USER django

RUN pip install -e /coconnect/

ENTRYPOINT ["/entrypoint.sh"]