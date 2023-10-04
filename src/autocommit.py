#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import click
import dotenv
import openai
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.schema import HumanMessage, SystemMessage
from rich import print

from utils import coro

_ = dotenv.load_dotenv(dotenv.find_dotenv())
openai.api_key = os.environ["OPENAI_API_KEY"]

DIFF_PROMPT = "Generate a succinct summary of the following code changes:"
COMMIT_MSG_PROMPT = (
    "Using no more than 50 characters, "
    "generate a descriptive commit message from these summaries:"
)
PROMPT_CUTOFF = 10000


def get_diff(ignore_whitespace: bool = True) -> str:
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


def parse_diff(diff: str) -> tuple[str, str]:
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


def assemble_diffs(parsed_diffs, cutoff):
    """Create multiple well-formatted diff strings, each being shorter than
    cutoff."""
    assembled_diffs = [""]

    def add_chunk(chunk):
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


async def complete(prompt, guild_lines: str | Path | None = None):
    model = ChatOpenAI(temperature=0, max_tokens=128, model="gpt-4")
    messages = [SystemMessage(content=guild_lines),
                HumanMessage(content=prompt[: PROMPT_CUTOFF + 100])]
    completion = model(messages)
    return completion.content


async def summarize_diff(diff, guild_lines):
    assert diff
    return await complete(DIFF_PROMPT + "\n\n" + diff + "\n\n", guild_lines)


async def summarize_summaries(summaries, guild_lines):
    assert summaries
    return await complete(COMMIT_MSG_PROMPT + "\n\n" + summaries + "\n\n", guild_lines)


async def generate_commit_message(diff, guild_lines):
    if not diff:
        return "style: Fix whitespace"

    assembled_diffs = assemble_diffs(parse_diff(diff), PROMPT_CUTOFF)
    summaries = await asyncio.gather(
        *[summarize_diff(diff, guild_lines) for diff in assembled_diffs]
    )
    return await summarize_summaries("\n".join(summaries), guild_lines)


def commit(message):
    # will ignore message if diff is empty
    return subprocess.run(["git", "commit", "--message", message, "--edit"]).returncode


def load_commit_guildlines(guild_path: str | Path | None = None):
    if guild_path is None:
        guild_path = Path(f'{__file__}/../src/commit-message-guidelines.md').resolve()
    loader = UnstructuredMarkdownLoader(guild_path)
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
