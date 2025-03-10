# ska-tango-event-monitor

`ska-tango-event-monitor` provides facilities to monitor the Tango event system
performance for your Tango devices. It refines the event system's output, 
providing clearer insights into the number of events processed, how many were missed, 
and introducing better monitoring and tracking of event-specific performance data.

Currently, it provides two python packages:

- A patched pytango wheel, which provides additional DServer Tango commands for
performance monitoring. This must be used by the Tango devices you wish to
profile.
- ska-tango-event-monitor, which provides a script of the same name which can
monitor a set of Tango devices.

## Usage

To install the `ska-tango-event-monitor` script, run the following:

```sh
poetry install
```
To use the `ska-tango-event-monitor` script,  run the following command from the
poetry envrionemtn:

```sh
ska-tango-event-monitor <device> [<device>...] [options]
```

### Arguments

- `device`: The devices or admin devices to poll (at least 1 required).
- `--poll-period`: Period between polls in seconds (default: 10.0).
- `-o, --output`: File to save data to, one JSON object per line (default: None).
- `-a, --append`: Append to file (default: False).
- `-m, --monitor-perf`: Enable performance monitoring

### Example

```sh
ska-tango-event-monitor my/running/device my/running/device2 --poll-period 5 -o output.json
```

This command will monitor the specified Tango devices, polling every 5 seconds, and save the output to `output.json`.

## Additional DServer Commands

### QueryEventSystem

Returns a json blob in a DevString.

This can potentially stall the subscriber thread, so should be called
infrequently.

### StartEventSystemPerfMon

Starts record samples for events published and received.  This could have a
performance impact on your device, so use with caution.  The samples will be
included in the next call to QueryEventSystem.  Only the most recent 256 samples
(for publisher and subscriber) are recorded.

### StopEventSystemPerfMon

Stops the recording of performance samples.

## Building

To build the patched wheel run the following:

```
make build_pytango950
```

## Local testing

After running building the patched wheel, a test OCI image can be built by
running:

```
./tests/build.sh
```

These can then be deployed with:

```sh
docker compose -f tests/compose.yaml up -d
export TANGO_HOST=localhost:10000
```

This provides a Tango database on `locahost:10000` and two devices
`foo/bar/pub` and `foo/bar/sub`.  `foo/bar/sub` can be made to start
subscriptions to `foo/bar/pub` by invoking the `StartSubscriptions` command:

```sh
python -c "import tango; tango.DeviceProxy("foo/bar/sub").StartSubscription()"
```

The devices can then both be monitored with:

```sh
ska-tango-event-monitor -m "foo/bar/pub" "foo/bar/sub"
```

## Pipeline Integration

Currently, this utility and patch wheel are manually applied within shell sessions on pods deployed in both local and ITF clusters.

Multiple Tango device servers can be monitored at once and it is recommend to
monitor them all with a single monitoring process so that they are sampled at
the same time.  This makes it easier to correlate the event system query data
between devices.

Each device which you want to monitor must be run from a pod with the patched
pytango wheel. The ska-tango-event-monitor python package does _not_ require the
patched pytango wheel.

To streamline usage, we propose adding a dedicated job to the test stage. This job will:

* Stream summarized event processing information during test execution.
* Capture and save events transmitted over the ZMQ wire to a file called `zmq-events.json`

This file will contain detailed event data, including device (server) publications, client subscriptions to attributes, and their respective callback counts.

To further simplify management, a make target will be integrated into the ska-cicd-makefile. In the interim, the pipeline structure from [this example pipeline](https://gitlab.com/ska-telescope/ska-mid-dish-manager/-/pipelines/1698758127) can be replicated (for integration environment, wait for make target).

**Do the following**:

### Select an ska-tango-event-monitor commit to use

Currently, ska-tango-event-monitor is unreleased and the utility is only
guaranteed to work with a patched wheel built from the same commit.  Browse the
package registry
[here](https://gitlab.com/ska-telescope/ska-tango-event-monitor/-/packages) to
select a commit from the `main` branch, let's call it `$STEM_SHA`.

### Update or Add a Dockerfile to install the built wheel and ska-tango-event-monitor

``` bash
# ./build-with-custom-whl/Dockerfile
...

# install custom pytango wheel from gitlab registry
# each pod containing a device server that wants to be monitored must use the
# patched version of pytango.  Currently, patched wheels based on 9.5.0 and 9.5.1
# are available.
RUN pip install pytango==9.5.0+dev.c${STEM_SHA} --force-reinstall --index-url https://gitlab.com/api/v4/projects/67270251/packages/pypi/simple
RUN pip install numpy==1.26.4 # Required for pytango 9.5.0

# install ska-tango-event-monitor from gitlab registry
# This package does not require the patched version of pytango, but it is often
# easiest to run the script from a device server pod
RUN pip install ska-tango-event-monitor==0.0.0+dev.c${STEM_SHA} --index-url https://gitlab.com/api/v4/projects/67270251/packages/pypi/simple
```

### Point your docker build command to the new dockerfile

```bash
# ./Makefile
...

OCI_IMAGE_FILE_PATH = build-with-custom-whl/Dockerfile
```

### Add jobs to stream and store the events

``` bash
# .gitlab-ci.yml
...

stream-processed-zmq-events:
  tags:
    - ${SKA_K8S_RUNNER}
  variables:
    KUBE_NAMESPACE: 'ci-$CI_PROJECT_NAME-$CI_COMMIT_SHORT_SHA'
    TARGET_POD_NAME: <the-pod-to-run-the-sampling-script>
    DEVICE_NAMES: "<foo/bar/1> <foo/bar/2> ..."
  allow_failure: true
  when: always
  stage: test
  script:
    - git clone https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile.git
    - cd ska-cicd-makefile
    - KUBE_APP=<k8s-app-label-name> make k8s-wait
    - echo "Starting ZMQ event monitoring on $DEVICE_NAME in namespace $KUBE_NAMESPACE"
    - kubectl exec -i $TARGET_POD_NAME -n $KUBE_NAMESPACE -- sudo touch zmq-events.json
    - kubectl exec -i $TARGET_POD_NAME -n $KUBE_NAMESPACE -- sudo chown tango zmq-events.json
    - kubectl exec -i $TARGET_POD_NAME -n $KUBE_NAMESPACE -- /app/bin/ska-tango-event-monitor $DEVICE_NAMES --monitor-perf --append --output zmq-events.json 

stop-streaming-and-store-zmq-events:
  tags:
    - ${SKA_K8S_RUNNER}
  variables:
    KUBE_NAMESPACE: 'ci-$CI_PROJECT_NAME-$CI_COMMIT_SHORT_SHA'
    TARGET_POD_NAME: <the-pod-to-run-the-sampling-script>
  stage: test
  when: always
  allow_failure: true
  script:
    - echo "Test run has completed, collecting events recorded"
    - mkdir -p build
    - kubectl exec -i $TARGET_POD_NAME -n $KUBE_NAMESPACE -- cat zmq-events.json >> build/zmq-events.json
    - kubectl exec -i $TARGET_POD_NAME -n $KUBE_NAMESPACE -- pkill -f "/app/bin/ska-tango-event-monitor"
  needs:
    - k8s-test-runner
  artifacts:
    name: "$CI_JOB_NAME-$CI_JOB_ID-recorded-events"
    paths:
      - build/
```
