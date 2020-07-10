FROM artifactory.homecredit.ru:9555/containerization/base-microservice-python:latest


MAINTAINER Yuriy Rumyantsev

ARG BUILD_VERSION
ARG BUILD_DATE
ARG GIT_COMMIT

LABEL maintainer="YRumyantsev@homecredit.ru" \
      version="$BUILD_VERSION" \
      description="Wiremock config restore or backup Docker image" \
      hcfb.devops.builder-node.image.build-version="$BUILD_VERSION" \
      hcfb.devops.builder-node.image.build-date="$BUILD_DATE" \
      hcfb.devops.builder-node.image.git-commit="$GIT_COMMIT"


RUN apt update \
    && apt-get --assume-yes install git telnet nano \
    && rm -f /etc/apt/sources.list

ADD app /opt/app
ADD configmodule.py /opt/configmodule.py
ADD requirements.txt /opt/requirements.txt
ADD run.py /opt/run.py 
ADD README.md /opt/README.md

# Install dependency
RUN cd /opt \
    && pip install -r requirements.txt \
    && ls -la

VOLUME /opt/app/static/uploads

EXPOSE 5000

WORKDIR /opt

CMD ["flask", "run", "--host", "0.0.0.0" ]
