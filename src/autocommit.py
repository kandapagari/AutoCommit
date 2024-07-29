#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import click
import dotenv
from langchain.chains import LLMChain
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
from rich import print

from src.utils import coro

_ = dotenv.load_dotenv(dotenv.find_dotenv())
# openai.api_key = os.environ["OPENAI_API_KEY"]
server_url = os.environ["SERVER_URL"]
llm = Ollama(base_url=server_url, model='llama3:latest')

DIFF_PROMPT = "Generate a succinct summary of the following code changes:"
COMMIT_MSG_PROMPT = (
    "Using no more than 50 characters, "
    "generate a descriptive commit message from these summaries:"
)
PROMPT_CUTOFF = 10000


def get_diff(ignore_whitespace: bool = True) -> str:
    """Executes a git command to get the diff of staged changes, with options
    to ignore whitespace changes.

    This function runs a git diff command on staged files. It can be configured to ignore all
    whitespace and blank lines in the diff output. The function captures and returns the standard
    output from the git command, which contains the diff of staged changes.

    Args:
        ignore_whitespace (bool): If True, the git diff command will ignore all spaces and blank
                                    lines. Defaults to True.

    Returns:
        str: The diff output of staged changes as a string, stripped of leading and trailing
                whitespace.

    Example:
        >>> get_diff()
        'diff --git a/file.txt b/file.txt\nindex 83db48f..563b55a 100644\n---\
            a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-Hello World\n+Hello, World!'

        >>> get_diff(ignore_whitespace=False)
        'diff --git a/file.txt b/file.txt\nindex 83db48f..563b55a 100644\n---\
            a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-Hello World\n+Hello, World!'

    Note:
        This function requires the `subprocess` module for executing the git command and capturing
        its output. Ensure that git is installed and accessible from the command line where this
        script is executed. The function assumes that git is configured and that there are staged
        changes to diff.
    """
    args = [
        "git",
        "--no-pager",
        "diff",
        "--staged"
    ]
    if ignore_whitespace:
        args.extend(["--ignore-all-space", "--ignore-blank-lines"])
    diff_process = subprocess.run(args, capture_output=True, text=True)
    diff_process.check_returncode()
    return diff_process.stdout.strip()


def parse_diff(diff: str) -> list:
    """Parses a git diff output string into a list of file diffs, each
    represented as a tuple containing the file header and a list of its chunk
    diffs.

    This function takes the output of a git diff command as input and separates it into individual
    file diffs. Each file diff is then further divided into its header (containing information like
    the file names and indices) and its content chunks (each representing a change block in the
    file). The content chunks are reversed to maintain their original order in the diff.

    Args:
        diff (str): The full git diff output as a single string.

    Returns:
        list: A list where each element is a tuple. The first element of the tuple is a string
              representing the header of a file's diff. The second element is a list of strings,
              each representing a reversed chunk of changes for that file.

    Example:
        >>> diff_output = '''diff --git a/file1.txt b/file1.txt\\nindex 83db48f..563b55a \
            100644\\n--- a/file1.txt\\n+++ b/file1.txt\\n@@ -1 +1 @@\\n-Hello World\\n+Hello,\
            World!\\ndiff --git a/file2.txt b/file2.txt\\nindex 73db48f..463b55a \
            100644\\n--- a/file2.txt\\n+++ b/file2.txt\\n@@ -1 +1 @@\\n-Goodbye\\n+Goodbye!'''
        >>> parse_diff(diff_output)
        [('diff --git a/file1.txt b/file1.txt\\nindex 83db48f..563b55a 100644\\n--- \
            a/file1.txt\\n+++ b/file1.txt', ['\\n@@ -1 +1 @@\\n-Hello World\\n+Hello,\
            World!']), ('diff --git a/file2. b/file2.txt\\nindex 73db48f..463b55a \
                100644\\n--- a/file2.txt\\n+++ b/file2.txt',\
                    ['\\n@@ -1 +1 @@\\n-Goodbye\\n+Goodbye!'])]

    Note:
        The function assumes the input diff string is well-formed and directly output from a
        git diff command. It might not handle edge cases or malformed input gracefully.
    """
    file_diffs = diff.split("\ndiff")
    file_diffs = [file_diffs[0]] + [
        "\ndiff" + file_diff for file_diff in file_diffs[1:]
    ]
    chunked_file_diffs = []
    for file_diff in file_diffs:
        [head, *chunks] = file_diff.split("\n@@")
        chunks = ["\n@@" + chunk for chunk in reversed(chunks)]
        chunked_file_diffs.append((head, chunks))
    return chunked_file_diffs


def assemble_diffs(parsed_diffs: list, cutoff: int) -> list:
    """Assembles parsed git diffs into multiple strings, each not exceeding a
    specified character cutoff.

    This function takes a list of parsed diffs (as produced by `parse_diff`) and a character limit
    (cutoff). It aims to reassemble these diffs into a series of strings, where each string
    represents part of the diff and does not exceed the specified cutoff length. This is useful for
    scenarios where diffs need to be displayed or processed in chunks due to size constraints.

    Args:
        parsed_diffs (list): A list of tuples, each representing a parsed file diff. The first
                    element of each tuple is the header of the file diff, and the second element
                    is a list of chunk strings representing the content changes.
        cutoff (int): The maximum length allowed for each assembled diff string.

    Returns:
        list: A list of strings, each representing a segment of the diff that is within the cutoff
            length. Segments are formatted to maintain readability, with new segments starting with
            the file header if the previous segment was cut off in the middle of a file's diff.

    Example:
        >>> parsed_diffs = [('diff --git a/file1.txt b/file1.txt', ['\\n@@ -1 +1 @@\\n-Hello\
            \\\n+Hello, World!']), ('diff --git a/file2.txt b/file2.txt', ['\\n@@ -1 +1 @@\\n\
                -Goodbye\\n+Goodbye!'])]
        >>> assemble_diffs(parsed_diffs, 100)
        ['diff --git a/file1.txt b/file1.txt\\n\\n@@ -1 +1 @@\\n-Hello\\n+Hello, World!',\
            'diff --git a/file2.txt b/file2.txt\\n\\n@@ -1 +1 @@\\n-Goodbye\\n+Goodbye!']

    Note:
        This function does not validate the structure of `parsed_diffs` against a specific schema.
        It assumes that `parsed_diffs` is structured correctly as per the output of `parse_diff`.
        Mis-structured input may lead to unexpected output or errors.
    """
    assembled_diffs = [""]

    def add_chunk(chunk: str) -> bool:
        """Attempts to add a diff chunk to the latest string in the assembled
        diffs list without exceeding the cutoff.

        Args:
            chunk (str): A string representing a chunk of the diff to be added.

        Returns:
            bool: True if the chunk was added without creating a new string, False if a new string
                  was started to accommodate the chunk.
        """
        if len(assembled_diffs[-1]) + len(chunk) <= cutoff:
            assembled_diffs[-1] += "\n" + chunk
            return True
        else:
            assembled_diffs.append(chunk)
            return False

    for head, chunks in parsed_diffs:
        if not chunks:
            add_chunk(head)
        else:
            add_chunk(head + chunks.pop())
        while chunks:
            if not add_chunk(chunks.pop()):
                assembled_diffs[-1] = head + assembled_diffs[-1]
    return assembled_diffs


async def complete(prompt: str, guild_lines: str | Path | None = None) -> str:
    """Asynchronously invokes an OpenAI model to complete a given prompt, with
    an optional context from guild lines.

    This function takes a prompt and optionally a context provided by guild lines, which can be a
    string or a path to a file containing such lines. It then interacts with an OpenAI model to
    generate a completion for the prompt. The function is designed to be asynchronous, suitable for
    applications that require non-blocking operations.

    Args:
        prompt (str): The initial text to which the model should generate a completion.
        guild_lines (str | Path): Additional context to provide to the model before the prompt.
                                This can be either a string directly containing the guild lines,
                                or a path to a file where such lines are stored. Defaults to None.

    Returns:
        str: The content generated by the model as a completion to the input prompt.

    Example:
        >>> asyncio.run(complete("What's the weather like in Paris today?"))
        'The weather in Paris today is sunny with a high of 75°F and a low of 56°F.'
    """
    model = LLMChain(prompt=prompt, llm=llm)
    # model = ChatOpenAI(temperature=0, max_tokens=128, model="gpt-4")
    messages = [SystemMessage(content=str(guild_lines)),
                HumanMessage(content=prompt[: PROMPT_CUTOFF + 100])]
    completion = model.invoke(messages)
    return str(completion.content)


async def summarize_diff(diff: str, guild_lines: str) -> str:
    assert diff
    prompt = f"{DIFF_PROMPT}\n\n{diff}\n\n"
    return await complete(prompt, guild_lines)


async def summarize_summaries(summaries, guild_lines) -> str:
    assert summaries
    prompt = f"{COMMIT_MSG_PROMPT}\n\n{summaries}\n\n"
    return await complete(prompt, guild_lines)


async def generate_commit_message(diff, guild_lines) -> str:
    if not diff:
        return "style: Fix whitespace"

    assembled_diffs = assemble_diffs(parse_diff(diff), PROMPT_CUTOFF)
    summaries: list = await asyncio.gather(
        *[summarize_diff(diff, guild_lines) for diff in assembled_diffs]
    )
    return await summarize_summaries("\n".join(summaries), guild_lines)


def commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message, "--edit"]).returncode


def load_commit_guildlines(guild_path: str | Path | None = None):
    if guild_path is None:
        guild_path = Path(
            f'{__file__}/../commit-message-guidelines.md').resolve()
    loader = UnstructuredMarkdownLoader(str(guild_path))
    return loader.load()[0].page_content


@click.command(help=(
    "Generate a commit message for staged files and commit them. "
    "Git will prompt you to edit the generated commit message."
))
@click.option("-p", '--print-message', is_flag=True,
              help="print message in place of performing commit")
@click.option("-g", '--guild-path', type=click.Path(exists=True, dir_okay=False), required=False,
              help='path to commit guildlines markdown file')
@coro
async def main(print_message: bool = False, guild_path: str | Path | None = None):
    try:
        guild_lines = load_commit_guildlines(guild_path)
        if not get_diff(ignore_whitespace=False):
            print(
                "No changes staged. Use 'git add' to stage files before invoking AutoCommit."
            )
            exit()
        commit_message = await generate_commit_message(get_diff(), guild_lines)
    except UnicodeDecodeError:
        print("codecomit does not support binary files", file=sys.stderr)
        commit_message = (
            "# codecomit does not support binary files. "
            "Please enter a commit message manually or unstage any binary files."
        )

    if print_message:
        print(commit_message)
    else:
        exit(commit(commit_message.replace('`', '')))


if __name__ == "__main__":
    asyncio.run(main())
