import argparse

import re
import os
from os import path
from tempfile import TemporaryDirectory

import shutil
import signal
import subprocess


DOCKER_IMAGE = "ghcr.io/softvare-group/ddnnife"
DOCKER_TAG = "main-amd64"


class DockerHarness():
    def __init__(self):
        self._dir = TemporaryDirectory()
        self.filemap = {}

    def push(self, filepath):

        filepath = path.abspath(filepath)

        if filepath in self.filemap:
            raise ValueError()

        if path.exists(filepath):
            newpath = shutil.copy(filepath, self._dir.name)
        else:
            newpath = path.join(self._dir.name, path.basename(filepath))

        self.filemap[filepath] = newpath

        return newpath

    def pull(self, filepath):

        filepath = path.abspath(filepath)

        if filepath not in self.filemap:
            raise ValueError()

        shutil.copy(self.filemap[filepath], filepath)

    def __repr__(self):
        return self._dir.name


def harnessed(*varnames):
    def harness_decorator(f):
        def wrapper(*args, **kwargs):

            harness = DockerHarness()

            files = []
            newargs = []
            newkwargs = {}
            newkwargs.update(kwargs)

            varnames_avail = f.__code__.co_varnames

            var2values = list(zip(varnames_avail, args))
            binds = dict(var2values)

            for var in varnames:
                if var in binds:
                    continue
                elif var in kwargs:
                    value = kwargs[var]
                    if value is None:
                        continue

                    files.append(value)
                    newpath = harness.push(value)
                    newkwargs[var] = newpath
                else:
                    raise ValueError(f"Cannot harness undefined variable ({var})")

            for var, value in var2values:
                if var in varnames:
                    if value is None:
                        continue

                    files.append(value)
                    newpath = harness.push(value)
                    newkwargs[var] = newpath
                else:
                    newargs.append(value)

            out = f(*newargs, **newkwargs)

            for filepath in files:
                harness.pull(filepath)

            return out

        return wrapper
    return harness_decorator


def via_subprocess(cmd, timeout = None, capture_output = False):

    if timeout is not None:

        with subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid) as proc:
            try:
                out, err = proc.communicate(timeout = timeout)
              
            except subprocess.TimeoutExpired as te:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                raise te

    else:
        cmd = re.split(r"\s+", cmd)
        return subprocess.run(cmd, capture_output = capture_output)


def run_ddnnife(file_in = None, file_out = None, file_nnf = None, **kwargs):
    return _run_ddnnife(file_in = file_in, file_out = file_out, file_nnf = file_nnf, **kwargs)


@harnessed("file_in", "file_out", "file_nnf")
def _run_ddnnife(file_in = None, file_out = None, file_nnf = None, cmd = None, image = DOCKER_IMAGE, tag = DOCKER_TAG, **kwargs):
    """ Executes ddnnife. Should not be called directly as run_ddnnife populates the file_fields for the harness """
    
    if file_in is not None:
        # then file_in is harnessed
        dir_working = path.dirname(file_in)
    else:
        dir_working = TemporaryDirectory().name

    call_cmd = f'docker run -v {dir_working}:{dir_working} --init {image}:{tag}'\
        f'{f" --input {file_in}" if file_in is not None else ""}'\
        f'{f" --output {file_out}" if file_out is not None else ""}'\
        f'{f" --save-ddnnf {file_nnf}" if file_nnf is not None else ""}'\
        f'{f" {cmd}" if cmd else ""}'

    try:
        call = via_subprocess(call_cmd, **kwargs)
    except subprocess.TimeoutExpired:
        print(f"Aborted at timeout (--timeout {kwargs["timeout"]})")
    except Exception as e:
        print(f"Failed with exception ({e})")
        print("--- STDOUT", "-" * 24)
        print(call.stdout.decode("utf-8"))
        print()
        print("--- STDERR", "-" * 24)
        print(call.stderr.decode("utf-8"))


def check(image, tag):
    call = via_subprocess(f"docker run {image}:{tag}", capture_output = True)
    return call and call.stderr.decode("utf-8").startswith("Usage: ddnnife [OPTIONS] [COMMAND]")


def check_install_ddnnife(image, tag):

    if check(image, tag):
        return True
    else:
        print(f"Could not find \"{image}:{tag}\" on your system.")
        answer = input("Do you want to download it? [yes/No]")
        print()
        
        if answer and answer.lower()[0] == "y":
            via_subprocess(f"docker pull {image}:{tag}")
            
            if not check(image, tag):
                print("Download failed")
                print()
            else:
                return True
    return False


def main():
    parser = argparse.ArgumentParser(
        prog='ddnnife-py',
        description='Wraps the Docker container for ddnnife to ease usage.',
        epilog='ddnnife-py by https://github.com/obddimal')

    parser.add_argument("-i", "--input", help = "DIMACS (for CNF) or NNF (for d-DNNF) file")  
    parser.add_argument("-o", "--output", nargs = "?", help = "(opt.) save output to file")
    parser.add_argument("--save-ddnnf", nargs = "?", help = "(opt.) save d-DNNF to file")  
    parser.add_argument("--timeout", nargs = "?", type = int, help = "(opt.) set a timeout")  
    parser.add_argument("--image", nargs = "?", type = str, default = DOCKER_IMAGE, help = "Docker image to use")  
    parser.add_argument("--tag", nargs = "?", type = str, default = DOCKER_TAG, help = "Tag to use")  
    parser.add_argument("cmd", nargs="*")

    args = parser.parse_args()

    args.cmd = " ".join(args.cmd).strip()

    if check_install_ddnnife(args.image, args.tag):
        run_ddnnife(file_in = args.input, file_out = args.output, file_nnf = args.save_ddnnf, cmd = args.cmd, timeout = args.timeout, image = args.image, tag = args.tag)

if __name__ == '__main__':
    main()
