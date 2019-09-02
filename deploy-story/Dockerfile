FROM python:3

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY /src /root
COPY /credidentals /root/.aws

EXPOSE 80

CMD [ "gunicorn", "-b", ":80", "--chdir", "/root","story:app" , "--reload", "--log-level", "debug","-w","4"]