import logging
import re
import urllib
from typing import IO, Any, Dict, Generator, Literal, Optional, Union

import boto3
import botocore

from .errors import NotFoundError, ResourceExecutionError

logger = logging.getLogger(__name__)


def _client(
    service: Union[
        Literal["s3"],
        Literal["ssm"],
        Literal["ecr"],
        Literal["sts"],
        Literal["glue"],
    ],
) -> Any:
    """Creates a boto3 client for a service with default config.

    Args:
        service (str): The service to create a boto3 client for.

    Returns:
        any: A boto3 client instance.
    """
    return boto3.client(
        service,
        config=botocore.config.Config(
            retries={"mode": "adaptive"},
        ),
    )


def _resource(service: Literal["s3"]) -> Any:
    """Creates a boto3 resource client for a service with default config.

    Args:
        service (str): The service to create a boto3 resource client for.

    Returns:
        any: A boto3 resource client instance.
    """
    return boto3.resource(
        service,
        config=botocore.config.Config(
            retries={"mode": "adaptive"},
        ),
    )


def set_defaults(region: Optional[str] = None):
    """Sets AWS session defaults.

    Args:
        region (Optional[str]): Region name. Defaults to None.
    """
    boto3.setup_default_session(region_name=region)


def resolve_parameters(parameters: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    """Retrieves parameters from SSM.

    Args:
        parameters (Dict[Union[str, Optional[str]): Parameters by key (only those with ssm prefix are retrieved.)

    Returns:
        Dict[str, Optional[str]]: Same parameters with values resolved.
    """
    if len(parameters) == 0:
        return parameters

    ssm_parameters = {}
    for k, v in parameters.items():
        if not v:
            continue

        match = re.match(pattern=r"^(boto\+)?ssm:", string=v)
        if match:
            ssm_parameters[v[match.end() :]] = k

    if ssm_parameters:
        resp = _client("ssm").get_parameters(
            Names=list(ssm_parameters.keys()),
            WithDecryption=True,
        )
        for p in resp.get("InvalidParameters", []):
            logger.critical("Parameter not found: %s", p)

        for p in resp.get("Parameters", []):
            parameters[ssm_parameters[p["Name"]]] = p["Value"]

    return parameters


def get_parameter(name: str) -> Optional[str]:
    """Reads SSM parameter by name.

    Args:
        name (str): Parameter name.

    Returns:
        Optional[str]: Parameter value as string or none if not found.
    """
    try:
        ssm = _client("ssm")
        resp = ssm.get_parameter(Name=name, WithDecryption=True)
        return resp["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        logger.error("Parameter %s not found", name)
        return None


def set_parameter(name: str, value: str):
    """Writes SSM parameter.

    Args:
        name (str): Parameter name.
        value (str): Parameter value.
    """
    _client("ssm").put_parameter(Name=name, Value=value, Overwrite=True)


def environment_storage_bucket(environment: str, name: str) -> str:
    """Constructs environment-specific S3 bucket following convention.

    Args:
        environment (str): Environment name.
        name (str): Partial bucket name.

    Returns:
        str: Full bucket name.
    """
    account = _client("sts").get_caller_identity().get("Account")
    region = boto3.session.Session().region_name
    return f"{environment}-{name}-{account}-{region}"


def get_storage_object(bucket: str, key: str) -> Optional[IO]:
    """Retrieves body of an object stream from S3.

    Args:
        bucket (str): Bucket name.
        key (str): Object key.

    Returns:
        Optional[IO]: An S3 object body stream or None.
    """
    try:
        s3 = _client("s3")
        s3_object = s3.get_object(Bucket=bucket, Key=key)
        return s3_object["Body"]
    except s3.exceptions.NoSuchKey:
        logger.warning("Object %s not found", key)
        return None


def download_storage_object(bucket: str, key: str, filename: str):
    """Downloads S3 object to file.

    Args:
        bucket (str): Bucket name.
        key (str): Object key.
        filename (str): Target filename.
    """
    try:
        _resource("s3").Bucket(bucket).download_file(Key=key, Filename=filename)
    except botocore.exceptions.ClientError as ex:
        if ex.response["Error"]["Code"] in ("NoSuchKey", "404"):
            logger.warning("Object %s not found", key)
            raise NotFoundError() from ex
        raise ex


def upload_storage_object(filename: str, bucket: str, key: str):
    """Uploads file to S3 object.

    Args:
        filename (str): Source filename.
        bucket (str): Bucket name.
        key (str): Object key.
    """
    _client("s3").upload_file(Filename=filename, Bucket=bucket, Key=key)


def move_storage_object(from_bucket: str, from_key: str, to_bucket: str, to_key: str):
    """Moves S3 object and deletes original.

    Args:
        from_bucket (str): Source bucket name.
        from_key (str): Source object key.
        to_bucket (str): Target bucket name.
        to_key (str): Target object key.
    """
    s3 = _resource("s3")
    s3.Object(to_bucket, to_key).copy_from(CopySource={"Bucket": from_bucket, "Key": from_key})
    s3.Object(from_bucket, from_key).delete()


def list_storage_objects(bucket: str, prefix: str) -> Generator[str, None, None]:
    """Lists S3 objects under key prefix.

    Args:
        bucket (str): Bucket name.
        prefix (str): Object key prefix.

    Yields:
        Generator[str, None, None]: Object keys under the prefix.
    """
    s3 = _client("s3")
    kwargs = {"Bucket": bucket, "Prefix": prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            key = obj.get("Key")
            if key and not key.endswith("/"):
                yield key

        if resp.get("IsTruncated", False) and "NextContinuationToken" in resp:
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
        else:
            break


def parse_storage_url(url: str) -> Dict[str, str]:
    """Parses S3 URL (e.g. s3:// or s3a://) into object arguments.

    Args:
        url (str): Raw URL.

    Returns:
        Dict[str, str]: Same 'url' and if only valid, 'bucket' and 'key'.
    """
    obj = {"url": url}
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme in ("s3", "s3a"):
        obj["bucket"] = parsed.netloc
        obj["key"] = parsed.path.lstrip("/")
    return obj


def format_storage_url(bucket: str, key: str) -> str:
    """Generates S3 URL to bucket key (using s3:// schema).

    Args:
        bucket (str): Bucket name.
        key (str): Object key.
    """
    return f"s3://{bucket}/{key}"


def run_spark_job(name: str, properties: Optional[Dict[str, str]] = None) -> str:
    """Executes Spark job and return its run ID.

    Args:
        name (str): Job name.
        properties (Dict[str, str], optional): Run properties. Defaults to None.
    """
    if properties == None:
        properties = {}

    return (
        _client("glue")
        .start_job_run(
            JobName=name,
            Arguments=properties,
        )
        .get("JobRunId")
    )


def get_spark_job_state(name: str, run_id: str) -> bool:
    """Returns the state of the job.

    Args:
        name (str): Job name.
        run_id (str): Job run ID.

    Raises:
        ResourceExecutionError: If the job has failed.
    """
    job_run_resp = _client("glue").get_job_run(
        JobName=name,
        RunId=run_id,
    )
    state = job_run_resp.get("JobRun").get("JobRunState")

    if state == "SUCCEEDED":
        return True

    if state not in ("RUNNING", "STOPPING", "WAITING", "STARTING"):
        raise ResourceExecutionError(f"Job run returned: {state}")

    return False


def latest_image_version(registry_id: str, repository_name: str) -> str:
    """Gets the latest image version from ECR.

    Args:
        registry_id (str): The ECR registry id.
        repository_name (str): The ECR repository name.

    Returns:
        str: The latest image version. "" if no images exist.
    """
    iterator = (
        _client("ecr")
        .get_paginator("describe_images")
        .paginate(
            registryId=registry_id,
            repositoryName=repository_name,
            PaginationConfig={"PageSize": 1000},
        )
    )
    filter_iterator = iterator.search(
        "imageDetails[? imageTags!=null]|[?contains(imageTags,'latest')].imageTags"
    )
    latest_image_tags = ",".join([tag for tag in filter_iterator][0])
    version_match = re.search(r"\d*\.\d*\.\d*", latest_image_tags)
    return version_match.group(0) if version_match else ""
