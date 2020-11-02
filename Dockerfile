FROM python:3

ADD ./distributed_kvs /distributed_kvs
ADD ./requirements.txt ./distributed_kvs
WORKDIR /distributed_kvs

RUN pip3 install -r requirements.txt
EXPOSE 8081

CMD ["python", "__main__.py"]