import json
import pytest
from typing import cast

import notifier
from chording_modes import ChordingMode
from config import Config
from config_wrapper import ConfigWrapper
from notifier import ConfigNotificationSender, MissedKey, _load_json_counts


def make_config(*, mode="load", chip_path="", chara_path="", log_to_path="",
                log_to_stdout=False, chording="charachorder", blocked=None):
    return Config({
        "general": {"mode": chording},
        "notification": {
            "mode": "notify",
            "message": "$triggers = $chord",
            "title": "possible missed chord",
        },
        "filter": {"blocked": blocked or [], "allowed": []},
        "logging": {
            "log_to_stdout": log_to_stdout,
            "log_to_path": log_to_path,
            "mode": mode,
            "chip_path": chip_path,
            "chara_path": chara_path,
        },
    })


class FakeConfigWrapper:
    def __init__(self, config):
        self.config = config

    def chara_mode(self):
        return self.config.general.mode == ChordingMode.CHARA_CHORDER

    def make_message(self, triggers, val):
        return self.config.notification.message.replace(
            "$triggers", str(triggers)).replace("$chord", val)

    def filtered(self, s):
        return s in self.config.filter.blocked


def make_sender(config):
    return ConfigNotificationSender(cast(ConfigWrapper, FakeConfigWrapper(config)))


@pytest.fixture(autouse=True)
def displayed(monkeypatch):
    calls = []
    monkeypatch.setattr(
        notifier, "display_notification",
        lambda title, message, cw: calls.append((title, message)))
    return calls


class TestMissedKey:
    def test_triggers_are_canonicalized(self):
        assert MissedKey.of("x", ["b", "a"]) == MissedKey.of("x", ["a", "b"])

    def test_different_chords_are_distinct(self):
        assert MissedKey.of("x", ["a"]) != MissedKey.of("y", ["a"])


class TestPathSelection:
    def test_chord_mode_writes_chord_path(self, tmp_path):
        chord_path = tmp_path / "chords.json"
        chip_path = tmp_path / "chips.json"
        sender = make_sender(make_config(
            chara_path=str(chord_path), chip_path=str(chip_path)))
        sender.send_notification("the", ["t h e"])

        assert chord_path.exists()
        assert not chip_path.exists()
        assert json.loads(chord_path.read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 1}]

    def test_chip_mode_writes_chip_path(self, tmp_path):
        chord_path = tmp_path / "chords.json"
        chip_path = tmp_path / "chips.json"
        sender = make_sender(make_config(
            chording="fuzzy chips",
            chara_path=str(chord_path), chip_path=str(chip_path)))
        sender.send_notification("the", ["t h e"])

        assert chip_path.exists()
        assert not chord_path.exists()

    def test_empty_path_writes_nothing(self, tmp_path):
        make_sender(make_config()).send_notification("the", ["t h e"])
        assert list(tmp_path.iterdir()) == []

    def test_creates_parent_dirs(self, tmp_path):
        chord_path = tmp_path / "nested" / "chords.json"
        make_sender(make_config(chara_path=str(chord_path))
                    ).send_notification("the", ["t h e"])
        assert chord_path.exists()


class TestModes:
    def test_overwrite_destroys_previous_session(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps(
            [{"triggers": ["old"], "chord": "old", "count": 9}]))
        sender = make_sender(make_config(
            mode="overwrite", chara_path=str(path)))

        assert json.loads(path.read_text())[0]["chord"] == "old"

        sender.send_notification("the", ["t h e"])
        assert json.loads(path.read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 1}]

    def test_load_merges_with_baseline(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps(
            [{"triggers": ["t h e"], "chord": "the", "count": 5}]))
        sender = make_sender(make_config(mode="load", chara_path=str(path)))
        sender.send_notification("the", ["t h e"])

        assert json.loads(path.read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 6}]

    def test_load_adds_new_entries_to_baseline(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps(
            [{"triggers": ["old"], "chord": "old", "count": 5}]))
        sender = make_sender(make_config(mode="load", chara_path=str(path)))
        sender.send_notification("new", ["new"])

        data = {e["chord"]: e for e in json.loads(path.read_text())}
        assert data["old"]["count"] == 5
        assert data["new"]["count"] == 1

    def test_load_missing_file_starts_fresh(self, tmp_path):
        path = tmp_path / "chords.json"
        sender = make_sender(make_config(mode="load", chara_path=str(path)))
        sender.send_notification("the", ["t h e"])
        assert json.loads(path.read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 1}]

    def test_load_corrupt_file_starts_fresh(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text("not valid json")
        sender = make_sender(make_config(mode="load", chara_path=str(path)))
        sender.send_notification("the", ["t h e"])
        assert json.loads(path.read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 1}]

    def test_increment_uses_free_name(self, tmp_path):
        path = tmp_path / "chords.json"
        make_sender(make_config(mode="increment", chara_path=str(path))
                    ).send_notification("the", ["t h e"])
        assert path.exists()

    def test_increment_avoids_collision(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text("[]")
        make_sender(make_config(mode="increment", chara_path=str(path))
                    ).send_notification("the", ["t h e"])

        assert path.read_text() == "[]"
        assert json.loads((tmp_path / "chords_1.json").read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 1}]

    def test_increment_chain_of_collisions(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text("[]")
        (tmp_path / "chords_1.json").write_text("[]")
        make_sender(make_config(mode="increment", chara_path=str(path))
                    ).send_notification("the", ["t h e"])
        assert (tmp_path / "chords_2.json").exists()

    def test_increment_does_not_load_baseline(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps(
            [{"triggers": ["old"], "chord": "old", "count": 5}]))
        make_sender(make_config(mode="increment", chara_path=str(path))
                    ).send_notification("the", ["t h e"])
        assert json.loads((tmp_path / "chords_1.json").read_text()) == [
            {"triggers": ["t h e"], "chord": "the", "count": 1}]


class TestCountsAndOutput:
    def test_repeated_misses_increment_count(self, tmp_path):
        path = tmp_path / "chords.json"
        sender = make_sender(make_config(chara_path=str(path)))
        sender.send_notification("the", ["t h e"])
        sender.send_notification("the", ["t h e"])
        assert json.loads(path.read_text())[0]["count"] == 2

    def test_same_triggers_different_order_merge(self, tmp_path):
        path = tmp_path / "chords.json"
        sender = make_sender(make_config(chara_path=str(path)))
        sender.send_notification("the", ["t", "h e"])
        sender.send_notification("the", ["h e", "t"])
        assert json.loads(path.read_text()) == [
            {"triggers": ["h e", "t"], "chord": "the", "count": 2}]

    def test_filtered_miss_is_not_written(self, tmp_path):
        path = tmp_path / "chords.json"
        sender = make_sender(make_config(
            chara_path=str(path), blocked=["the"]))
        sender.send_notification("the", ["t h e"])
        assert not path.exists()

    def test_json_sorted_by_count_then_chord(self, tmp_path):
        path = tmp_path / "chords.json"
        sender = make_sender(make_config(chara_path=str(path)))
        sender.send_notification("bbb", ["bbb"])
        sender.send_notification("aaa", ["aaa"])
        sender.send_notification("bbb", ["bbb"])
        data = json.loads(path.read_text())
        assert [e["chord"] for e in data] == ["bbb", "aaa"]

    def test_log_to_path_stays_session_only(self, tmp_path):
        chord_path = tmp_path / "chords.json"
        chord_path.write_text(json.dumps(
            [{"triggers": ["t h e"], "chord": "the", "count": 5}]))
        log_path = tmp_path / "log.txt"
        sender = make_sender(make_config(
            mode="load", chara_path=str(chord_path),
            log_to_path=str(log_path), log_to_stdout=False))
        sender.send_notification("the", ["t h e"])

        assert log_path.read_text() == "['t h e'] = the 1\n"

    def test_json_written_without_log_options(self, tmp_path):
        path = tmp_path / "chords.json"
        sender = make_sender(make_config(
            chara_path=str(path), log_to_path="", log_to_stdout=False))
        sender.send_notification("the", ["t h e"])
        assert path.exists()


class TestLoadJsonCounts:
    def test_ignores_non_list_root(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps({"entries": []}))
        assert _load_json_counts(path) == {}

    def test_any_malformed_entry_discards_baseline(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps([
            {"triggers": ["a"], "chord": "x", "count": 2},
            {"triggers": "a", "chord": "x", "count": 2},
            {"chord": "x", "count": 2},
            "nonsense",
        ]))
        counts = _load_json_counts(path)
        assert counts == {}

    def test_bool_count_is_rejected(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps(
            [{"triggers": ["a"], "chord": "x", "count": True}]))
        assert _load_json_counts(path) == {}

    def test_loads_valid_entries(self, tmp_path):
        path = tmp_path / "chords.json"
        path.write_text(json.dumps([
            {"triggers": ["a"], "chord": "x", "count": 2},
            {"triggers": ["b"], "chord": "y", "count": 3},
        ]))
        counts = _load_json_counts(path)
        assert counts == {
            MissedKey.of("x", ["a"]): 2,
            MissedKey.of("y", ["b"]): 3,
        }

    def test_missing_file(self, tmp_path):
        assert _load_json_counts(tmp_path / "nope.json") == {}
