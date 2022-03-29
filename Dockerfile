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

RUN pip install selenium==4.1.0 python-dotenv==0.19.2 pymongo==4.0.1 dnspython==2.2.0 psutil==5.9.0

RUN apt-get install -y alsa-base alsa-utils
RUN apt-get install -y pulseaudio
RUN apt install -y ffmpeg
RUN apt-get install lame
RUN apt update
RUN apt install -y firefox
RUN apt update
RUN apt install -y vim

WORKDIR /video-call-recorder

COPY . .

# RUN chmod +x entrypoint.sh

# CMD ["/video-call-recorder/entrypoint.sh"]