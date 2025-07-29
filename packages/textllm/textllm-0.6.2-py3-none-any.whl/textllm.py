#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import base64
import itertools
import json
import logging
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime
from functools import cached_property
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv  # pip install python-dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    merge_message_runs,
)

__version__ = "0.6.2"

log = logging.getLogger("textllm")

AUTO_TITLE = "!!AUTO TITLE!!"
TEMPLATE = """\
# {AUTO_TITLE}

```toml
# Optional Settings
temperature = {temperature}
model = {model!r}
```

Created with {version} at {now} 

--- System ---  

You are an expert assistant. Provide concise, accurate answers.

--- User ---  

"""


# Environment variable configs for defaults
class _DYNAMIC_ENV_CONFIG:
    @property
    def TEXTLLM_ENV_PATH(self):
        return os.environ.get("TEXTLLM_ENV_PATH", None)

    @property
    def TEXTLLM_EDITOR(self):
        return os.environ.get("TEXTLLM_EDITOR", os.environ.get("EDITOR", "vi"))

    @property
    def TEXTLLM_DEFAULT_MODEL(self):
        return os.environ.get("TEXTLLM_DEFAULT_MODEL", "openai:gpt-4o")

    @property
    def TEXTLLM_DEFAULT_TEMPERATURE(self):
        return float(os.environ.get("TEXTLLM_DEFAULT_TEMPERATURE", 0.5))

    @property
    def TEXTLLM_TEMPLATE_FILE(self):
        return os.environ.get("TEXTLLM_TEMPLATE_FILE", None)

    @property
    def TEMPLATE(self):
        return TEMPLATE.format(
            AUTO_TITLE=AUTO_TITLE,
            temperature=float(self.TEXTLLM_DEFAULT_TEMPERATURE),
            model=self.TEXTLLM_DEFAULT_MODEL,
            now=datetime.now().astimezone().isoformat(),
            version=f"textllm-{__version__}",
        )


CONFIG = _DYNAMIC_ENV_CONFIG()


TITLE_SYSTEM_PROMPT = """\
Provide an appropriate, consice, title for this conversation. The conversation is in JSON form with roles 'system' (or 'developer'), 'human', and 'ai'.

- Aim for fewer than 5 words but absolutely no more than 10.
- Be as concise as possible without losing the context of the conversation.
- Your goal is to extract the key point and intent of the conversation
- Make sure the title is also appropriate for a filename. Spaces are acceptable.
- Reply with ONLY the title and nothing else!
"""

MAX_FILENAME_CHAR = 240

FLAG2ROLE = {
    "--- system ---": SystemMessage,
    "--- user ---": HumanMessage,
    "--- assistant ---": AIMessage,
}

CONVO_PATTERN = re.compile(
    "(" + "|".join("^" + re.escape(flag) for flag in FLAG2ROLE) + ")",
    flags=re.DOTALL | re.MULTILINE | re.IGNORECASE,
)

DEFAULT_FILEPATH = "New Conversation.md"

TEST_MODE = False


class Conversation:
    def __init__(self, filepath):
        self.filepath = self.filepath0 = filepath

        # Read and truncate file
        with open(self.filepath, "rt") as fp:
            self.text = fp.read().rstrip()

        self.parsed = loads(self.text)
        self.messages = self.process_conversation()

    def call_llm(self, messages, stream_model=False, **new_settings):
        settings = self.settings.copy() | new_settings
        log.debug(f"Settings {settings}")

        model = settings.pop("model")  # Will KeyError if not set as expected
        try:
            model_provider, model_name = model.split(":", 1)
        except ValueError:
            model_provider = None
            model_name = model
            log.debug(f"{model!r} does not contain a provider. Will try to infer")

        log.debug(f"{model_provider = } {model_name = }")

        chat_model = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            **settings,
        )

        if stream_model:
            try:
                stream = chat_model.stream(messages, stream_usage=True)
                chunk = response = next(stream)
            except:
                stream = chat_model.stream(messages)
                chunk = response = next(stream)

            print("\n" + chunk.content, end="", flush=True)
            for chunk in stream:
                response += chunk
                print(chunk.content, end="", flush=True)
            print("\n\n", end="", flush=True)
        else:
            response = chat_model.invoke(messages)

        try:
            logtxt = (
                f"tokens: "
                f"prompt {response.usage_metadata['input_tokens']}, "
                f"completion {response.usage_metadata['output_tokens']}, "
                f"total {response.usage_metadata['total_tokens']}"
            )
            log.debug(logtxt)
        except:
            # The above seems to only work well with OpenAI.
            # ToDO: Fix this
            pass

        return response

    def chat(self, require_user_prompt=True, stream_model=False):
        if require_user_prompt and (
            not self.messages or not isinstance(self.messages[-1], HumanMessage)
        ):
            raise NoHumanMessageError("Must have a new user message")

        response = self.call_llm(messages=self.messages, stream_model=stream_model)

        # Not really needed but in case I do more with it later
        self.messages.append(response)

        # Add escapes to flags in the content
        content = response.content
        content = CONVO_PATTERN.sub(r"\\\1", content)

        with open(self.filepath, "r+") as file:
            # Move to the last non-white space up to 100
            # characters
            file.seek(0, 2)  # Move to the end of the file
            file_length = file.tell()

            MX = 100
            for _ in range(MX):
                if file_length == 0:
                    break
                file.seek(file_length - 1)
                if not file.read(1).isspace():
                    file.seek(file_length)  # Move forward character
                    break
                file_length -= 1

            else:
                log.debug(
                    f"Did not find a non-whitespace character within the last {MX} "
                    "characters."
                )
            file.write("\n\n--- Assistant ---  \n\n")
            file.write(content)
            file.write("\n\n--- User ---  \n\n")

            log.info(f"Updated {self.filepath!r}")

    def set_title(self):
        top, rest = self.text.split("\n", 1)
        if AUTO_TITLE not in top:
            log.debug(f"{AUTO_TITLE!r} not found in first line.")
            return  # This will happen nearly every time but the first

        new = [
            SystemMessage(content=TITLE_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(self.parsed["conversation"])),
        ]

        if TEST_MODE:  # For testing, I don't want to provide this
            del new[1]

        response = self.call_llm(messages=new, **self.settings)
        title = response.content

        top = top.replace(AUTO_TITLE, title)
        self.text = f"{top}\n{rest}"
        with open(self.filepath, "wt") as fp:
            fp.write(self.text)
        log.info(f"Set title to {title!r}")

    @cached_property
    def settings(self):
        defaults = Conversation.read_settings(CONFIG.TEMPLATE)
        return defaults | self.parsed["settings"]

    @staticmethod
    def read_settings(text):
        pattern = re.compile(
            r"""
                ^```          # Start of line with fenced code block
                \s*           # Optional whitespace
                (?:toml)?     # Optional designation as TOML
                \s*$          # Optional whitespace to end of line
                \n            # At least one new line
                (.*?)         # Actual TOML code (non-greedy)
                \n            # New line before closing fence
                ^```          # Closing fence on its own line
                \s*$          # Optional whitespace to end of line
            """,
            flags=re.VERBOSE | re.DOTALL | re.MULTILINE | re.IGNORECASE,
        )

        if match := pattern.search(text):  # First one only
            toml_content = match.group(1).strip()
            return tomllib.loads(toml_content)

        return {}

    @staticmethod
    def loads(text):
        res = {}

        split_text = CONVO_PATTERN.split(text)

        # Split will split at the flags. If the first item is a flag, then there is no
        # top matter. If it isn't a flag, the first item is top matter.
        if split_text[0].lower() not in FLAG2ROLE:
            top = split_text.pop(0)
        else:
            top = ""

        res["title"] = top.split("\n")[0].strip().strip("#").strip()
        res["settings"] = Conversation.read_settings(top)
        res["top"] = top

        re_role = re.compile("--- (.*) ---")
        res["conversation"] = conversation = []
        for flag, msg in grouper(split_text, 2):
            msg = msg.strip()
            if not msg:
                continue  # Empty or blank

            # Clean up and unescape
            msg_lines = []
            for line in msg.strip().split("\n"):
                if any(line.lower().startswith(rf"\{flag}") for flag in FLAG2ROLE):
                    line = line[1:]
                msg_lines.append(line)

            role = re_role.findall(flag)[0].lower()  # Must be a flag from initial split
            content = "\n".join(msg_lines)

            conversation.append({"role": role, "content": content})

        return res

    def process_conversation(self):
        conversation = []
        for item in self.parsed["conversation"]:
            flag = f"--- {item['role']} ---"
            msg = item["content"]

            # Clean up and unescape
            msg_lines = []
            for line in msg.strip().split("\n"):
                if any(line.lower().startswith(rf"\{flag}") for flag in FLAG2ROLE):
                    line = line[1:]
                msg_lines.append(line)

            msg, img_urls = process_msg_for_images(msg_lines)

            content = [{"type": "text", "text": msg}]
            for img_url in img_urls:
                item = {"type": "image_url"}
                if re.match("https?://.*", img_url, flags=re.IGNORECASE):
                    item["image_url"] = {"url": img_url}
                    log.debug(f"Found image with URL: {img_url!r}")
                elif img_url.lower().startswith("data:"):
                    item["image_url"] = {"url": img_url}
                    log.debug(f"Found 'data:<...>' URL")
                else:
                    # Need to load it relative to the file
                    img_path = os.path.join(os.path.dirname(self.filepath), img_url)
                    mime_type, _ = mimetypes.guess_type(img_path)
                    with open(img_path, "rb") as fp:
                        data = fp.read()
                        img_data = base64.b64encode(data).decode("utf-8")
                        item["image_url"] = {
                            "url": f"data:{mime_type};base64,{img_data}"
                        }
                    log.debug(f"Found image {img_path!r}, {len(data)} bytes")
                content.append(item)

            conversation.append(FLAG2ROLE[flag.lower()](content=content))

        return merge_message_runs(conversation)

    def rename_by_title(self):
        dirname = os.path.dirname(self.filepath)
        ext = os.path.splitext(self.filepath)[1]

        # Compute the new name without worrying about duplicates
        title, *_ = self.text.split("\n", 1)

        if AUTO_TITLE in title:  # BEFORE cleaning it
            log.warning(f"{AUTO_TITLE!r} in title. Not renaming!")
            return

        # Clean the current for possible "<name> (n).<ext>"
        cleaned_filepath = clean_filepath(self.filepath)
        cleaned_filename = os.path.basename(cleaned_filepath)
        log.debug(f"{cleaned_filename = }")

        # Create a filename from the title
        title_based_filename = title2filename(title, ext=ext)
        title_based_filepath = os.path.join(dirname, title_based_filename)
        log.debug(f"{title_based_filename = }")
        if cleaned_filename == title_based_filename:
            log.debug("Already named by title. No action needed")
            return

        title_based_filepath = uniqueify_filepath(title_based_filepath)
        shutil.move(self.filepath, title_based_filepath)

        log.info(f"Rename by title {self.filepath!r} --> {title_based_filepath!r}")
        self.filepath = title_based_filepath


loads = Conversation.loads


def file_edit(filepath, *, prompt, editor):
    size0 = os.path.getsize(filepath)
    mtime0 = os.path.getmtime(filepath)

    if prompt:
        with open(filepath, "rb+") as fp:
            # Need to be in binary mode for seek
            fp.seek(0, 2)  # Move the cursor to the end of the file
            if fp.tell() > 0:  # Check if the file is not empty
                fp.seek(-1, 2)  # Move the cursor to the last character
                last_char = fp.read(1).decode()
            else:
                last_char = ""

            if last_char and last_char != "\n":
                log.debug("Adding a new line")
                fp.write(b"\n")
            fp.write(prompt.encode())

    if editor:
        # Use shlex.split in case there are flags with the environment variable
        editcmd = shlex.split(CONFIG.TEXTLLM_EDITOR) + [filepath]
        log.debug(f"Calling: {editcmd!r}")
        with open("/dev/tty", "r") as tty:
            subprocess.run(editcmd, stdin=tty, check=True)

    size1 = os.path.getsize(filepath)
    mtime1 = os.path.getmtime(filepath)
    if size1 == size0 and abs(mtime1 - mtime0) <= 0.5:
        return False
    return True


def process_msg_for_images(lines):
    # Regex to capture markdown images
    image_regex = re.compile(
        r"""
        ^               # Start of a line
        !\[             # Literal '![', start of markdown image
        (.*?)           # Non-greedy capture for the alt text (optional)
        \]              # Literal closing bracket
        \(\s*           # Literal '(', start of URL, allowing optional whitespace
        (.*?)           # Non-greedy capture for the URL
        \s*             # Allow optional whitespace
        (?:             # Non-capturing group for optional title
            "           # Opening quote for title
            (.*?)       # Non-greedy capture for the title text
            "           # Closing quote for title
        )?              # Title is optional
        \)              # Literal closing parenthesis
        \s*$            # Allow optional whitespace till the end of the line
        """,
        re.VERBOSE,
    )

    in_code_block = False
    final_lines = []
    image_urls = []

    for line in lines:
        # Check for start or end of a fenced code block
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            final_lines.append(line)
            continue

        # If inside a code block, just keep the line
        if in_code_block:
            final_lines.append(line)
            continue

        # If not inside a code block, check for images
        match = image_regex.match(line)
        if match:
            # Capture the URL from the image line
            url = match.group(2)
            image_urls.append(url)
        else:
            # Keep lines that are not image lines
            final_lines.append(line)

    # Return the processed text and list of image URLs
    return "\n".join(final_lines), image_urls


########################################
############ Filename Utils ############
########################################
def clean_filepath(filepath):
    """'/path/to/file (1).ext --> '/path/to/file.ext'"""
    base, ext = os.path.splitext(filepath)
    cleaned_filepath = re.sub(r" \(\d+\)$", "", base) + ext
    return cleaned_filepath


def title2filename(title, ext=".md"):
    """Take a title and process it to a filename."""
    invalid_chars = set(
        "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13"
        '\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"*/:<>?\\|'
    )
    title = title.strip().strip("#").strip()
    title = "".join(c for c in title if c not in invalid_chars)
    title = title[: (MAX_FILENAME_CHAR - len(ext))]
    title = title + ext
    return title


def uniqueify_filepath(filepath):
    """Ensure filepath doesn't exist by adding (n) to the name"""
    filepath0 = filepath
    dirname, filename = os.path.split(filepath)
    base, ext = os.path.splitext(filename)

    c = 0
    while os.path.exists(filepath):
        c += 1
        if c >= 100:
            raise ValueError(f"Too many for {filepath0!r}")

        new = f"{base} ({c}){ext}"
        filepath = os.path.join(dirname, new)
    log.debug(f"{filepath0!r} required {c} iterations for unique name: {filepath!r}")
    return filepath


########################################
########## END Filename Utils ##########
########################################


def grouper(iterable, n, *, fillvalue=None):
    iterators = [iter(iterable)] * n
    return itertools.zip_longest(*iterators, fillvalue="")


class NoHumanMessageError(ValueError):
    """Error when a conversation doesn't end with a HumanMessage"""


def cli(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Simple LLM interface that reads and writes to a text file",
        epilog="See readme.md for details on format description",
        # formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "filepath",
        nargs="?",
        default=None,
        help=f"""
            Specifies the input file in the noted format. If not provided, the default 
            file {DEFAULT_FILEPATH!r} will be used, with an incremented filename to 
            ensure uniqueness. If you specify an existing directory, {DEFAULT_FILEPATH!r} 
            will be created in that directory.
            """,
    )

    parser.add_argument(
        "--env",
        help="""
            Specify an additional environment file to load. Note, %(prog)s will 
            also look for a .env file and from $TEXTLLM_ENV_PATH. 
            
            Useful for storing API keys""",
    )

    parser.add_argument(
        "--title",
        choices=["auto", "only", "off"],
        default="auto",
        help=f"""
            [%(default)s] How to set the title. If 'auto', will replace {AUTO_TITLE!r}
            with the generated title. If 'only', will only replace the title and
            not continue the chat. If 'off', will not update the title (or rename). 
            The title is the first line.
            """,
    )

    parser.add_argument(
        "--require-user-prompt",
        dest="require_user_prompt",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="""
            [%(default)s] Whether or not to require there be a user prompt at the end of 
            the messages.
        """,
    )

    parser.add_argument(
        "--rename",
        "--move",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=f"""
            Rename the file based on the title. The title must NOT have {AUTO_TITLE!r}
            in it. Will increment the filename as needed if one already exists.
            If a filename is specified, default is False. If filename is not specified, default is True.
        """,
    )

    parser.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=f"""
            [%(default)s] Whether or not to stream the model response to stdout in 
            addition to writing it to file. 
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s-" + __version__,
    )

    verb = parser.add_argument_group("Verbosity Settings:")
    verb.add_argument(
        "-q", "--quiet", action="count", default=0, help="Decrease Verbosity"
    )
    verb.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase Verbosity"
    )

    edit = parser.add_argument_group(
        title="Edit Settings",
        description="""
            These options let you add the prompt and/or edit the file directly
            before calling the LLM. Note it is assumed that a '--- User ---'
            heading is present (as it should be by default). 
            """,
    )
    edit.add_argument(
        "--prompt",
        metavar="text",
        default="",
        help="""
            Prompt text to add. Will be included if --edit. 
        """,
    )
    edit.add_argument(
        "--stdin",
        action="store_true",
        help="""
            Read stdin for prompt. Will go *after* --prompt. Will be included if --edit.
        """,
    )

    edit.add_argument(
        "--edit",
        action="store_true",
        help="""
            Open an interactive editor with the file. Will try $TEXTLLM_EDITOR, then
            $EDITOR, then finally fallback to 'vi'.
        """,
    )

    args = parser.parse_args(argv)

    # Define logging levels
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    level_index = args.verbose - args.quiet + 2  # +1: WARNING, +2: INFO
    level_index = max(0, min(level_index, len(levels) - 1))  # Always keep ERROR

    log.setLevel(logging.DEBUG)  # Highest. Handler will set lower
    fmt = logging.Formatter(
        "%(asctime)s:%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(levels[level_index])

    log.handlers.clear()
    log.addHandler(console_handler)
    if TEST_MODE:
        logfile = f"{args.filepath}.log" if args.filepath else "log"
        try:
            os.makedirs(os.path.dirname(logfile))
        except OSError:
            pass
        file_handler = logging.FileHandler(logfile, mode="w")
        file_handler.setFormatter(fmt)
        file_handler.setLevel(logging.DEBUG)
        log.addHandler(file_handler)

    log.debug(f"{argv = }")
    log.debug(f"{args = }")

    # Load the environment. Can be in three possible places (a,b,c below)
    if CONFIG.TEXTLLM_ENV_PATH:  # (a) Specified environment variable with the path
        if load_dotenv(CONFIG.TEXTLLM_ENV_PATH, override=True):
            log.debug(f"Loaded env from ${CONFIG.TEXTLLM_ENV_PATH = }")
        else:
            log.info(f"Could not load env from specified ${CONFIG.TEXTLLM_ENV_PATH = }")
    if load_dotenv(override=True):  # (b) a .env file
        log.debug(f"Loaded env from a found '.env' file")
    if args.env:  # (c) specified --env at the command line
        if load_dotenv(args.env, override=True):
            log.debug(f"Loaded env from args {args.env!r}")
        else:
            log.info(f"env file {args.env!r} not loaded or found")

    # Handle default --rename
    if args.rename is None:
        args.rename = args.filepath is None or os.path.isdir(args.filepath)
        log.debug("Settings --rename to {args.rename}.")

    # Handle edit modes.
    args.prompt = args.prompt.strip()
    if args.prompt == "-":
        log.warning("To read stdin, use --stdin")
    if args.stdin:
        log.debug("reading stdin")
        args.prompt = args.prompt + "\n\n" + sys.stdin.read().strip()
        args.prompt = args.prompt.strip()
    edit_mode = bool(args.edit or args.prompt or args.stdin)
    log.debug(f"{edit_mode = }")

    try:
        if args.filepath is None:
            args.filepath = uniqueify_filepath(DEFAULT_FILEPATH)
            log.debug(f"No filepath speciried. Set {args.filepath!r}")
        elif os.path.isdir(args.filepath):
            fp = os.path.join(args.filepath, DEFAULT_FILEPATH)
            args.filepath = uniqueify_filepath(fp)
            log.debug(f"Directory specified. Set {args.filepath!r}")

        filepath = args.filepath
        if not os.path.exists(filepath):
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "xt") as fp:
                if CONFIG.TEXTLLM_TEMPLATE_FILE:
                    with open(CONFIG.TEXTLLM_TEMPLATE_FILE, "rt") as fp2:
                        fp.write(fp2.read())
                else:
                    fp.write(CONFIG.TEMPLATE)
            log.info(f"{filepath!r} does not exist. Created template.")

            if not edit_mode:
                return
        else:
            log.debug(f"{filepath!r} exists")

        if edit_mode and not file_edit(filepath, prompt=args.prompt, editor=args.edit):
            # edit returns True iff it was modified.
            raise ValueError("File not modified")

        convo = Conversation(filepath)

        if args.title != "off":
            convo.set_title()  # Will do nothing if AUTO_TITLE not in the top line
        if args.title == "only":
            if TEST_MODE:
                return convo
            return

        convo.chat(
            require_user_prompt=args.require_user_prompt,
            stream_model=args.stream,
        )

        if args.rename:
            convo.rename_by_title()

        if TEST_MODE:
            return convo

    except Exception as E:
        log.error(E)
        if levels[level_index] == logging.DEBUG or TEST_MODE:
            raise
        sys.exit(1)


if __name__ == "__main__":
    cli()
