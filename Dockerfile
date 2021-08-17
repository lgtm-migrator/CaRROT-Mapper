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
        gcc \
        graphviz

RUN addgroup -q django && \
    adduser --quiet --ingroup django --disabled-password django

COPY ./entrypoint.sh /entrypoint.sh

RUN chmod u+x /entrypoint.sh

RUN chown -R django:django /entrypoint.sh

RUN mkdir /api

WORKDIR /api

RUN chown -R django:django /api

USER django

ENV PATH=/home/django/.local/bin:$PATH

COPY ./api/requirements.txt /api/requirements.txt

RUN pip install -r /api/requirements.txt --no-cache-dir

RUN cd react-client-app

RUN npm install

RUN npm run build

RUN cd ..

ENTRYPOINT ["/entrypoint.sh"]
