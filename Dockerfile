FROM ubuntu:20.04

RUN  apt-get update \
  && apt-get install -y wget apt-utils

RUN apt-get update && apt-get install -y gnupg2
ENV TZ=Asia/Kolkata \
    DEBIAN_FRONTEND=noninteractive
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Install Chrome.
RUN apt-get update && apt-get -y install google-chrome-stable

RUN echo "chrome install"

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3
RUN apt install -y python3-pip

WORKDIR /video-call-recorder

COPY . .

RUN pip install -r requirements.txt

ENV DISPLAY=:1

CMD ["python3", "meeting_recorder.py"]