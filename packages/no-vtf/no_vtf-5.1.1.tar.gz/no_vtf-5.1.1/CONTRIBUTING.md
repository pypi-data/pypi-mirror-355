# How to contribute

## Mailing list

The [mailing list](https://lists.sr.ht/~b5327157/no_vtf) is open for questions, support requests, and any other discussion.

Before preparing your message:
- follow the guide at [useplaintext.email](https://useplaintext.email) to configure your e-mail client for plaintext (`text/html` is always rejected at the server), and
- review the [mailing list etiquette](https://man.sr.ht/lists.sr.ht/etiquette.md) to ensure your message is properly formatted.

## Feedback

Feedback such as bug reports or feature requests can be submitted to the project's [ticket tracker](https://todo.sr.ht/~b5327157/no_vtf) and [mailing list](https://lists.sr.ht/~b5327157/no_vtf).

Please make sure to include links to relevant tickets in the discussions on the mailing list, and vice versa.

### Issues

If you found an issue, ensure you're using the latest version of the software.

If the problem persists, check the ticket tracker to see if a similar issue has been reported.
If not, please open a new ticket.
When reporting an issue, provide as much relevant information as possible, including expected and actual behavior, and details about your system.

If you're unsure, feel free to discuss the issue on the mailing list before creating a ticket.

### Security vulnerabilities

Refer to [SECURITY.md](https://git.sr.ht/~b5327157/no_vtf/tree/master/SECURITY.md) instead.

## Development (local)

The [Nox](https://nox.thea.codes/en/stable/) runner is used to build and test the project.
Nox sessions are implemented in `noxfile.py`.

You can install Nox via [pipx](https://pipx.pypa.io/stable/):

```
pipx install nox
```

### Test suite

The project has a comprehensive system test suite.
The test suite operates through the readback mode by comparing actual output with expected output based on individual tests (inputs and command line arguments).
Inputs and expected outputs are referred to as test samples.

New major functionality must be accompanied by relevant tests added to the test suite.
To add to the test suite, subclass `TestCase` and add test samples as necessary.

### Linting

Quality is enforced using standard tools: mypy, pyright, flake8, reuse, shellcheck, coverage, black, isort, shfmt.

```
# automatically fix formatting issues, then run analysis
nox -R -- --fix && nox -R
```

Add any new paths to .py files in the `lint()` function, and enable strict checks for them in `pyproject.toml`.

### Coverage

```
nox -R --session coverage
```

Branch coverage is measured by running the test suite.
The coverage HTML report will be generated under `htmlcov/`.

Aim for ~90% coverage.
If necessary, add more test cases and samples.

### Packaging

To create and test a Python distribution ([sdist](https://packaging.python.org/en/latest/overview/#python-source-distributions) and [wheel](https://packaging.python.org/en/latest/overview/#python-binary-distributions)):

```
nox --session package -- [OUT_SDIST_PATH [OUT_WHEEL_PATH]]
```

### Bundling

To create and test a [frozen bundle](https://pyinstaller.org/en/stable/index.html):

```
nox --session freeze -- [OUT_ARCHIVE_PATH [IN_SDIST_PATH]]
```

### Test samples manipulation

```
# extract the samples
nox --session test_extract -- DIR_PATH

# self-test (readback only)
nox --session test_readback -- DIR_PATH

# regenerate the expected output (write then readback)
nox --session test_write -- DIR_PATH

# equivalent invocation of the above R/W sessions
nox --session test_run -- --always-write --readback -- DIR_PATH
nox --session test_run -- --no-write --readback -- DIR_PATH
```

#### Updating test samples

To update test samples, compress the delta into `tar.xz` archives with `XZ_OPT=-9` and store them under `resources/test/samples/`.

You can automate this process using the `test_update` nox session (Linux-only):

1\. Extract the old samples:

```
nox --session test_extract -- DIR_PATH
```

2\. Add, update, or remove specific samples in `DIR_PATH`:

```
# example of an incremental update (generate output for new input only)
nox --session test_run -- -- DIR_PATH
```

> Note: Running `test_write` regenerates all output, which would cause the entire output to be considered modified and archived again.

3\. Create delta archives (comparing the original output from `test_extract` to the updated state in `DIR_PATH`):

```
nox --session test_update -- DIR_PATH
```

### Pre-build step

A pre-build step has to be run if a `.ksy` file was modified.
Outputs of this pre-build step are committed to the repository.

```
python3 ksy/compile.py
```

## Builds (remote)

Build is run automatically at [builds.sr.ht](https://builds.sr.ht/~b5327157/no_vtf) for every [repository push](https://builds.sr.ht/~b5327157/no_vtf/commits) and for every [received patch](https://builds.sr.ht/~b5327157/no_vtf/patches).

With every build, Python packages and frozen bundles are created and fully tested, on native Linux and also on Windows via [WINE](https://www.winehq.org).

For more details about how the Nox sessions are run during the build, refer to the build system implementation in `builds/`.

## Patches

This project accepts patches via the project's [mailing list](https://lists.sr.ht/~b5327157/no_vtf) instead of pull requests.

The only limitation of the workflow is that the build is still run with the old manifest when patching `.build.yml`.
In such case, a build with the patched manifest will be re-submitted by the maintainers manually.
Most likely, you do not need to be concerned about this.

### Preparing the repository

Clone the repository:

```
git clone https://git.sr.ht/~b5327157/no_vtf
```

Configure e-mail address of the project's mailing list:

```
git config sendemail.to '~b5327157/no_vtf@lists.sr.ht'
```

Configure the subject prefix to match the name of the repository:
```
git config format.subjectPrefix 'PATCH no_vtf'
```

### Preparing the patch

1. Make your changes and commit them locally on top of the `master` branch.
2. Test your changes at least via the `lint` and `package` Nox sessions.
3. Send your patch to the mailing list.

In case you need to rebase, follow the guide at [git-rebase.io](https://git-rebase.io).
If you are familiar with the concept already, you can use [lazygit](https://github.com/jesseduffield/lazygit) to speed up the process.

An interactive tutorial on using `git send-email` to send patches is available at [git-send-email.io](https://git-send-email.io).

### Follow-up

Any patches submitted will be built and tested automatically.
For the patch to be considered for upstreaming, the build must pass.

You will receive an e-mail about the build status, and you may receive some feedback on your patch from the maintainers.

The resulting artifacts (source distribution, Linux/Windows bundles and coverage report) will be available for download at the build status page.
In this way, you can also use the build system to create your own personalized copy of the software, even if the patches are not upstreamed.
