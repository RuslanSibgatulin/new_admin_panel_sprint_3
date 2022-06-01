FROM python:3.9
EXPOSE 8000/tcp
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
