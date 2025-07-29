# Copyright (C) 2025 Embedl AB

"""
embedl-hub compile - send an ONNX model to Qualcomm AI Hub, retrieve a
device-specific binary (.tflite for tflite, .bin for qnn, or .onnx for onnxruntime).
"""

from pathlib import Path

import typer

from embedl_hub.core.compile import CompileError, CompileResult, compile_model
from embedl_hub.core.hardware.qualcomm_ai_hub import print_device_table
from embedl_hub.core.hub_logging import console

compile_cli = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)


@compile_cli.command()
def compile(
    model: Path = typer.Option(
        ...,
        "-m",
        "--model",
        help="Path to the ONNX model file to be compiled.",
        show_default=False,
    ),
    device: str = typer.Option(
        ...,
        "-d",
        "--device",
        help="Target device name for deployment. Use command `list-devices` to view all available options.",
        show_default=False,
    ),
    runtime: str = typer.Option(
        "tflite",
        "-r",
        "--runtime",
        help="Runtime backend for compilation: tflite, qnn, or onnx.",
    ),
    quantize_io: bool = typer.Option(
        False,
        "--quantize-io",
        help="Quantize input and output tensors. Improves performance on platforms that support quantized I/O.",
        show_default=True,
    ),
    output_file: str = typer.Option(
        None,
        "-o",
        "--output-file",
        help="Destination path or directory where the compiled model will be saved.",
        show_default=False,
    ),
):
    """
    Compile an ONNX model into a device ready binary using Qualcomm AI Hub.

    Required arguments:
        --model
        --device

    Examples
    --------
    Compile the ONNX model `int8_model.onnx` for the Samsung Galaxy S24 and runtime (tflite):

        $ embedl-hub compile -m int8_model.onnx -d "Samsung Galaxy S24"

    Compile the ONNX model `fp32_model.onnx` for the Samsung Galaxy S24 using the tflite runtime:

        $ embedl-hub compile -m fp32_model.onnx -d "Samsung Galaxy S24" -r tflite

    Compile the ONNX model `model.onnx` for the Samsung Galaxy S24 and save the output to `./my_outputs/model.tflite`:

        $ embedl-hub compile -m model.onnx -d "Samsung Galaxy S24" -o ./my_outputs/model.tflite

    """

    try:
        res: CompileResult = compile_model(
            model_file=model,
            device=device,
            runtime=runtime,
            quantize_io=quantize_io,
            output_file=output_file,
        )
        console.print(f"[green]✓ Compiled model for {res.device}[/]")

        # TODO: upload artefacts / metrics to web
    except (CompileError, ValueError) as error:
        console.print(f"[red]✗ {error}[/]")
        raise typer.Exit(1)
