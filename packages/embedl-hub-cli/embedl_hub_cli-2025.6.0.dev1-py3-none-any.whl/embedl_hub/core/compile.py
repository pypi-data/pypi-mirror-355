# Copyright (C) 2025 Embedl AB
"""
Core compile logic for the embedl-hub CLI.

Handles submitting models to Qualcomm AI Hub for compilation and saving the resulting artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import qai_hub as hub


class CompileError(RuntimeError):
    """Raised when Qualcomm AI Hub compile job fails or times out."""


@dataclass
class CompileResult:
    model_path: Path  # local .tflite, .bin, or .onnx after compile
    job_id: str
    device: str


def compile_model(
    model_file: Path | str,
    device: str,
    runtime: str = "tflite",
    quantize_io: bool = False,
    output_file: Path | str = None,
    image_size: tuple[int, int] | None = None,
) -> CompileResult:
    """
    Submit an ONNX model to Qualcomm AI Hub and retrieve the compiled artifact.

    Args:
        model_file: Path to ONNX (INT8 or FP32).
        device: Device nickname, e.g. 'Samsung Galaxy S24'.
        runtime: 'tflite' | 'qnn' | 'onnx'
        quantize_io: Add --quantize_io to options.
        output_file: Compiled model filename. File ending added automatically if not specified.
        image_size: Input image size as (height, width) tuple, e.g. (224, 224).

    Returns:
        CompileResult with local path to compiled model.

    """
    model_file = Path(model_file)
    if not model_file.exists():
        raise ValueError(f"Model not found: {model_file}")

    try:
        hub_device = hub.Device(device)
    except Exception as error:
        raise ValueError(
            f"Device '{device}' not recognized. "
            "Run  embedl-hub compile --list-devices  to see valid names."
        ) from error

    opts = f"--target_runtime {runtime}"
    if quantize_io:
        opts += " --quantize_io"

    input_specs = {"image": (1, 3, *image_size)} if image_size else None

    try:
        job = hub.submit_compile_job(
            model=model_file.as_posix(),
            device=hub_device,
            options=opts,
            input_specs=input_specs,
        )
    except Exception as error:
        raise CompileError("Failed to submit compile job.") from error

    try:
        compiled_model = job.get_target_model()
    except Exception as error:
        raise CompileError(
            "Failed to download compiled model from Qualcomm AI Hub."
        ) from error
    local_path = _save_compiled_model(compiled_model, output_file)

    return CompileResult(
        model_path=local_path,
        job_id=job.job_id,
        device=device,
    )


def _save_compiled_model(
    compiled: "hub.Model", output_file: Path | str = None
) -> Path:
    """
    Save the compiled artifact to a user-specified location or to the root
    directory with the name provided by Qualcomm AI Hub.

    Returns:
        Path to the saved model file.
    """
    model_filename = Path(compiled.name)
    if output_file is None:
        dst = Path.cwd() / model_filename
    else:
        output_path = Path(output_file)
        if output_path.is_dir() or str(output_file).endswith(("/", "\\")):
            dst = output_path / model_filename
        else:
            dst = output_path

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst = compiled.download(dst)
    return dst
