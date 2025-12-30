FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

ARG EMANE_VERSION=1.5.3
ARG EMANE_DICT=emane-${EMANE_VERSION}-release-1
ARG EMANE_BUNDLE=${EMANE_DICT}.ubuntu-22_04.amd64

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        autoconf automake cmake debhelper dh-python g++ gcc git \
        libboost-program-options-dev libconfig++-dev libfftw3-dev libmbedtls-dev libpcap-dev \
        libpcre3-dev libprotobuf-dev libsctp-dev libsqlite3-dev libtool libxml2-dev libzmq3-dev \
        libzmq5 lsb-release pkg-config protobuf-compiler python3-dev python3-lxml python3-protobuf \
        python3-setuptools python3-zmq sqlite3 uuid-dev \
        iputils-ping tcpdump iperf3 net-tools python3-pip iproute2 \
        wget ca-certificates; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    cd /tmp; \
    wget https://adjacentlink.com/downloads/emane/${EMANE_BUNDLE}.tar.gz; \
    tar zxf ${EMANE_BUNDLE}.tar.gz; \
    cd ${EMANE_DICT}/debs/ubuntu-22_04/amd64; \
    apt-get update; \
    DEBS="$(find .. -name '*.deb' -print | egrep -v '(dev|debug)')"; \
    apt-get install -y --no-install-recommends $DEBS; \
    rm -rf /var/lib/apt/lists/*; \
    cd /; \
    rm -rf /tmp

