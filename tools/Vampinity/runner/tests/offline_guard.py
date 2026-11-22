"""Makes it impossible for a test in this process to reach the network or to start another program.

  import offline_guard
  offline_guard.install()        # before the runner is loaded

From then on every one of these records what was tried in ATTEMPTS and raises Blocked:

  - a socket that connects, binds, listens or sends to an address (socket.socket.connect, connect_ex, bind,
    listen, sendto, sendmsg), socket.create_connection, and every name lookup (getaddrinfo, gethostbyname,
    gethostbyname_ex, gethostbyaddr). urllib, http.client and ftplib all go through these.
  - a child process (subprocess.Popen, so run, call and check_output too; os.system, os.popen, os.posix_spawn,
    os.posix_spawnp and the os.exec* and os.spawn* family). A child could reach the network on its own.

Blocked is an OSError. The runner turns an OSError from the console into "no answer" and carries on, so a raise
alone could pass unseen. That is why ATTEMPTS exists: the tests check that it is empty after every case.

Standard library only. It changes nothing outside this process and nothing on disk.
"""
import os
import socket
import subprocess

ATTEMPTS = []
_saved = {}


class Blocked(OSError):
    """Something a test must never do: reach for the network, or start a program."""


def _refuse(what):
    def refused(*args, **kwargs):
        shown = ", ".join([repr(a)[:80] for a in args[:3] if not isinstance(a, socket.socket)])
        ATTEMPTS.append(f"{what}({shown})")
        raise Blocked(f"offline test: {what} is blocked ({shown})")
    refused.__name__ = what.rsplit(".", 1)[-1]
    return refused


class _NoPopen:
    """Stands in for subprocess.Popen: making one is the attempt."""

    def __init__(self, args=None, *more, **kwargs):
        shown = repr(args)[:160]
        ATTEMPTS.append(f"subprocess.Popen({shown})")
        raise Blocked(f"offline test: starting a program is blocked ({shown})")


_SOCKET_METHODS = ("connect", "connect_ex", "bind", "listen", "sendto", "sendmsg")
_SOCKET_FUNCTIONS = ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr")
_OS_FUNCTIONS = ("system", "popen", "posix_spawn", "posix_spawnp", "execv", "execve", "execvp", "execvpe", "execl",
                 "execle", "execlp", "execlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "spawnl", "spawnle",
                 "spawnlp", "spawnlpe", "startfile")


def install():
    """Put the guard in place. Calling it twice changes nothing."""
    if _saved:
        return
    for name in _SOCKET_METHODS:
        _saved["socket.socket." + name] = (socket.socket, name, socket.socket.__dict__.get(name))
        setattr(socket.socket, name, _refuse("socket." + name))
    for name in _SOCKET_FUNCTIONS:
        if hasattr(socket, name):
            _saved["socket." + name] = (socket, name, getattr(socket, name))
            setattr(socket, name, _refuse("socket." + name))
    _saved["subprocess.Popen"] = (subprocess, "Popen", subprocess.Popen)
    subprocess.Popen = _NoPopen
    for name in _OS_FUNCTIONS:
        if hasattr(os, name):
            _saved["os." + name] = (os, name, getattr(os, name))
            setattr(os, name, _refuse("os." + name))


def remove():
    """Take the guard away again (the tests do this when their module is done)."""
    for owner, name, original in _saved.values():
        if original is None:
            delattr(owner, name)  # a socket method the class only inherited: the inherited one shows again
        else:
            setattr(owner, name, original)
    _saved.clear()


def installed():
    return bool(_saved)
