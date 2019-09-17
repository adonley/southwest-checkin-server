FROM python:3.7
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV FLASK_APP=main
ENV FLASK_ENV=development
CMD ["python", "main.py"]
