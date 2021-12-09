#
# Docker file for Message in a Bottle v1.0
#
FROM python:3.8
LABEL maintainer="4_squad"
LABEL version="1.0"
LABEL description="Message in a Bottle User Microservice"

# creating the environment
COPY . /app
# setting the workdir
WORKDIR /app
# set timezone to Europe/Rome
ENV TZ=Europe/Rome

# installing all requirements
RUN ["pip", "install", "-r", "requirements.prod.txt"]

# install english language to censor contents
RUN ["python3", "-m", "spacy", "download", "en"]

# exposing the port
EXPOSE 5003/tcp

# Main command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]