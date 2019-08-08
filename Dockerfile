FROM python:3.7


 COPY ./requirements.txt /requirements.txt
 COPY ./slack_snipeit.py /slack_snipeit.py
 COPY ./settings.conf /settings.conf

WORKDIR /

RUN pip3 install -r requirements.txt

CMD [ "python", "./slack_snipeit.py" ]