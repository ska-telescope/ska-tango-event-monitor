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
ska-tango-event-monitor "foo/bar/pub" "foo/bar/sub"
```
