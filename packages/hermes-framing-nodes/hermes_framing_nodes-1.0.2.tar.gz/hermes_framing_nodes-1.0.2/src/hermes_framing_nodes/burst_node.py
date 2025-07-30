import time
from typing import List, Literal

from burst_link_protocol import BurstInterfaceC, BurstSerialStatistics
from hermes_stream_nodes import GenericStreamTransport, SerialStream
from node_hermes_core.data.datatypes import PhysicalDatapacket
from node_hermes_core.depencency import NodeDependency
from node_hermes_core.links.generic_link import DataTarget
from node_hermes_core.nodes import GenericNode
from node_hermes_core.nodes.data_generator_node import AbstractDataGenerator, AbstractWorker


class BurstLinkNode(GenericNode, AbstractDataGenerator, AbstractWorker):
    class Config(GenericNode.Config):
        type: Literal["burst-link"] = "burst-link"
        stream: str | SerialStream.Config

    config: Config

    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config
        self.base_dependency = NodeDependency(name="interface", config=config.stream, reference=SerialStream)
        self.dependency_manager.add(self.base_dependency)

        self.statistics_metadata = {
            "bytes_handled": PhysicalDatapacket.PointDefinition(unit="B", precision=3, si=True),
            "bytes_processed": PhysicalDatapacket.PointDefinition(unit="B", precision=3, si=True),
            "packets_processed": PhysicalDatapacket.PointDefinition(unit="packets", precision=3, si=True),
            "crc_errors": PhysicalDatapacket.PointDefinition(unit="errors", precision=0, si=False),
            "overflow_errors": PhysicalDatapacket.PointDefinition(unit="errors", precision=0, si=False),
            "decode_errors": PhysicalDatapacket.PointDefinition(unit="errors", precision=0, si=False),
            "handled_bytes_per_second": PhysicalDatapacket.PointDefinition(unit="B/s", precision=3, si=True),
            "processed_bytes_per_second": PhysicalDatapacket.PointDefinition(unit="B/s", precision=3, si=True),
            "processed_packets_per_second": PhysicalDatapacket.PointDefinition(unit="packets/s", precision=3, si=True),
        }
        self.base_target = DataTarget("output")
        self.source_port_manager.add("output", self.base_target)

    def init(self, interface: GenericStreamTransport):  # type: ignore
        super().init()
        self.stream_interface = interface
        self.interface = BurstInterfaceC()
        self.statistics = BurstSerialStatistics()

    def deinit(self):
        super().deinit()
        self.stream_interface = None
        self.interface = None

    def read(self) -> List[bytes]:
        if self.stream_interface is None or self.interface is None:
            raise RuntimeError("Stream interface or Burst interface not initialized")
        data_read = self.stream_interface.read()

        packets = self.interface.decode(data_read)

        if self.statistics is not None:
            self.statistics.update(
                self.interface.bytes_handled,
                self.interface.bytes_processed,
                self.interface.packets_processed,
                self.interface.crc_errors,
                self.interface.overflow_errors,
                self.interface.decode_errors,
            )

        return packets

    def get_data(self) -> PhysicalDatapacket:
        assert self.statistics is not None, "Statistics not initialized"
        return PhysicalDatapacket(
            source=self.name,
            timestamp=time.time(),
            data=self.statistics.to_dict(),
            metadata=self.statistics_metadata,
        )

    def work(self):
        stats = self.get_data()
        self.base_target.put_data(stats)
