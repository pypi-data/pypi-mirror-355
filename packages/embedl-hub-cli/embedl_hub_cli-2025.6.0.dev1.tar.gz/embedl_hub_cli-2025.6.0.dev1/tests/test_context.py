# Copyright (C) 2025 Embedl AB


import logging

import pytest

from embedl_hub.core.context import RunType, experiment_context


def test_experiment_context_logs(caplog):
    """Test that the experiment_context logs the correct messages."""

    # Capture INFO-level logs
    caplog.set_level(logging.INFO)

    with experiment_context(RunType.TUNE):
        pass

    # Extract just the log messages
    messages = [record.getMessage() for record in caplog.records]

    # Check that both messages appeared
    assert "Running command with project-id: 313" in messages
    assert "Running command with experiment-id: 1337" in messages


if __name__ == "__main__":
    pytest.main([__file__])
