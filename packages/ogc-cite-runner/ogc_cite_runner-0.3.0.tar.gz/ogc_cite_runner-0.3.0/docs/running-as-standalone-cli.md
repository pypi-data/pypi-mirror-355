---
hide:
  - navigation
---

# Running as a standalone application


## Installation

ogc-cite-runner is available on the [Python Package Index (PyPI):material-open-in-new:]{: target="blank_" }
so all common installation methods are available.

=== "pipx"

    The recommended way of installing ogc-cite-runner is by using [pipx:material-open-in-new:]{: target="blank_" },
    which will install ogc-cite-runner and make it available globally on your system in a fully isolated environment.

    ```shell
    pipx install ogc-cite-runner
    ```

=== "pip"

    You can also use [pip:material-open-in-new:]{: target="blank_" } to install ogc-cite-runner, in which case we
    recommend starting by creating a virtualenv, activating it, and finally installing ogc-cite-runner

    ```shell
    python3 -m venv .venv
    source .venv/bin/activate
    pip install ogc-cite-runner
    ```



#### Starting a local teamengine instance

ogc-cite-runner is a local runner for executing [OGC TEAM Engine:material-open-in-new:]{: target="blank_" } (aka
teamengine). teamengine is the OGC application used for running test suites. As such, in order to use ogc-cite-runner,
you also need to have an instance of teamengine at hand.

One way of running teamengine is by pulling its [docker image:material-open-in-new:]{: target="blank_" } and
running it locally. You can achieve this by running:

```shell
docker pull ogccite/teamengine-production:1.0-SNAPSHOT
docker run \
    --rm \
    --name=teamengine \
    --add-host=host.docker.internal:host-gateway \
    --publish=9080:8080 \
    ogccite/teamengine-production:1.0-SNAPSHOT
```

!!! note

    Using docker's `--add-host=host.docker.internal:host-gateway` is only necessary when running bare docker engine,
    as discussed in the [docker engine docs:material-open-in-new:]{: target="blank_" }. If you are using docker
    desktop you can omit this flag.


This will spawn a teamengine instance, which will be running locally on port `9080` - it will thus be accessible
at:

<http://localhost:9080/teamengine>

!!! warning

    ogc-cite-runner has been implemented to work with the teamengine version that is used in
    the `ogccite/teamengine-production:1.0-SNAPSHOT` docker image as this is documented as
    being the same version used in the OGC production system.

    At the time of writing, this means **ogc-cite-runner is known to work with teamengine version
    5.6.1**.

    ogc-cite-runner has not been tested with other versions of teamengine.


## Usage

Once installed, ogc-cite-runner can be executed by calling the `ogc-cite-runner` application with a command
and suitable arguments.

```shell
ogc-cite-runner [OPTIONS] COMMAND [ARGS] ...
```

!!! tip

    The `--help` option can be used to discover how to use ogc-cite-runner interactively, like this:

    ```shell
    ogc-cite-runner --help
    ```

## Commands

### execute-test-suite

Execute a teamengine CITE test suite and get its result.

Results are serialized with the requested output format and are printed to the application's standard output stream,
which is usually the terminal. If needed, you can redirect the output to a file.

```shell
cite runner execute-test-suite [OPTIONS] TEAMENGINE_BASE_URL TEST_SUITE_IDENTIFIER
```


##### Arguments

- `TEAMENGINE_BASE_URL` - Base URL of the teamengine service. Example: `http://localhost:9080/teamengine`
- `TEST_SUITE_IDENTIFIER` - Identifier of the test suite as known to teamengine. Look up known identifiers in the
  [section on OGC test suites](ogc-test-suites.md). Example: `ogcapi-features-1.0`


##### Options

!!! warning "Specifying the URL of the OGC service being tested"

    Special care must be given with respect to specifying the URL of the OGC service which is being tested:

    1.  **The service is running on a public host** - If the OGC service is running on a public host, for example
        if you have a live demo instance, you can just refer to its public name. Example:

        ```shell
        ogc-cite-runner execute-test-suite \
            # other arguments
            --suite-input iut https://demo.pygeoapi.io/master
        ```

    1.  **The service is running on the same host** - When you are testing an OGC service which is running on
        the same host, you must not refer to the host as `localhost`, but rather as `host.docker.internal`. Example:

        ```shell
        # Assuming you have started the service to be tested and it is
        # running locally on port 5001
        ogc-cite-runner execute-test-suite \
            # other arguments
            --suite-input iut http://host.docker.internal:5001
        ```

        The reason for this is that the TeamEngine service that is started by ogc-cite-runner is running
        as a docker container and is only able to recognize the host as `host.docker.internal`. Check the
        [docker engine docs:material-open-in-new:]{: target="blank_" } for more detail.

| name | description |
| ---- | ----------- |
| `--help` | Show information on how to run the command, including a description of arguments and options |
| `--teamengine-username` | Username for authenticating with teamengine |
| `--teamengine-password` | Password for authenticating with teamengine |
| `--suite-input` | Inputs expected by teamengine for running the test suite specified with TEST_SUITE_IDENTIFIER. These vary depending on the test suite.<br><br>This parameter can be specified multiple times.<br><br>Each parameter must be specified as a name and a value, separated by the space character (_i.e._ `--suite-input {name} {value}`).<br><br>**Ensure you read the warning above on how to provide the URL of the service being tested.**<br><br>Example: `--suite-input iut http://host.docker.internal:5000 --suite-input noofcollections -1`|
| `--output-format` | Format for the ogc-cite-runner result. Available options are:<br><ul><li><code>console</code> - Return results in a format suitable for reading in the terminal - This is the default</li><li><code>json</code> - Return results as JSON. This is useful for piping the results to other commands for further processing.</li><li><code>markdown</code> - Return results as a Markdown document.</li><li><code>raw</code> - Return the raw results as provided by teamengine. This is an XML document.</li></ul>
| `--with-summary`/`--without-summary` | Whether the output should include a summary. This is enabled by default. Disable it by providing `--without-summary` |
| `--with-failed`/`--without-failed` | Whether the output should include a section with details about failed tests. This is disabled by default, enable it by providing `--with-failed`.|
| `--with-skipped`/`--without-skipped` | Whether the output should include a section with details about skipped tests. This is disabled by default, enable it by providing `--with-skipped`.|
| `--with-passed`/`--without-passed` | Whether the output should include a section with details about passed tests. This is disabled by default, enable it by providing `--with-passed`.|
| `--exit-with-error`/`--exit-without-error` | Whether the application should exit with an error code when a suite is declared as failed. This is enabled by default, disable it by providing `--exit-without-error`|


##### Examples

1. Run the test suite for OGC API Features, using a service that is running locally on port 5000 and then output just the
   result summary to the terminal:

    ```shell
    ogc-cite-runner execute-test-suite \
        http://localhost:9080/teamengine \
        ogcapi-features-1.0 \
        --suite-input iut http://host.docker.internal:5000
    ```

2. Run the test suite for OGC API Features using the [pygeoapi demo service:material-open-in-new:]{: target="blank_" } and then output the
   full report in Markdown format, redirecting the output to the `result.md` file:

    ```shell
    ogc-cite-runner execute-test-suite \
        http://localhost:9080/teamengine \
        ogcapi-features-1.0 \
        --suite-input iut https://demo.pygeoapi.io/stable \
        --suite-input noofcollections -1 \
        --with-failed \
        --with-skipped \
        --with-passed \
        --output-format markdown \
    > result.md
    ```

3. Run the test suite for OGC API Processes using a service that is running locally on port 5000 and then output the
   full report in JSON format, piping it to `jq` for further processing:

    ```shell
    ogc-cite-runner execute-test-suite \
        http://localhost:9080/teamengine \
        ogcapi-processes-1.0 \
        --suite-input iut http://host.docker.internal:5000 \
        --suite-input noofcollections -1 \
        --output-format json \
    | jq '.passed'
    ```


### parse-result

Parse previously gotten results from an earlier ogc-cite-runner run that used `raw` as its output format.

This command is most useful when you want to produce multiple reports in different output formats or with different
details from the same test run.

##### Arguments

-   `TEST_SUITE_RESULT` - Path to an XML file containing the raw execution results of a previous ogc-cite-runner run.
    You can also use a raw result file generated by teamengine, as long as it has been generated with the
    [teamengine EARL output format]. This can also be provided as the command's `stdin`, by using the special
    argument `-`, as in:

    ```shell
    ogc-cite-runner execute-test-suite \
        http://localhost:9080/teamengine \
        ogcapi-features-1.0 \
        --suite-input iut http://host.docker.internal:5000 \
    | ogc-cite-runner parse-result -
    ```


##### Options

Accepts a subset of similar [options as the execute-test-suite-command](#options)  namely:

- `--output-format`
- `--with-summary`/`--without-summary`
- `--with-failed`/`--without-failed`
- `--with-skipped`/`--without-skipped`
- `--with-passed`/`--without-passed`
- `--exit-with-error`/`--exit-without-error`


##### Examples

1. Parse a previously generated `raw-results.xml` file and output results for consumption in the terminal:

    ```shell
    ogc-cite-runner parse-result raw-results.xml
    ```

2. Run the OGC API Features test suite, then save the raw results in the `raw-results.xml` file and then parse
   them into a markdown report:

    ```shell
    RAW_RESULT_PATH=raw-results.xml

    ogc-cite-runner execute-test-suite \
        http://localhost:9080/teamengine \
        ogcapi-processes-1.0 \
        --suite-input iut http://host.docker.internal:5000 \
        --suite-input noofcollections -1 \
        --output-format raw
    > ${RAW_RESULT_PATH}

    ogc-cite-runner parse-result ${RAW_RESULT_PATH} \
        --with-failed \
        --with-skipped \
        --with-passed \
        --output-format markdown \
    > parsed-results.md

    ```


### execute-test-suite-from-github-actions

This command is merely a convenience for when executing ogc-cite-runner via github actions. When running ogc-cite-runner
as a standalone tool you should prefer to use the [execute-test-suite command](#execute-test-suite) instead

## Global options

ogc-cite-runner includes a couple of global options. These are mainly useful for debugging. They must to be provided
before the command.


| name | description |
| ---- | ----------- |
| `--debug`/`--no-debug` | Whether to run ogc-cite-runner in debug mode or not. Debug mode provides additional runtime information, which can be used during development. This is disabled by default, enable it by providing `--debug`|
| `--network-timeout` | How many seconds to use as the timeout parameter when contacting the teamengine service. The default value is `120` |

##### Examples

1. Run ogc-cite-runner in debug mode:

    ```shell
    ogc-cite-runner --debug parse-result raw-results.xml --output-format console
    ```


[docker engine docs:material-open-in-new:]: https://docs.docker.com/reference/cli/docker/container/run/#add-host
[docker image:material-open-in-new:]: https://hub.docker.com/r/ogccite/teamengine-production
[pygeoapi demo service:material-open-in-new:]: https://demo.pygeoapi.io/stable
[official docker documentation:material-open-in-new:]: https://docs.docker.com/engine/network/tutorials/host/#prerequisites
[OGC TEAM Engine:material-open-in-new:]: https://opengeospatial.github.io/teamengine/
[Python Package Index (PyPI):material-open-in-new:]: https://pypi.org/project/ogc-cite-runner/
[pipx:material-open-in-new:]: https://pypa.github.io/pipx/
[pip:material-open-in-new:]: https://pip.pypa.io/en/stable/
[teamengine EARL output format:material-open-in-new:]: https://opengeospatial.github.io/teamengine/users.html#EARL_.28RDF.2FXML.29
