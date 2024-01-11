#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: luo

import os
import re
import tempfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import docker
from docker.errors import DockerException, ImageNotFound, NotFound
from docker.models.containers import Container as DockerContainer

from kwaiagents.tools.base import BaseTool, BaseResult


class CommandExecutionError(Exception):
    """Base class for specific exceptions relevant in the execution of Agents"""
    message: str

    hint: Optional[str] = None
    """A hint which can be passed to the LLM to reduce reoccurrence of this error"""

    def __init__(self, message: str, *args):
        self.message = message
        super().__init__(message, *args)


class InvalidArgumentError(CommandExecutionError):
    """The command received an invalid argument"""


class CodeExecutionError(CommandExecutionError):
    """The operation (an attempt to run arbitrary code) returned an error"""


def find_first_non_empty_index(lst):
    for i, item in enumerate(lst):
        if item:
            return i
    return -1  # 如果列表中所有元素都为空，则返回-1


def extract_code(text):
    # Match triple backtick blocks first
    triple_match = re.search(r'```[^\n]*\n(.+?)```', text, re.DOTALL)
    if triple_match:
        text = triple_match.group(1)
    else:
        print(text)
        # try:
        #     text = json5.loads(text)['code']
        # except Exception:
        #     print(''.join(traceback.format_exception(*sys.exc_info())))
    # If no code blocks found, return original text
    lines = text.splitlines()
    last_line = lines[-1]
    if "print" not in last_line:
        new_last_line = last_line[:find_first_non_empty_index(last_line)] + f"print({last_line})"
        lines[-1] = new_last_line
    return "\n".join(lines)


def execute_python_file(
        workspace: str,
        filename: str
) -> str:
    """Execute a Python file in a Docker container and return the output

    Args:
        workspace (Path): The workspace to execute
        filename (Path): The name of the file to execute

    Returns:
        str: The output of the file
    """
    print(
        f"Executing python file '{filename}' "
        f"in working directory '{workspace}'"
    )

    if not str(filename).endswith(".py"):
        raise InvalidArgumentError("Invalid file type. Only .py files are allowed.")

    file_path = Path(filename)
    if not file_path.is_file():
        # Mimic the response that you get from the command line to make it
        # intuitively understandable for the LLM
        raise FileNotFoundError(
            f"python: can't open file '{filename}': [Errno 2] No such file or directory"
        )

    print("Running in a Docker container")
    try:

        client = docker.from_env()
        # You can replace this with the desired Python image/version
        # You can find available Python images on Docker Hub:
        # https://hub.docker.com/_/python
        image_name = "python:3-alpine"
        container_is_fresh = False
        container_name = "code_interpreter_sandbox"
        try:
            container: DockerContainer = client.containers.get(
                container_name
            )  # type: ignore
        except NotFound:
            try:
                client.images.get(image_name)
                print(f"Image '{image_name}' found locally")
            except ImageNotFound:
                print(
                    f"Image '{image_name}' not found locally,"
                    " pulling from Docker Hub..."
                )
                # Use the low-level API to stream the pull response
                low_level_client = docker.APIClient()
                for line in low_level_client.pull(image_name, stream=True, decode=True):
                    # Print the status and progress, if available
                    status = line.get("status")
                    progress = line.get("progress")
                    if status and progress:
                        print(f"{status}: {progress}")
                    elif status:
                        print(status)

            print(f"Creating new {image_name} container...")
            container: DockerContainer = client.containers.run(
                image_name,
                ["sleep", "60"],  # Max 60 seconds to prevent permanent hangs
                volumes={
                    str(workspace): {
                        "bind": "/workspace",
                        "mode": "rw",
                    }
                },
                working_dir="/workspace",
                stderr=True,
                stdout=True,
                detach=True,
                name=container_name,
            )  # type: ignore
            container_is_fresh = True

        if not container.status == "running":
            container.start()
        elif not container_is_fresh:
            container.restart()

        print(f"Running {file_path} in container {container.name}...")
        exec_result = container.exec_run(
            [
                "python",
                "-B",
                file_path.relative_to(workspace).as_posix(),
            ],
            stderr=True,
            stdout=True,
        )

        if exec_result.exit_code != 0:
            raise CodeExecutionError(exec_result.output.decode("utf-8"))

        return exec_result.output.decode("utf-8")

    except DockerException as e:
        print(
            "Could not run the script in a container. "
            "If you haven't already, please install Docker: "
            "https://docs.docker.com/get-docker/"
        )
        raise CommandExecutionError(f"Could not run the script in a container: {e}")


class CodeInterpreterResult(BaseResult):
    @property
    def answer(self):
        return self.json_data


class CodeInterpreterTool(BaseTool):
    """
    Execute a Python code in a Docker container

    Args:
        code (str): The Python code to run.

    Returns:
         str: The STDOUT captured from the code when it ran.
    """
    name = "code_interpreter"
    zh_name = "代码解释器"
    description = 'Code Interpreter:"code_interpreter", args:"code": "<str: the python code, required>"'
    tips = ""

    def __init__(
            self,
            lang="wt-wt",
            max_retry_times=5,
            *args,
            **kwargs,
    ):
        self.max_retry_times = max_retry_times
        self.lang = lang

    def run_code_interpreter(self, code: str) -> str:

        code = extract_code(code)
        workspace = os.path.join(tempfile.gettempdir(), "workspace")
        if not os.path.exists(workspace):
            os.mkdir(workspace)
        tmp_code_file = NamedTemporaryFile(
            "w", dir=workspace, suffix=".py", encoding="utf-8", delete=False
        )
        tmp_code_file.write(code)
        tmp_code_file.flush()

        try:
            return execute_python_file(workspace, tmp_code_file.name)
        except Exception as e:
            return f"Code execute error: {e}"
        finally:
            tmp_code_file.close()

    def __call__(self, code, *args, **kwargs):
        result = self.run_code_interpreter(code=code)
        return CodeInterpreterResult(result)
