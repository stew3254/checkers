FROM python:3

WORKDIR /srv/checkers
EXPOSE 5000

RUN apt-get update -y && apt-get upgrade -y && yes | apt-get dist-upgrade
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./src src
CMD FLASK_ENV=development FLASK_APP=src/app.py flask run --host='0.0.0.0'