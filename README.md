# ska-tango-event-monitor

ska-tango-event-monitor provides facilities to monitor the Tango event system
performance for your Tango devices.

Currently, it provides two python packages:

- A patched pytango wheel, which provides additional DServer Tango commands for
performance monitoring.  This must be used by the Tango devices you wish to
profile.
- ska-tango-event-monitor, which provides a script of the same name which can
monitor a set of Tango devices.

## Usage

TODO

## Additional DServer Commands

- QueryEventSystem

Returns a json blob in a DevString.

This can potentially stall the subscriber thread, so should be called
infrequently.

- StartEventSystemPerfMon

Starts record samples for events published and received.  This could have a
performance impact on your device, so use with caution.  The samples will be
included in the next call to QueryEventSystem.  Only the most recent 256 samples
(for publisher and subscriber) are recorded.

- StopEventSystemPerfMon

Stops the recording of performance samples.

