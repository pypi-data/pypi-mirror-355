# snowcross-python

Adaptors for tools and services in a Snowflake-centric data platform.

> **WARNING** While this repository is private, releases are published _publicly_ to 
> [PyPI](https://pypi.org/project/snowcross/)! All commits, pull requests and this readme are
> hidden, however the source code is easily extracted from published artifacts. Refrain from
> including any references to proprietary code, infrastructure or architecture. This package is
> for generic utilities for tools and services only.

## Usage

You can install from [PyPI](https://pypi.org/project/snowcross/):

```
pip install snowcross
```

Requires Python 3.10 or above.

## Cloud

Cloud provider functionality is abstracted for writing cloud-agnostic code.

For example, to install AWS:

```
pip install snowcross[aws]
```

For AWS-only code, you can import `aws` directly:

```python
import snowcross.aws

snowcross.aws.some_function()
```

For cloud-agnostic code, import `cloud` alias instead:

```python
import snowcross.cloud

snowcross.cloud.some_function()
```

Underlying implementation can be dynamically switched by setting `CLOUD` environment variable to
the package name. This currently defaults to `aws`.

### Supported Clouds

* AWS (`aws`)

## Locator

When using `locator` functionality, install extra dependencies `snowcross[locator]`.
