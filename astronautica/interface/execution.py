"""Module dedicated solely to the execution of Command Functions and the
    handling of their Returns.
"""

from asyncio import AbstractEventLoop, Task
from typing import AsyncIterator, Coroutine, Iterator, List, Sequence

from .commands import CommandNotAvailable, CommandNotFound, CommandRoot
from .etc import EchoType, T


def handle_return(echo: EchoType, result):
    """We have received either an Iterator or the result of a Command Function.
        If it is an Iterator or a Sequence, loop through it and Echo each
        element to the Output. Otherwise, simply Echo a String of it.
    """
    if isinstance(result, (Iterator, Sequence)) and not isinstance(result, str):
        for each in result:
            if isinstance(each, BaseException):
                echo(f"{type(each).__name__}: {each}")
            elif each is not None:
                echo(str(each))

    else:
        echo(str(result))


async def handle_async(line: str, echo: EchoType, result, dispatched: bool = False):
    """We have received...something. So long as it is a Coroutine, replace it
        with the result of awaiting it. If it is an Asynchronous Iterator,
        loop through it and Echo each element. If it is anything else, simply
        forward it to the Synchronous Return Handler.
    """
    try:
        while isinstance(result, Coroutine):
            result = await result

        if isinstance(result, AsyncIterator):
            kw = line.split()[0].lower()

            async for each in result:
                if isinstance(each, BaseException):
                    echo(f"! {T.bold(kw)}: {type(each).__name__}: {each}")
                elif each is not None:
                    echo(f"  {T.bold(kw)}: {each}")

        elif result is not None:
            handle_return(echo, result)

    except Exception as exc:
        echo(
            f"Error: {T.bold(line)}\n    {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {T.bold(line)}\n    {type(exc).__name__}"
        )

    finally:
        if dispatched:
            echo(f"Command Complete: {T.bold(line)}")


def execute_function(
    line: str,
    echo: EchoType,
    handler: CommandRoot,
    loop: AbstractEventLoop,
    tasks: List[Task],
    set_job,
) -> None:
    """Find the Command Object and Tokens represented by the input line, and
        handle the process of either retrieving its output, or dispatching a
        Task to do so.
    """
    tokens = handler.split(line)

    for i, token in enumerate(tokens):
        if token == "|":
            tokens, filt = tokens[:i], tokens[i + 1:]

            def output(*text, **kw) -> None:
                if any(want in ln for want in filt for ln in text):
                    return echo(*text, **kw)
            break

        elif token == "||":
            tokens, filt = tokens[:i], tokens[i + 1:]

            def output(*text, **kw) -> None:
                if all(want in ln for want in filt for ln in text):
                    return echo(*text, **kw)
            break

        elif token == "%":
            tokens, filt = tokens[:i], tokens[i + 1:]

            def output(*text, **kw) -> None:
                if not any(want in ln for want in filt for ln in text):
                    return echo(*text, **kw)
            break
    else:
        output = echo

    command, args = handler.get_command(tokens)
    try:
        if command is None:
            raise CommandNotFound(f"Command {tokens[0].upper()!r} not found.")
        elif command.keyword in handler.disabled:
            raise CommandNotAvailable(
                f"Command {tokens[0].upper()!r} not available."
            )

        if command.is_async:
            # This Command Function is Asynchronous. Dispatch a Task to run
            #   and manage it.
            task = loop.create_task(
                handle_async(line, output, command(args), command.dispatch_task)
            )
            tasks.append(task)

            if not command.dispatch_task:
                set_job(task)
                task.add_done_callback(lambda *_: set_job(None))
            # else:
            #     echo("Asynchronous Task dispatched.")
        else:
            # This Command Function is Synchronous. We have no choice but to
            #   accept the blocking.
            handle_return(output, command(args))

    except Exception as exc:
        echo(
            f"Error: {T.bold(line)}\n    {type(exc).__name__}: {exc}"
            if str(exc)
            else f"Error: {T.bold(line)}\n    {type(exc).__name__}"
        )
