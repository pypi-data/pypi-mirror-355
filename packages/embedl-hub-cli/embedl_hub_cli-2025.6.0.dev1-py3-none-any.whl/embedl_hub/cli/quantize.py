# Copyright (C) 2025 Embedl AB

"""
embedl-hub quantize - send an onnx model to Qualcomm AI Hub and retrieve a quantized onnx model.
"""

from pathlib import Path

import typer

from embedl_hub.cli.init import read_embedl_hub_context
from embedl_hub.cli.utils import remove_none_values
from embedl_hub.core.config import load_default_config_with_size
from embedl_hub.core.hub_logging import console
from embedl_hub.core.quantization.quantization_config import QuantizationConfig
from embedl_hub.core.quantization.quantize import (
    QuantizationResult,
    quantize_model,
)

quantize_cli = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)


@quantize_cli.command()
def quantize(
    model: Path = typer.Option(
        None,
        "-m",
        "--model",
        help="Path to the ONNX model file to be quantized. (required)",
        show_default=False,
    ),
    data_path: str = typer.Option(
        None,
        "--data",
        "-d",
        help=(
            "Path to the dataset used for calibration. "
            "Supports a modified torchvision ImageFolder format. "
            "Use a single directory (e.g., /path/to/dataset) for a training-only set, "
            "or provide a structure with '/train' and '/val' subdirectories (e.g., /path/to/dataset/train and /path/to/dataset/val) "
            "to enable separate training and validation splits. "
            "Each subdirectory should contain one folder per class with corresponding images. "
            "If both train and val directories are provided, calibration will use the validation set. "
            "If no data path is provided, random data will be generated for calibration."
        ),
        show_default=False,
    ),
    output_file: Path = typer.Option(
        None,
        "-o",
        "--output-file",
        help="Destination path or directory to save the quantized model.",
        show_default=False,
    ),
    num_samples: int = typer.Option(
        None,
        "--num-samples",
        "-n",
        help="Number of data samples to use during quantization calibration.",
        show_default=False,
    ),
    size: str = typer.Option(
        None,
        "--size",
        help="Input size in format HEIGHT,WIDTH (e.g. 224,224).",
        show_default=False,
    ),
    config_path: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a YAML file with custom quantization tuning configuration.",
    ),
):
    """
    Quantize an ONNX model using Qualcomm AI Hub.

    Required arguments (if not provided through --config):
        --model

    Examples
    --------
    Quantize the ONNX model `exported_model.onnx` calibrating on data from `/path/to/dataset/` using 1000 samples from the dataset:

        $ embedl-hub quantize -m exported_model.onnx -d /path/to/dataset/ -n 1000

    Quantize the ONNX model using the configuration specified in `my_config.yaml`:

        $ embedl-hub quantize -c ./my_config.yaml

    """

    if not output_file:
        output_file = Path(model).with_suffix(".quantized.onnx")
        console.print(
            f"[yellow]No output file specified, using default: {output_file}[/]"
        )
    cfg = load_default_config_with_size(QuantizationConfig, size, "quantize")
    cli_flags = remove_none_values(
        {
            "model": model,
            "output_file": output_file,
            "num_samples": num_samples,
        }
    )
    # Data path is allowed to be None, so we don't remove it
    cli_flags.update(
        {
            "data_path": data_path,
        }
    )
    cfg = cfg.merge_yaml(other=config_path, **cli_flags)
    try:
        cfg.validate_config()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)

    ctx = read_embedl_hub_context()
    results: QuantizationResult = quantize_model(
        config=cfg,
        project_name=ctx["project_name"],
        experiment_name=ctx["experiment_name"],
    )
    console.print(f"[green]✓ Quantized model saved to {results.model_path}[/]")
