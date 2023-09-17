import subprocess
import threading
from functools import partial
import shutil
from shortpath83 import convert_path_in_string

taskkillexe = shutil.which("taskkill.exe")
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE
creationflags = subprocess.CREATE_NO_WINDOW
invisibledict = {
    "startupinfo": startupinfo,
    "creationflags": creationflags,
    "start_new_session": True,
}


def callback_func(pid):
    subprocess.Popen(f"{taskkillexe} /F /PID {pid} /T", **invisibledict)


def timer_thread(timer, pid):
    timer.start()
    timer.join()
    callback_func(pid)


class Popen(subprocess.Popen):
    def __init__(
        self,
        args,
        bufsize=-1,
        executable=None,
        stdin=None,
        stdout=None,
        stderr=None,
        preexec_fn=None,
        close_fds=True,
        shell=False,
        cwd=None,
        env=None,
        universal_newlines=None,
        startupinfo=None,
        creationflags=0,
        restore_signals=True,
        start_new_session=False,
        pass_fds=(),
        *,
        group=None,
        extra_groups=None,
        user=None,
        umask=-1,
        encoding=None,
        errors=None,
        text=None,
        pipesize=-1,
        process_group=None,
        **kwargs,
    ):
        r"""
        Extended version of `subprocess.Popen` with additional features:

        Args:
            args (str or list): The command to run, either as a string or as a sequence of arguments.
            bufsize (int, optional): Buffering policy. Default is -1.
            executable (str, optional): The name or path of the program to execute. Default is None.
            stdin (int, optional): File descriptor for the standard input. Default is None.
            stdout (int, optional): File descriptor for the standard output. Default is None.
            stderr (int, optional): File descriptor for the standard error. Default is None.
            preexec_fn (callable, optional): A function to be called in the child process before executing the command.
            close_fds (bool, optional): Close all file descriptors in the child process. Default is True.
            shell (bool, optional): Run the command in a shell. Default is False.
            cwd (str, optional): The current working directory. Default is None.
            env (dict, optional): Environment variables to set for the child process. Default is None.
            universal_newlines (bool, optional): Convert newlines to the universal newline convention. Default is None.
            startupinfo (subprocess.STARTUPINFO, optional): Startup information for the child process. Default is None.
            creationflags (int, optional): Flags to control the child process creation. Default is 0.
            restore_signals (bool, optional): Restore the default signal handlers in the child process. Default is True.
            start_new_session (bool, optional): Start the child process in a new session. Default is False.
            pass_fds (tuple, optional): File descriptors to pass to the child process. Default is ().
            group (int, optional): The child process group ID. Default is None.
            extra_groups (tuple, optional): Additional group IDs to set for the child process. Default is None.
            user (int, optional): The user ID for the child process. Default is None.
            umask (int, optional): The file creation mask for the child process. Default is -1.
            encoding (str, optional): The encoding to use for text mode. Default is None.
            errors (str, optional): The error handling strategy for text mode. Default is None.
            text (bool, optional): Whether to open streams in text mode. Default is None.
            pipesize (int, optional): The buffer size for pipes. Default is -1.
            process_group (int, optional): The process group ID for the child process. Default is None.

        Additional Keyword Args:
            timeout (float, optional): Maximum time in seconds to wait for the process to complete.
            convert_to_83 (bool, optional): Convert file paths to their short 8.3 format. Default is False.

        Attributes:
            stdout_lines (list): A list of lines read from the standard output.
            stderr_lines (list): A list of lines read from the standard error.

        Methods:
            __exit__(*args, **kwargs): Cleanup method called when the object goes out of scope.
            __del__(*args, **kwargs): Cleanup method called when the object is deleted.
        """
        stdin = subprocess.PIPE
        stdout = subprocess.PIPE
        universal_newlines = False
        stderr = subprocess.PIPE
        # shell = False
        hastimeout = "timeout" in kwargs
        _convert_to_83 = "convert_to_83" in kwargs
        if _convert_to_83:
            del kwargs["convert_to_83"]
            if isinstance(args, (list, tuple)):
                args = [convert_path_in_string(x) for x in args]
            elif isinstance(args, str):
                args = convert_path_in_string(args)
        timeout = 0
        if hastimeout:
            timeout = kwargs["timeout"]

            del kwargs["timeout"]

        super().__init__(
            args,
            bufsize=bufsize,
            executable=executable,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            preexec_fn=preexec_fn,
            close_fds=close_fds,
            shell=shell,
            cwd=cwd,
            env=env,
            universal_newlines=universal_newlines,
            startupinfo=startupinfo,
            creationflags=creationflags,
            restore_signals=restore_signals,
            start_new_session=start_new_session,
            pass_fds=pass_fds,
            group=group,
            extra_groups=extra_groups,
            user=user,
            umask=umask,
            encoding=encoding,
            errors=errors,
            text=text,
            **kwargs,
        )
        if hastimeout:
            timer = threading.Timer(timeout, partial(callback_func, self.pid))
            timer.start()
        self.stdout_lines = []
        self.stderr_lines = []
        self._stdout_reader = StreamReader(self.stdout, self.stdout_lines)
        self._stderr_reader = StreamReader(self.stderr, self.stderr_lines)
        stdo = self._stdout_reader.start()
        stdee = self._stderr_reader.start()
        for stdo_ in stdo:
            self.stdout_lines.append(stdo_)
        for stde_ in stdee:
            self.stderr_lines.append(stde_)

        if hastimeout:
            timer.cancel()
        self.stdout = b"".join(self.stdout_lines)
        self.stderr = b"".join(self.stderr_lines)

    def __exit__(self, *args, **kwargs):
        try:
            self._stdout_reader.stop()
            self._stderr_reader.stop()
        except Exception as fe:
            pass

        super().__exit__(*args, **kwargs)

    def __del__(self, *args, **kwargs):
        try:
            self._stdout_reader.stop()
            self._stderr_reader.stop()
        except Exception as fe:
            pass
        super().__del__(*args, **kwargs)


class StreamReader:
    def __init__(self, stream, lines):
        self._stream = stream
        self._lines = lines
        self._stopped = False

    def start(self):
        while not self._stopped:
            line = self._stream.readline()
            if not line:
                break
            yield line

    def stop(self):
        self._stopped = True
