"""Tests for api.state.DataStore."""

from __future__ import annotations

from pathlib import Path

from api.state import DataStore


class TestEventCounts:
    """Tests for DataStore.event_counts aggregation."""

    def test_event_counts_match_label_frequencies(
        self, mock_signal_path: Path, mock_event_path: Path
    ) -> None:
        store = DataStore()
        store.source = "filesystem"
        store.data_level = "Files"
        store.data_paths = [str(mock_signal_path), str(mock_event_path)]
        store.load_data()

        assert store.all_wrappers, "expected at least one loaded session"
        wrapper = store.all_wrappers[0]
        expected = wrapper.get_dataframe()["label"].value_counts().to_dict()

        assert set(store.event_counts) == set(store.available_events)
        for label in store.available_events:
            assert store.event_counts[label] == expected.get(label, 0)

    def test_event_counts_empty_before_load(self) -> None:
        store = DataStore()
        assert store.event_counts == {}
