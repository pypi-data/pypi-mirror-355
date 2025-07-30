import time

from hermes_stream_nodes import SerialStream

from hermes_framing_nodes import BurstLinkNode
from hermes_odin_nodes import OdinStreamNode


def main():
    serial_node = SerialStream(SerialStream.Config(port="COM9", baudrate=115200))
    serial_node.init()

    burst_node = BurstLinkNode(BurstLinkNode.Config(stream=""))
    burst_node.init(serial_node)

    odin_stream_node = OdinStreamNode(
        OdinStreamNode.Config(
            burst_node="",
            odin_definitions=r"C:\Users\fvernieuwe\Downloads\OD.odin",
            time_correction=OdinStreamNode.TimeCorrection(counts_per_second=1000000),
        )
    )
    odin_stream_node.init(burst_node)

    assert burst_node.statistics is not None
    assert serial_node.statistics is not None

    while True:
        time.sleep(1)
        data = odin_stream_node.read_merged()
        # print timestamp
        if data is None:
            continue
        print(data)
        # # print timestamps
        # timestamps = data.get_column("timestamp")
        # if timestamps is not None:
        #     print(f"Received data with timestamps: {timestamps.to_list()}")
        # else:
        #     print("No timestamps found in the data.")


if __name__ == "__main__":
    main()
