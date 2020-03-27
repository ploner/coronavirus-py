FROM python:3.8

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir /corona-app-py
WORKDIR /corona-app-py
COPY ./ ./

EXPOSE 8050
ENV NAME Corona
CMD ["python", "./app.py"]
