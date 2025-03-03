ARG SKABUILD_VERSION=0.1.2
ARG BUILD_IMAGE="artefact.skao.int/ska-build:${SKABUILD_VERSION}"

FROM $BUILD_IMAGE AS build_system_deps
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libboost-python-dev \
        libjpeg8-dev; \
    rm -rf /var/lib/apt/lists/*; \
    echo libjpeg8   >> /runtime_deps.txt;

FROM build_system_deps AS build_tools
ARG DEBIAN_FRONTEND=noninteractive

RUN set -xe; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        autoconf \
        automake \
        cmake \
        curl \
        file \
        git \
        libtool \
        patchelf \
        pkg-config \
        python3-pip \
        unzip; \
    rm -rf /var/lib/apt/lists/*

FROM build_tools AS build_zmq
ARG ZEROMQ_VERSION=4.3.5

ENV ZEROMQ_DOWNLOAD_URL="https://github.com/zeromq/libzmq/archive/v${ZEROMQ_VERSION}.tar.gz"

RUN mkdir /usr/src/zeromq
WORKDIR /usr/src/zeromq
RUN set -xe; \
    curl -kfsSL "$ZEROMQ_DOWNLOAD_URL" -o zeromq.tar.gz; \
    tar xf zeromq.tar.gz -C /usr/src/zeromq --strip-components=1; \
    ./autogen.sh; \
    ./configure --enable-static=no; \
    make -C /usr/src/zeromq -j$(nproc); \
    make -C /usr/src/zeromq install

FROM build_zmq AS build_cppzmq
ARG CPPZMQ_VERSION=4.10.0

ENV CPPZMQ_DOWNLOAD_URL="https://github.com/zeromq/cppzmq/archive/v${CPPZMQ_VERSION}.tar.gz"

RUN mkdir /usr/src/cppzmq
WORKDIR /usr/src/cppzmq
RUN set -xe; \
    curl -kfsSL "$CPPZMQ_DOWNLOAD_URL" -o cppzmq.tar.gz; \
    tar xf cppzmq.tar.gz -C /usr/src/cppzmq --strip-components=1; \
    cmake -Bbuild -S. -DCPPZMQ_BUILD_TESTS=OFF; \
    cmake --build build --target install

FROM build_tools AS build_omniorb
ARG OMNIORB_VERSION=4.3.2

ENV OMNIORB_DOWNLOAD_URL="https://sourceforge.net/projects/omniorb/files/omniORB/omniORB-${OMNIORB_VERSION}/omniORB-${OMNIORB_VERSION}.tar.bz2/download"

RUN mkdir /usr/src/omniorb
WORKDIR /usr/src/omniorb
RUN set -xe; \
    curl -kfsSL "$OMNIORB_DOWNLOAD_URL" -o omniorb.tar.bz2; \
    tar xf omniorb.tar.bz2 -C /usr/src/omniorb --strip-components=1; \
    ./configure --enable-static=no --disable-longdouble; \
    make -C /usr/src/omniorb -j$(nproc); \
    make -C /usr/src/omniorb install

FROM build_tools AS build_tango
ARG TANGOIDL_VERSION=5.1.2
ARG CPPTANGO_VERSION=9.5.0

COPY --from=build_cppzmq /usr/local /usr/local
COPY --from=build_omniorb /usr/local /usr/local

RUN mkdir -p /usr/src/idl
WORKDIR /usr/src/idl
RUN set -xe; \
    git clone --depth=1 --branch=${TANGOIDL_VERSION} -c advice.detachedHead=false \
        https://gitlab.com/tango-controls/tango-idl.git /usr/src/idl; \
    cmake -B /usr/src/idl/build -DCMAKE_INSTALL_PREFIX=/usr/local/ /usr/src/idl; \
    cmake --build /usr/src/idl/build  -j$(nproc) --target install

RUN mkdir -p /usr/src/tango
WORKDIR /usr/src/tango
RUN set -xe; \
    git clone --depth=1 --branch=${CPPTANGO_VERSION} --recurse-submodules --shallow-submodules \
        -c advice.detachedHead=false https://gitlab.com/tango-controls/cppTango.git /usr/src/tango
COPY patches/ ./patches/
RUN set -xe; \
    git apply patches/*; \
    cmake -S. -Bbuild \
        -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_INSTALL_RPATH=/usr/local/lib; \
    cmake --build /usr/src/tango/build -j$(nproc) --target install

FROM build_tools AS build_pytango
ARG PYTANGO_VERSION=9.5.0
ARG CI_COMMIT_SHORT_SHA

COPY --from=build_tango /usr/local /usr/local

RUN mkdir -p /usr/src/pytango
WORKDIR /usr/src/pytango
RUN set -xe; \
    git clone --depth=1 --branch=v${PYTANGO_VERSION} --recurse-submodules --shallow-submodules \
        -c advice.detachedHead=false https://gitlab.com/tango-controls/pytango.git /usr/src/pytango
COPY patch-pytango-version.sh .
RUN ./patch-pytango-version.sh; \
    python3 -m pip install build auditwheel; \
    python3 -m build --wheel

RUN auditwheel repair --plat manylinux_2_35_x86_64 dist/*.whl
