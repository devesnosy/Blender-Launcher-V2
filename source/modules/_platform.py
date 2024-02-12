import os
import platform
import sys
from functools import cache
from locale import LC_ALL, getdefaultlocale, setlocale
from pathlib import Path
from subprocess import DEVNULL, PIPE, STDOUT, Popen, call, check_call, check_output


@cache
def get_platform():
    platforms = {
        "linux": "Linux",
        "linux1": "Linux",
        "linux2": "Linux",
        "darwin": "macOS",
        "win32": "Windows",
    }

    if sys.platform not in platforms:
        return sys.platform

    return platforms[sys.platform]


@cache
def get_platform_full():
    return f"{get_platform()} {os.name} {platform.release()}"


def set_locale():
    platform = get_platform()

    if platform == "Windows":
        setlocale(LC_ALL, "eng_usa")
    elif platform in {"Linux", "macOS"}:
        setlocale(LC_ALL, "en_US.UTF-8")


default_locale = getdefaultlocale(("LC_ALL",))[0]


def reset_locale():
    setlocale(LC_ALL, default_locale)


def get_environment():
    # Make a copy of the environment
    env = dict(os.environ)
    # For GNU/Linux and *BSD
    lp_key = "LD_LIBRARY_PATH"
    lp_orig = env.get(lp_key + "_ORIG")

    if lp_orig is not None:
        # Restore the original, unmodified value
        env[lp_key] = lp_orig
    else:
        # This happens when LD_LIBRARY_PATH was not set
        # Remove the env var as a last resort
        env.pop(lp_key, None)

    return env


def _popen(args):
    if get_platform() == "Windows":
        DETACHED_PROCESS = 0x00000008
        return Popen(
            args,
            shell=True,
            stdin=None,
            stdout=None,
            stderr=None,
            close_fds=True,
            creationflags=DETACHED_PROCESS,
            start_new_session=True,
        )

    return Popen(
        args,
        shell=True,
        stdout=None,
        stderr=None,
        close_fds=True,
        preexec_fn=os.setpgrp,  # type: ignore
        env=get_environment(),
    )


def _check_call(args):
    platform = get_platform()

    if platform == "Windows":
        from subprocess import CREATE_NO_WINDOW

        return check_call(args, creationflags=CREATE_NO_WINDOW, shell=True, stderr=DEVNULL, stdin=DEVNULL)

    return check_call(args, shell=False, stderr=DEVNULL, stdin=DEVNULL)


def _call(args):
    platform = get_platform()

    if platform == "Windows":
        from subprocess import CREATE_NO_WINDOW

        call(args, creationflags=CREATE_NO_WINDOW, shell=True, stdout=PIPE, stderr=STDOUT, stdin=DEVNULL)
    elif platform == "Linux":
        pass


def _check_output(args):
    platform = get_platform()

    if platform == "Windows":
        from subprocess import CREATE_NO_WINDOW

        return check_output(args, creationflags=CREATE_NO_WINDOW, shell=True, stderr=DEVNULL, stdin=DEVNULL)

    return check_output(args, shell=False, stderr=DEVNULL, stdin=DEVNULL)


@cache
def is_frozen():
    """
    This function checks if the application is running as a bundled executable
    using a package like PyInstaller. It returns True if the application is "frozen"
    (i.e., bundled as an executable) and False otherwise.
    """

    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


@cache
def get_cwd():
    if is_frozen():
        return Path(os.path.dirname(sys.executable))

    return Path.cwd()
