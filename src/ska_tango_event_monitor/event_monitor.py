from tango import DeviceProxy, DevFailed, Group
from argparse import ArgumentParser
from datetime import datetime
import re
import json
import statistics
import itertools
import time

# TODO: split this up.

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="ska-tango-event-moniotor",
        description="Called QueryEventSystem periodically and summarizes the output",
    )
    parser.add_argument('device', help='device or admin device to poll', nargs='+')
    parser.add_argument('--poll-period', help='period between polls in seconds', type=float, default=10.0)
    parser.add_argument('-o', '--output', help='file to save data to, one json object per line', default=None)
    parser.add_argument('-a', '--append', help='append to file', action='store_true')

    return parser

regex = re.compile("tango://[^/]+/(.*)")
def strl(ev):
    m = regex.match(ev)
    return m.group(1)

def print_stats(sorted_array, name, units=' (μs)'):
    mean = float(statistics.mean(sorted_array))
    stdev = float(statistics.pstdev(sorted_array))
    err = stdev / (len(sorted_array) ** 0.5)
    minimum = min(sorted_array)
    maximum = max(sorted_array)
    try:
        pc10 = sorted_array[len(sorted_array) // 10]
        pc50 = sorted_array[len(sorted_array) // 2]
        pc90 = sorted_array[len(sorted_array) - len(sorted_array) // 10]
    except:
        pc10 = None
        pc50 = None
        pc90 = None
    name = name + units;
    print(f"\t{name:>30}: {mean:10.2f}±{err:<10.2f} (count={len(sorted_array)}, min={minimum}, 10%={pc10}, med={pc50}, 90%={pc90} max={maximum})")

def print_summary(name, data, last_data):
    server = data['server']
    counters = server['event_counters']
    last_counters = last_data['server']['event_counters'] if last_data is not None else {}
    event_names = set(itertools.chain(counters.keys(), last_counters.keys()))
    new = []
    removed = []
    changed = []
    for ev in event_names:
        if ev in counters and ev not in last_counters:
            new.append(ev)
        elif ev in last_counters and ev not in counters:
            removed.append(ev)
        elif counters[ev] != last_counters[ev]:
            changed.append(ev)

    if len(new) > 0:
        print(f"{name} new publishers:")
        for ev in new:
            print(f"\t{strl(ev)}: {counters[ev]}")

    if len(changed) > 0:
        print(f"{name} published events:")
        for ev in changed:
            print(f"\t{strl(ev)}: {counters[ev] - last_counters[ev]:+}")

    if len(removed) > 0:
        print(f"{name} removed publishers:")
        for ev in removed:
            print(f"\t{strl(ev)}")

    if server['perf_stats'] is not None and len(server['perf_stats']) > 0:
        print(f'{name} publishing performance:')
        stats = server['perf_stats']
        micros_since_last_events = sorted(x["micros_since_last_event"] for x in stats if x["micros_since_last_event"] != -1)
        print_stats(micros_since_last_events, "Event Gaps")
        push_event_micros = sorted(x["push_event_micros"] for x in stats)
        print_stats(push_event_micros, "Event push time")

    if 'client' in data:
        client = data['client']
        callbacks = client['event_callbacks']
        last_callbacks = last_data['client']['event_callbacks'] if last_data is not None and 'client' in last_data else {}
        event_names = set(itertools.chain(callbacks.keys(), last_callbacks.keys()))
        new = []
        removed = []
        changed = []
        for ev in event_names:
            if ev in callbacks and ev not in last_callbacks:
                new.append(ev)
            elif ev in last_callbacks and ev not in callbacks:
                removed.append(ev)
            elif callbacks[ev] != last_callbacks[ev]:
                changed.append(ev)

        if len(new) > 0:
            print(f"{name} new subscriptions:")
            for ev in new:
                v = callbacks[ev]
                print(f'\t{strl(ev)}: {v["server_counter"]} ({v["callback_count"]} callback(s) registered)')

        if len(changed) > 0:
            print(f"{name} received events or callbacks changed:")
            for ev in changed:
                v = callbacks[ev]
                last = last_callbacks[ev]
                ev_name = strl(ev)
                print(f'\t{ev_name}: {v["event_count"] - last["event_count"]:+} received events')
                print(f'\t{" ":>{len(ev_name)}}  {last["server_counter"]} -> {v["server_counter"]} ({v["server_counter"] - last["server_counter"]:+}) server counter')
                if v["callback_count"] != last["callback_count"]:
                    print(f'\t{" ":>{len(ev_name)}}  {v["callback_count"] - last["callback_count"]:+} callbacks')
                if v["missed_event_count"] != last["missed_event_count"]:
                    print(f'\t{" ":>{len(ev_name)}}  {v["missed_event_count"] - last["missed_event_count"]:+} missed events')

        if len(removed) > 0:
            print(f"{name} removed subscriptions:")
            for ev in removed:
                print(f"\t{strl(ev)}")

        if client['perf_stats'] is not None and len(client['perf_stats']) > 0:
            stats = client['perf_stats']
            print(f'{name} subscription performance:')
            micros_since_last_events = sorted(x["micros_since_last_event"] for x in stats if x["micros_since_last_event"] != -1)
            print_stats(micros_since_last_events, "Event Gaps")
            sleep_micros = sorted(x["sleep_micros"] for x in stats)
            print_stats(sleep_micros, "Sleeping time")
            first_callback_latency = sorted(x["first_callback_lactency_micros"] for x in stats if x["first_callback_lactency_micros"] is not None)
            print_stats(first_callback_latency, "First callback latency")
            callback_count = sorted(x["callback_count"] for x in stats)
            print_stats(callback_count, "Callback Count", "")
            wake_count = sorted(x["wake_count"] for x in stats)
            print_stats(wake_count, "Wake Count", "")
            grouped = itertools.groupby(sorted(stats, key=lambda x: x["att_name"]), lambda x: x["att_name"])
            process_micros = dict((k, list(c["process_micros"] for c in x)) for k, x in grouped)
            for k, times in process_micros.items():
                print_stats(sorted(times), f"{k} processing time")

#TODO: Compress what we save to disk by only saving the changes...
def main():
    args = build_parser().parse_args()

    group = Group("EventQueryGroup")
    for name in args.device:
        display_name = name
        dp = DeviceProxy(name)

        if dp.info().dev_class != 'DServer':
            adm_name = dp.adm_name()
            display_name = f'{adm_name} (from {name})'
            name = adm_name
            dp = DeviceProxy(name)

        if 'QueryEventSystem' not in dp.get_command_list():
            print(f'{display_name} does not support QueryEventSystem, is this pod using "PyTango 9.5.1234"?', file=sys.stderr)
            sys.exit(1)

        if name not in group.get_device_list():
            group.add(name)

    last_data = {}
    for name in group.get_device_list():
        last_data[name] = None

    if args.append:
        mode = 'a'
    else:
        mode = 'w'
    output = None
    if args.output is not None:
        output = open(args.output, mode)

    while(True):
        next_poll = time.time() + args.poll_period

        try:
            now = datetime.now().isoformat()
            replies = group.command_inout("QueryEventSystem")

            line = ''
            if output is not None:
                line += f'{{"time":"{now}", "replies":{{'

            print(f"*** {now}")
            first = True
            for reply in replies:
                name = reply.dev_name()
                if output is not None:
                    if not first:
                        line += ','
                    line += f'"{name}":'
                    first=False
                if reply.has_failed():
                    errs = reply.get_err_stack()
                    print(errs, file=sys.stderr)
                    if output is not None:
                        line += f'{{"error":"{repr(errs)}"}}'
                else:
                    s = reply.get_data()

                    if output is not None:
                        line += f'{{"data":{s}}}'

                    data = json.loads(s)
                    print_summary(name, data, last_data[name])
                    last_data[name] = data

            if output is not None:
                output.write(f'{line}\n')
            print(f"\n\n")
        except DevFailed as exc:
            print(exc, file=sys.stderr)

        sleep_for = next_poll - time.time()
        if sleep_for > 0.001:
            time.sleep(sleep_for)
        elif sleep_for < 0:
            print(f'poll time missed by {-sleep_for}s', file=sys.stderr)


if __name__ == '__main__':
    main()
