import argparse
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile


GNSS_TOPICS = {
    "/fix": "sensor_msgs/msg/NavSatFix",
    "/gnss/pose": "geometry_msgs/msg/PoseStamped",
    "/gnss/heading": "std_msgs/msg/Float64",
}


def read_gnss_messages(bag_path):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(bag_path), storage_id=""),
        rosbag2_py.ConverterOptions("", ""),
    )
    message_types = {}
    for topic in reader.get_all_topics_and_types():
        if topic.name not in GNSS_TOPICS:
            continue
        expected = GNSS_TOPICS[topic.name]
        if topic.type != expected:
            raise ValueError(
                f"Topic {topic.name} has type {topic.type}; expected {expected}"
            )
        message_types[topic.name] = get_message(topic.type)

    if not message_types:
        raise ValueError("The bag contains no GNSS topics")

    reader.set_filter(rosbag2_py.StorageFilter(topics=list(message_types)))
    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        yield topic, deserialize_message(data, message_types[topic]), timestamp


def format_message(topic, message, timestamp):
    lines = [f"Topic: {topic}", f"Recorded timestamp (nanoseconds): {timestamp}"]
    if topic in ("/fix", "/gnss/pose"):
        header = message.header
        lines.extend([
            f"Message timestamp (seconds): {header.stamp.sec}.{header.stamp.nanosec:09d}",
            f"Frame: {header.frame_id}",
        ])

    if topic == "/fix":
        lines.extend([
            f"Latitude (degrees): {message.latitude}",
            f"Longitude (degrees): {message.longitude}",
            f"Altitude (metres): {message.altitude}",
            f"Fix status: {message.status.status}",
        ])
    elif topic == "/gnss/pose":
        position = message.pose.position
        orientation = message.pose.orientation
        lines.extend([
            f"Local position (metres): x={position.x}, y={position.y}, z={position.z}",
            f"Quaternion: x={orientation.x}, y={orientation.y}, "
            f"z={orientation.z}, w={orientation.w}",
        ])
    elif topic == "/gnss/heading":
        lines.append(f"Compass heading (degrees clockwise from north): {message.data}")

    return "\n".join(lines) + "\n\n"


def write_export(bag_path, output_path, messages):
    if output_path.exists():
        raise FileExistsError(f"Output already exists: {output_path}. Choose another filename with -o")

    counts = dict.fromkeys(GNSS_TOPICS, 0)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=".gnss_export_",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(f"GNSS data exported from: {bag_path}\n\n")
            for topic, message, timestamp in messages:
                if topic not in GNSS_TOPICS:
                    continue
                stream.write(format_message(topic, message, timestamp))
                counts[topic] += 1

            if not any(counts.values()):
                raise ValueError("The bag contains no recorded GNSS messages")

            stream.write("Message counts:\n")
            for topic, count in counts.items():
                stream.write(f"{topic}: {count}\n")

        os.link(temporary_path, output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink()

    return counts


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Export a saved GNSS ROS bag to a readable text file. No playback is needed."
    )
    parser.add_argument("bag", type=Path, help="Saved ROS bag directory")
    parser.add_argument("-o", "--output", type=Path, help="Text output filename (default: BAG_FOLDER.txt)")
    options = parser.parse_args(args)
    bag_path = options.bag.expanduser().absolute()
    output_path = (
        options.output.expanduser().absolute()
        if options.output is not None
        else bag_path.with_name(bag_path.name + ".txt")
    )

    try:
        if not bag_path.is_dir():
            raise ValueError(f"Bag directory does not exist: {bag_path}")
        if not (bag_path / "metadata.yaml").is_file():
            raise ValueError(
                f"Bag metadata.yaml is missing: {bag_path}. Stop the recorder with Ctrl+C first"
            )
        counts = write_export(bag_path, output_path, read_gnss_messages(bag_path))
    except (OSError, RuntimeError, ValueError, ImportError) as error:
        print(f"GNSS export failed: {error}", file=sys.stderr)
        return 1

    print(f"Exported {sum(counts.values())} GNSS messages to {output_path}")
    for topic, count in counts.items():
        print(f"{topic}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
