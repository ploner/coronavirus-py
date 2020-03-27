FROM python:3.8
LABEL maintainer "Meinhard Ploner <meinhard.ploner@gmail.com>"

WORKDIR /code

COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ ./

EXPOSE 8050

CMD ["python", "./app.py"]
