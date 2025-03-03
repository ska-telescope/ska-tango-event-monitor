#!/usr/bin/env python

from tango import EventType, DeviceProxy
from tango.utils import EventCallback
from tango.server import Device, run, attribute, command

class PubDevice(Device):
    def init_device(self):
        self.counter = 0;

    @attribute(polling_period=200, abs_change=1)
    def attr(self) -> int:
        result = self.counter
        self.counter += 1
        return result

    @attribute(polling_period=200, abs_change=1)
    def attr2(self) -> int:
        result = self.counter
        self.counter += 1
        return result

class SubDevice(Device):
    @command
    def StartSubscription(self) -> None:
        self.device_proxy = DeviceProxy("foo/bar/pub")
        self.sub = self.device_proxy.subscribe_event("attr", EventType.CHANGE_EVENT, EventCallback())
        self.sub2 = self.device_proxy.subscribe_event("attr2", EventType.CHANGE_EVENT, EventCallback())

    @command
    def CleanSubscription(self) -> None:
        self.device_proxy.unsubscribe_event(self.sub)
        self.device_proxy.unsubscribe_event(self.sub2)


if __name__ == '__main__':
    run((PubDevice, SubDevice))
