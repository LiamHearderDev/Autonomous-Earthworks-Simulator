from pathlib import Path
from types import SimpleNamespace

import pytest

from excavator import gnss_export


@pytest.fixture
def samples():
    header = SimpleNamespace(
        stamp=SimpleNamespace(sec=42, nanosec=123), frame_id="excavator/odom"
    )
    fix = SimpleNamespace(
        header=header,
        latitude=48.08028,
        longitude=11.63806,
        altitude=553.0,
        status=SimpleNamespace(status=0),
    )
    pose = SimpleNamespace(
        header=header,
        pose=SimpleNamespace(
            position=SimpleNamespace(x=1.25, y=-2.5, z=0.0),
            orientation=SimpleNamespace(x=0.0, y=0.0, z=0.5, w=0.8660254),
        ),
    )
    return [
        ("/fix", fix, 1_000_000_001),
        ("/gnss/pose", pose, 1_000_000_002),
        ("/gnss/heading", SimpleNamespace(data=30.0), 1_000_000_003),
    ]


def test_exports_all_topics_values_timestamps_units_and_counts(tmp_path, samples):
    output = tmp_path / "data.txt"
    counts = gnss_export.write_export(Path("bag"), output, iter(samples))

    text = output.read_text(encoding="utf-8")
    assert "Latitude (degrees): 48.08028" in text
    assert "Longitude (degrees): 11.63806" in text
    assert "Altitude (metres): 553.0" in text
    assert "Local position (metres): x=1.25, y=-2.5, z=0.0" in text
    assert "Quaternion: x=0.0, y=0.0, z=0.5, w=0.8660254" in text
    assert "Compass heading (degrees clockwise from north): 30.0" in text
    assert "Recorded timestamp (nanoseconds): 1000000001" in text
    assert "Recorded timestamp (nanoseconds): 1000000003" in text
    assert "Message timestamp (seconds): 42.000000123" in text
    assert "Frame: excavator/odom" in text
    assert counts == {"/fix": 1, "/gnss/pose": 1, "/gnss/heading": 1}
    assert text.endswith("/fix: 1\n/gnss/pose: 1\n/gnss/heading: 1\n")
    assert list(tmp_path.iterdir()) == [output]


def test_partial_bag_and_unrelated_topics(tmp_path, samples):
    output = tmp_path / "fix.txt"
    records = [samples[0], ("/camera/image", object(), 2)]

    counts = gnss_export.write_export(Path("bag"), output, records)

    assert counts == {"/fix": 1, "/gnss/pose": 0, "/gnss/heading": 0}
    assert "/camera/image" not in output.read_text()


@pytest.mark.parametrize("records", [[], [("/odom", object(), 1)]])
def test_empty_export_creates_no_output_or_temporary_files(tmp_path, records):
    with pytest.raises(ValueError, match="no recorded GNSS messages"):
        gnss_export.write_export(Path("bag"), tmp_path / "empty.txt", records)

    assert list(tmp_path.iterdir()) == []


def test_existing_output_is_preserved(tmp_path, samples):
    output = tmp_path / "existing.txt"
    output.write_text("keep this")

    with pytest.raises(FileExistsError, match="Choose another filename"):
        gnss_export.write_export(Path("bag"), output, samples)

    assert output.read_text() == "keep this"
    assert list(tmp_path.iterdir()) == [output]


def test_read_failure_does_not_leave_a_partial_export(tmp_path, samples):
    def failing_reader():
        yield samples[0]
        raise RuntimeError("corrupt recording")

    with pytest.raises(RuntimeError, match="corrupt recording"):
        gnss_export.write_export(Path("bag"), tmp_path / "data.txt", failing_reader())

    assert list(tmp_path.iterdir()) == []


def test_output_created_during_export_is_preserved(tmp_path, samples):
    output = tmp_path / "data.txt"

    def records():
        yield samples[0]
        output.write_text("created by someone else")

    with pytest.raises(FileExistsError):
        gnss_export.write_export(Path("bag"), output, records())

    assert output.read_text() == "created by someone else"
    assert list(tmp_path.iterdir()) == [output]


@pytest.mark.parametrize("custom_output", [False, True])
def test_cli_exports_without_ros_imports(
    tmp_path, samples, monkeypatch, capsys, custom_output
):
    bag = tmp_path / "recording"
    bag.mkdir()
    (bag / "metadata.yaml").write_text("test metadata")
    monkeypatch.setattr(gnss_export, "read_gnss_messages", lambda path: iter(samples))
    output = tmp_path / ("custom.txt" if custom_output else "recording.txt")
    arguments = [str(bag)]
    if custom_output:
        arguments += ["-o", str(output)]

    assert gnss_export.main(arguments) == 0
    assert output.is_file()
    assert f"Exported 3 GNSS messages to {output}" in capsys.readouterr().out
    assert (bag / "metadata.yaml").read_text() == "test metadata"


def test_cli_missing_bag(tmp_path, capsys):
    assert gnss_export.main([str(tmp_path / "missing")]) == 1
    assert "Bag directory does not exist" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_cli_unfinished_recording(tmp_path, capsys):
    bag = tmp_path / "recording"
    bag.mkdir()

    assert gnss_export.main([str(bag)]) == 1
    assert "Stop the recorder with Ctrl+C first" in capsys.readouterr().err
    assert not (tmp_path / "recording.txt").exists()


def test_cli_reader_error_has_no_traceback_or_partial_output(
    tmp_path, monkeypatch, capsys
):
    bag = tmp_path / "recording"
    bag.mkdir()
    (bag / "metadata.yaml").write_text("test metadata")

    def fail(path):
        raise RuntimeError("cannot read bag")

    monkeypatch.setattr(gnss_export, "read_gnss_messages", fail)

    assert gnss_export.main([str(bag)]) == 1
    assert capsys.readouterr().err.strip() == "GNSS export failed: cannot read bag"
    assert not (tmp_path / "recording.txt").exists()


def test_cli_existing_output_is_preserved(tmp_path, samples, monkeypatch, capsys):
    bag = tmp_path / "recording"
    bag.mkdir()
    (bag / "metadata.yaml").write_text("test metadata")
    output = tmp_path / "recording.txt"
    output.write_text("keep this")
    monkeypatch.setattr(gnss_export, "read_gnss_messages", lambda path: iter(samples))

    assert gnss_export.main([str(bag)]) == 1
    assert "Output already exists" in capsys.readouterr().err
    assert output.read_text() == "keep this"
