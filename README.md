# Hey, Travis! Make a release!!

*heytravis* is a Python command-line tool for version-tagged commits of Python packages with the goal to trigger Travis-CI building Conda packages.

It assumes that 
- the package has a `setup.py` in which the `version` string needs to be updated,
- the `version` string follows [semantic versioning](https://semver.org/), and
- a tagged commit should be made and pushed with the tag being identical to the updated `version` string.

In [PSI](https://github.com/paulscherrerinstitute)'s current github setup this triggers Travis to build a new release and upload it to the [PSI Conda repo](https://anaconda.org/paulscherrerinstitute) (given that the committing acount has everything configured correctly :wink:).

---

Most often you probably just want to run a bare `$ ./heytravis.py`, which bumps the *patch* (third/last number) of the version by one (and asks you for confirmation before committing it).

*heytravis* has a few options. Excerpt from `$ ./heytravis.py -h`:
```
  -i FILENAME, --in FILENAME
                        input file name (default: setup.py)
  -f, --force           force version change for new <= old
  -y, --yes             assume yes on final prompt
  -d, --debug           print commands instead of running them
  -v, --verbose         print version changes
```

... and a few commands:

- `patch` or `+0.0.1`: increase the *patch* version (this is the default).
- `minor` or `+0.1.0`: increase the *minor* version, reset *patch* to zero.
- `major` or `+1.0.0`: increase the *major* version, reset *minor* and *patch* to zero.
- absolute versions like `3.2.1`

Multiple commands will be applied consecutively:
```
$ ./heytravis.py patch patch major minor major 4.2.1 minor minor -v
0.0.10
-> 0.0.11
-> 0.0.12
-> 1.0.0
-> 1.1.0
-> 2.0.0
-> 4.2.1
-> 4.3.0
-> 4.4.0
Last version was v0.0.10. Do you want to release v4.4.0? [Y/n]
```
