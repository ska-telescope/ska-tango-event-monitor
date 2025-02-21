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

To use the `ska-tango-event-monitor` script, run the following command:

```sh
python -m event_monitor.py <device> [options]
```

### Arguments

- `device`: The device or admin device to poll (required).
- `--poll-period`: Period between polls in seconds (default: 10.0).
- `-o, --output`: File to save data to, one JSON object per line (default: None).
- `-a, --append`: Append to file (default: False).

### Example

```sh
python -m event_monitor.py my/running/device --poll-period 5 -o output.json
```

This command will monitor the specified Tango device, polling every 5 seconds, and save the output to `output.json`.

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
