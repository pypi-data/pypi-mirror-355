#!/usr/bin/env python3

import argparse
import csv
import json
import logging
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional

import google.protobuf.duration_pb2
import grpc
import numpy as np
import soundfile
from phonexia.grpc.common.core_pb2 import Audio, RawAudioConfig, TimeRange
from phonexia.grpc.technologies.replay_attack_detection.experimental.replay_attack_detection_pb2 import (
    DetectRequest,
    DetectResponse,
)
from phonexia.grpc.technologies.replay_attack_detection.experimental.replay_attack_detection_pb2_grpc import (
    ReplayAttackDetectionStub,
)


def time_to_duration(time: float) -> Optional[google.protobuf.duration_pb2.Duration]:
    if time is None:
        return None
    duration = google.protobuf.duration_pb2.Duration()
    duration.seconds = int(time)
    duration.nanos = int((time - duration.seconds) * 1e9)
    return duration


def make_request(
    file: Path,
    start: Optional[float],
    end: Optional[float],
    use_raw_audio: bool,
) -> Iterator[DetectRequest]:
    time_range: Optional[TimeRange] = TimeRange(
        start=time_to_duration(start), end=time_to_duration(end)
    )
    chunk_size = 1024 * 100
    if use_raw_audio:
        with soundfile.SoundFile(file) as r:
            raw_audio_config: Optional[RawAudioConfig] = RawAudioConfig(
                channels=r.channels,
                sample_rate_hertz=r.samplerate,
                encoding=RawAudioConfig.AudioEncoding.PCM16,
            )
            for data in r.blocks(blocksize=r.samplerate, dtype="float32"):
                int16_info = np.iinfo(np.int16)
                data_scaled = np.clip(
                    data * (int16_info.max + 1), int16_info.min, int16_info.max
                ).astype("int16")
                yield DetectRequest(
                    audio=Audio(
                        content=data_scaled.flatten().tobytes(),
                        raw_audio_config=raw_audio_config,
                        time_range=time_range,
                    )
                )
                time_range = None
                raw_audio_config = None

    else:
        with open(file, mode="rb") as fd:
            while chunk := fd.read(chunk_size):
                yield DetectRequest(audio=Audio(content=chunk, time_range=time_range))
                time_range = None


def write_result(audio_path: str, response: DetectResponse, output_file: Optional[str] = None):
    with sys.stdout if output_file is None else open(output_file, "w") as f:
        logging.info(f"{audio_path!s} -> {output_file!s}")
        output = {
            "audio": str(audio_path),
            "total_billed_time": str(response.processed_audio_length.ToTimedelta()),
        }
        if response.HasField("result"):
            output["score"] = response.result.score
        json.dump(output, f, indent=2)


def detect(
    channel: grpc.Channel,
    file: Path,
    output_file: Optional[Path],
    start: Optional[float],
    end: Optional[float],
    metadata: Optional[list[Any]],
    use_raw_audio: bool,
):
    logging.info(f"Detecting replay attacks in {file}")
    stub = ReplayAttackDetectionStub(channel)
    response = stub.Detect(make_request(file, start, end, use_raw_audio), metadata=metadata)
    write_result(file, response, output_file)


# Main program
def check_file_exists(path: str) -> Path:
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist.")
    return Path(path)


def parse_list(path: Path) -> list[list[str]]:
    with open(path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=" ", skipinitialspace=True)
        rows = list(reader)

        for row in rows:
            num_cols = len(row)
            if num_cols < 1 or num_cols > 2:
                raise ValueError(
                    f"File '{path}' must contain one or two columns. Problematic row: '{row}'"
                )
            if num_cols == 1:
                row.append(str(Path(row[0]).with_suffix(".json")))

        return rows


def main():  # noqa: C901
    parser = argparse.ArgumentParser(description="Replay Attack Detection Client")
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost:8080",
        help="Server address, default: localhost:8080",
    )
    parser.add_argument(
        "-l",
        "--log_level",
        type=str,
        default="error",
        choices=["critical", "error", "warning", "info", "debug"],
    )
    parser.add_argument(
        "--metadata",
        metavar="key=value",
        nargs="+",
        type=lambda x: tuple(x.split("=")),
        help="Custom client metadata",
    )
    parser.add_argument("-i", "--input", type=check_file_exists, help="Input audio file")
    parser.add_argument("-o", "--output", type=Path, help="Output file path")
    parser.add_argument(
        "-L",
        "--list",
        type=check_file_exists,
        help="List of files and optional output locations (csv file, delimiter is space character ' ')",
    )
    parser.add_argument("--use_ssl", action="store_true", help="Use SSL connection")
    parser.add_argument("--start", type=float, default=None, help="Start time (seconds)")
    parser.add_argument("--end", type=float, default=None, help="End time (seconds)")
    parser.add_argument("--use_raw_audio", action="store_true", help="Send raw audio chunks")

    args = parser.parse_args()

    if not (args.input or args.list):
        raise ValueError("Either 'input' or 'list' parameter must be set.")

    if args.start is not None and args.start < 0:
        raise ValueError("Parameter 'start' must be a non-negative float.")

    if args.end is not None and args.end <= 0:
        raise ValueError("Parameter 'end' must be a positive float.")

    if args.start is not None and args.end is not None and args.start >= args.end:
        raise ValueError("Parameter 'end' must be larger than 'start'.")

    logging.basicConfig(
        level=args.log_level.upper(),
        format="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        logging.info(f"Connecting to {args.host}")
        channel = (
            grpc.secure_channel(target=args.host, credentials=grpc.ssl_channel_credentials())
            if args.use_ssl
            else grpc.insecure_channel(target=args.host)
        )

        def execute(input_file: Path, output_file: Path) -> None:
            detect(
                channel,
                input_file,
                output_file,
                args.start,
                args.end,
                args.metadata,
                args.use_raw_audio,
            )

        if args.input is not None:
            execute(args.input, args.output)

        elif args.list is not None:
            for input_file, output_file in parse_list(args.list):
                execute(Path(input_file), Path(output_file))

    except grpc.RpcError:
        logging.exception("RPC failed")
        exit(1)
    except ValueError as e:
        logging.exception(e)  # noqa: TRY401
        exit(1)
    except Exception:
        logging.exception("Unknown error")
        exit(1)
    finally:
        channel.close()


if __name__ == "__main__":
    main()
