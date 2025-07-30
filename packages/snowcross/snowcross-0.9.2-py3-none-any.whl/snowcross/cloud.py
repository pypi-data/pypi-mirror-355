import os
from importlib import import_module

_cloud = os.getenv("CLOUD")

# pylint: disable=wildcard-import,unused-wildcard-import
if _cloud == "aws" or not _cloud and import_module("boto3"):
    from .aws import *
else:
    raise ValueError(f"Unsupported cloud: {_cloud}")
