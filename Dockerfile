FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python3-pip build-essential
COPY . /beta
WORKDIR /beta
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["app.py"]