import time

import psutil
from hermes_stream_nodes import SerialStream

from hermes_framing_nodes import BurstLinkNode


def main():
    serial_node = SerialStream(SerialStream.Config(port="COM9", baudrate=115200))
    serial_node.init()

    node = BurstLinkNode(BurstLinkNode.Config(stream="serial_node.config"))
    node.init(serial_node)

    print_timestamp = time.time()

    assert node.statistics is not None
    assert serial_node.statistics is not None

    while True:
        node.read()

        if time.time() - print_timestamp > 1:
            print_timestamp = time.time()
            serial_rate = serial_node.statistics.get_rates()
            packet_rate = node.statistics.get_rates()
            print(packet_rate, serial_rate, f"CPU usage: {psutil.cpu_percent(interval=None)}%")

        time.sleep(0.01)


if __name__ == "__main__":
    main()
