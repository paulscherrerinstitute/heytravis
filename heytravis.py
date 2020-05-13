#!/usr/bin/env python3

import argparse
import functools
import os
import tokenize as tk #TODO: do we even need that?


DEFAULT_FNAME = "setup.py"

ALLOWED_COMMANDS = ( #TODO what else?
    "major",  "minor",  "patch",
    "+1.0.0", "+0.1.0", "+0.0.1"
    # plus absolute version
)


def main():
    clargs = handle_clargs()
    fname = clargs.filename

    sp = SetupPy(fname)
    old_version, new_version = run_commands(sp, clargs.command, clargs.verbose)
    git_commands = build_git_commands(fname, new_version)

    if clargs.debug:
        print(sp)
        print_cli(git_commands)
        raise SystemExit

    if not clargs.force:
        if old_version == new_version:
            msg = f"Version ({new_version}) unchanged."
            raise SystemExit(msg)
        if SemVer(old_version) > SemVer(new_version): # String comparison fails for 0.0.9 < 0.0.10
            msg = f"Version {new_version} is smaller than {old_version}."
            raise SystemExit(msg)

    if clargs.yes or ask_Yes_no(f"Last version was v{old_version}. Do you want to release v{new_version}"):
        sp.write(fname)
        run_cli(git_commands)


def handle_clargs():
    parser = argparse.ArgumentParser(description="Hey, Travis! Make a release!!")

    msg = "from: " + ", ".join(ALLOWED_COMMANDS) + " or an absolute version like 3.2.1 (default: patch)"
    parser.add_argument("command", nargs="*", default=["patch"], help=msg)
    parser.add_argument("-i", "--in", default=DEFAULT_FNAME, dest="filename", help=f"input file name (default: {DEFAULT_FNAME})")

    parser.add_argument("-f", "--force",   action="store_true", help="force version change for new <= old")
    parser.add_argument("-y", "--yes",     action="store_true", help="assume yes on final prompt")
    parser.add_argument("-d", "--debug",   action="store_true", help="print commands instead of running them")
    parser.add_argument("-v", "--verbose", action="store_true", help="print version changes")

    clargs = parser.parse_args()
    commands = clargs.command

    to_check = set(commands) - set(ALLOWED_COMMANDS)
    failed = set()
    for cmd in to_check:
        try:
            SemVer(cmd)
        except:
            failed.add(cmd)
    if failed:
        failed = sorted(failed)
        failed = " ".join(failed)
        msg = parser.format_usage()
        msg += "{}: error: unrecognized commands: {}".format(parser.prog, failed)
        raise SystemExit(msg)

    return clargs



class SetupPy:

    def __init__(self, fname):
        self.fname = fname
        toks = read_tokens(fname)

        self._pre  = parse_until_version(toks)
        self._ver  = parse_version(toks)
        self._post = parse_remainder(toks)

        ver = unrepr(self._ver.string)
        self.ver = SemVer(ver)


    def rebuild(self):
        self._ver.string = repr(self.ver)
        ver = self._ver.to_tokeninfo()
        res = self._pre + [ver] + self._post
        return res


    def write(self, fname):
        write_tokens(self.rebuild(), fname)


    def __str__(self):
        fn = self.fname + ":"
        header = "\n" + fn + "\n" + "="*len(fn) + "\n"
        return header + tk.untokenize(self.rebuild())



def read_tokens(fname):
    with tk.open(fname) as f:
        data = f.readline
        yield from tk.generate_tokens(data)

def write_tokens(toks, fname):
    data = tk.untokenize(toks)
    with open(fname, "w") as f:
        f.write(data)


def parse_until_version(toks):
    res = []
    for t in toks:
        res.append(t)

        if t.type != tk.NAME:
            continue

        if t.string == "version":
            t = next(toks)
            assert t.type == tk.OP
            assert t.string == "="
            res.append(t)
            return res

    raise ValueError("no version information found in file")


def parse_version(toks):
    t = next(toks)
    assert t.type == tk.STRING
    return MutableToken(t)

def parse_remainder(toks):
    return list(toks)



class MutableToken:

    def __init__(self, tokeninfo):
        self.type, self.string, self.start, self.end, self.line = tokeninfo

    def to_tokeninfo(self):
        return tk.TokenInfo(self.type, self.string, self.start, self.end, self.line)



def unrepr(r):
    assert r.startswith("'") or r.startswith('"')
    assert r.endswith("'") or r.endswith('"')
    return r.strip("'").strip('"')



@functools.total_ordering
class SemVer:

    def __init__(self, s):
        strings = s.strip().split(".")
        self.major, self.minor, self.patch = (int(i) for i in strings)

    def __repr__(self):
        return repr(str(self))

    def __str__(self):
        vals = (self.major, self.minor, self.patch)
        strings = (str(i) for i in vals)
        return ".".join(strings)

    def inc_major(self):
        self.major += 1
        self.minor = 0
        self.patch = 0

    def inc_minor(self):
        self.minor += 1
        self.patch = 0

    def inc_patch(self):
        self.patch += 1

    def __eq__(self, other):
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch)

    def __gt__(self, other): #TODO simplify
        if self.major > other.major:
            return True
        elif self.major == other.major:
            if self.minor > other.minor:
                return True
            elif self.minor == other.minor:
                if self.patch > other.patch:
                    return True
        return False



def run_commands(sp, commands, verbose):
    old_version = str(sp.ver)
    if verbose:
        print(old_version)

    for cmd in commands:
        if   cmd in ("major", "+1.0.0"): sp.ver.inc_major()
        elif cmd in ("minor", "+0.1.0"): sp.ver.inc_minor()
        elif cmd in ("patch", "+0.0.1"): sp.ver.inc_patch()
        else:
            sp.ver = SemVer(cmd)

        if verbose:
            print("->", sp.ver)

    new_version = str(sp.ver)
    return old_version, new_version


def build_git_commands(fname, version):
    commands = [
        f"git add {fname}",
        f"git commit -m 'Release v{version}' {fname}",
        f"git tag -a -m 'Release v{version}' {version}",
        f"git push origin {version}",
    ]

#    commands = ["echo " + cmd for cmd in commands] #TODO only for testing the command execution

    return commands


def run_cli(commands):
    commands = "; ".join(commands)
    os.system(commands)

def print_cli(commands):
    print("\n".join(commands))



def ask_Yes_no(question, default="y", ctrl_c="n", ctrl_d=None):
    ctrl_d = default if ctrl_d is None else ctrl_d

    ANSWERS = {
        "y":   True,
        "n":   False,
        "yes": True,
        "no":  False
    }

    OPTION_PROMPTS = {
        None: "y/n",
        "y":  "Y/n",
        "n":  "y/N"
    }

    option_prompt = OPTION_PROMPTS[default]
    prompt = question + "? [{}] ".format(option_prompt)

    ans = None
    while ans not in ANSWERS:
        try:
            ans = input(prompt).lower()
            if not ans:  # response was an empty string
                ans = default
        except KeyboardInterrupt:
            print()
            ans = ctrl_c
        except EOFError:
            print()
            ans = ctrl_d

    return ANSWERS[ans]





if __name__ == "__main__":
    main()



