FROM tiangolo/meinheld-gunicorn:python3.7

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

