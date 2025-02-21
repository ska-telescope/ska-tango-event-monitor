ARG BUILD_IMAGE=artefact.skao.int/ska-build-python:0.1.1
ARG BASE_IMAGE=artefact.skao.int/ska-tango-images-tango-python:0.1.0
FROM $BUILD_IMAGE AS build

ENV VIRTUAL_ENV=/app
RUN set -xe; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        python3-venv; \
    python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir /src
COPY ./dist/pytango-9.5.0+dev-cp310-cp310-manylinux_2_35_x86_64.whl /src/pytango-9.5.0+dev-cp310-cp310-manylinux_2_35_x86_64.whl
COPY ./MyServer.py /src/MyServer.py
RUN pip install numpy==1.26.4 /src/pytango-9.5.0+dev-cp310-cp310-manylinux_2_35_x86_64.whl
RUN cp /src/MyServer.py /app/bin/MyServer && chmod +x /app/bin/MyServer

# We don't want to copy pip into the runtime image
RUN pip uninstall -y pip

FROM $BASE_IMAGE

ENV VIRTUAL_ENV=/app
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=build $VIRTUAL_ENV $VIRTUAL_ENV
