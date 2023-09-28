FROM ubuntu:22.04

RUN apt update && apt install tzdata -y
ENV TZ="Europe/Berlin"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt install -y  --no-install-recommends \
vim \
iproute2 \
curl \
wget \
sudo 

RUN apt install  -y software-properties-common
RUN sudo add-apt-repository -y ppa:openjdk-r/ppa
RUN apt remove -y software-properties-common

RUN apt update

RUN apt-get install -y openjdk-11-jdk 

RUN apt-get install -y auditd bison clang cmake curl flex fuse git ifupdown libaudit-dev libfuse-dev lsof pkg-config unzip uthash-dev
#RUN apt-get install -y linux-headers-5.15.0-70-generic
RUN apt-get install -y linux-headers-generic 


RUN apt -y autoremove

RUN  apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 user
RUN useradd -u 1000 -g 1000 -m -s /bin/bash user

# RUN usermod -aG sudo user
#RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

ENV PATH "$PATH:/SPADE/bin"

COPY run.sh /



WORKDIR /SPADE
RUN chown user:user /SPADE
USER user



# CMD ["tail", "-f", "/dev/null"]
CMD ["/run.sh"]

