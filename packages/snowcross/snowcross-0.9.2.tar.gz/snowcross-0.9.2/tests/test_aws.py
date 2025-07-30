# pylint: disable=unused-import, unused-argument, redefined-outer-name, protected-access
import json
import logging
import re
from pathlib import Path

from mypy_boto3_ecr import ECRClient
from mypy_boto3_s3 import S3Client, S3ServiceResource
from mypy_boto3_ssm import SSMClient

import snowcross.aws
from tests import (
    TEST_AWS_ACCOUNT_ID,
    TEST_AWS_REGION,
    TEST_BUCKET_NAME,
    TEST_ECR_REPO_NAME,
    TEST_FILE_NAME,
    TEST_FILE_PATH,
    TEST_IMAGE_TAG,
    TEST_SPARK_JOB_NAME,
)
from tests.fixtures.aws import (
    aws_credentials,
    extract_job,
    fixture_ecr,
    fixture_ecr_client,
    fixture_ecr_image,
    fixture_file,
    fixture_s3_bucket,
    fixture_s3_client,
    fixture_s3_resource,
    fixture_ssm_client,
    fixture_sts_client,
    glue_client,
)

LOGGER = logging.getLogger(__name__)


# should return expected environment storage name.
def test_environment_storage_bucket(fixture_sts_client):
    environment = "test-env"
    assert (
        snowcross.aws.environment_storage_bucket(environment=environment, name=TEST_BUCKET_NAME)
        == f"{environment}-{TEST_BUCKET_NAME}-{TEST_AWS_ACCOUNT_ID}-{TEST_AWS_REGION}"
    )


# should return all expected parameter key-value pairs.
def test_resolve_parameters(fixture_ssm_client: SSMClient):
    parameters = {
        "test_1": {"ssm_name": "test/param/1", "value": "test1"},
        "test_2": {"ssm_name": "test/param/2", "value": "test2"},
        "test_3": {"ssm_name": "test/param/3", "value": "test3"},
    }

    for _, v in parameters.items():
        fixture_ssm_client.put_parameter(
            Name=v["ssm_name"],
            Description="test description",
            Value=v["value"],
            Type="String",
        )

    parameters_to_resolve = {k: f"boto+ssm:{v['ssm_name']}" for k, v in parameters.items()}

    res = snowcross.aws.resolve_parameters(parameters_to_resolve)

    for k, v in parameters.items():
        assert res[k] == v["value"]

    for _, v in parameters.items():
        fixture_ssm_client.delete_parameters(Names=[v["ssm_name"] for _, v in parameters.items()])


# should return the original value if not prefixed with boto+ssm:.
def test_resolve_parameters_non_ssm(fixture_ssm_client: SSMClient):
    non_ssm_parameters = {"test_1": "1", "test_2": "2"}
    res = snowcross.aws.resolve_parameters(non_ssm_parameters)

    for k, v in non_ssm_parameters.items():
        assert res[k] == v


# should return an empty dict if passed an empty dict.
def test_resolve_parameters_empty(fixture_ssm_client: SSMClient):
    empty_dict = {}
    res = snowcross.aws.resolve_parameters(empty_dict)

    assert res == empty_dict


# should return gracefully handle and log when an ssm prefixed parameter is invalid.
def test_resolve_parameters_invalid_param(fixture_ssm_client: SSMClient, caplog):
    caplog.set_level(logging.ERROR)
    parameters = {"test1": "boto+ssm:test/param/1", "test2": "boto+ssm:test/param/2"}
    res = snowcross.aws.resolve_parameters(parameters)
    assert res == parameters
    ssm_pattern = re.compile(r"^(boto\+)?ssm:")
    for _, parameter in parameters.items():
        assert f"Parameter not found: {ssm_pattern.sub(repl='', string=parameter)}" in caplog.text


# should get the streaming body of any s3 object
def test_get_storage_object(fixture_file):
    res = json.load(snowcross.aws.get_storage_object(bucket=TEST_BUCKET_NAME, key=TEST_FILE_NAME))
    assert res.get("test") == "test"


# should log if the object does not exist.
def test_get_storage_object_not_exists(fixture_file, caplog):
    caplog.set_level(logging.INFO)
    invalid_key = "invalid-key"
    snowcross.aws.get_storage_object(bucket=TEST_BUCKET_NAME, key=invalid_key)
    assert f"Object {invalid_key} not found" in caplog.text


# should upload a file to the s3 bucket and associate it with a specified key.
def test_upload_storage_object(fixture_s3_bucket, fixture_s3_client: S3Client):
    snowcross.aws.upload_storage_object(TEST_FILE_PATH, TEST_BUCKET_NAME, TEST_FILE_NAME)
    assert len(fixture_s3_client.get_object(Bucket=TEST_BUCKET_NAME, Key=TEST_FILE_NAME)) > 0


# should download a specified item from an s3_bucket to a local file.
def test_download_storage_object(fixture_file, tmp_path):
    download_path = Path(f"{tmp_path}/s3blobdownloadtest.txt")
    snowcross.aws.download_storage_object(
        bucket=TEST_BUCKET_NAME, key=TEST_FILE_NAME, filename=download_path
    )
    assert Path(download_path).is_file()


# should copy an item from 1 bucket to another bucket.
def test_move_storage_object(
    fixture_s3_client: S3Client, fixture_s3_resource: S3ServiceResource, fixture_file
):
    bucket_name_2 = f"{TEST_BUCKET_NAME}-2"
    fixture_s3_client.create_bucket(
        Bucket=bucket_name_2,
    )
    snowcross.aws.move_storage_object(
        from_bucket=TEST_BUCKET_NAME,
        from_key=TEST_FILE_NAME,
        to_bucket=bucket_name_2,
        to_key=TEST_FILE_NAME,
    )

    assert len(fixture_s3_client.get_object(Bucket=bucket_name_2, Key=TEST_FILE_NAME)) > 0

    fixture_s3_resource.Bucket(bucket_name_2).objects.all().delete()
    fixture_s3_client.delete_bucket(Bucket=bucket_name_2)


# should list all items within a bucket with a specified prefix.
def test_list_storage_objects(fixture_s3_client: S3Client):
    prefix_1 = "test_prefix"
    prefix_2 = "none_prefix"
    file_keys = [
        f"{prefix_1}/testfilekey",
        f"{prefix_1}/testfilekey2",
        f"{prefix_2}/testfilekey3",
    ]
    fixture_s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)
    for file_key in file_keys:
        fixture_s3_client.upload_file(TEST_FILE_PATH, TEST_BUCKET_NAME, file_key)
    assert (
        len(list(snowcross.aws.list_storage_objects(TEST_BUCKET_NAME, prefix_1))) == 2
        and len(list(snowcross.aws.list_storage_objects(TEST_BUCKET_NAME, prefix_2))) == 1
    )


# should parse an s3 scheme into objects.
def test_parse_storage_url_s3_scheme():
    obj = snowcross.aws.parse_storage_url(
        f"s3://{TEST_BUCKET_NAME}/prefix/schema/table/format/file.parquet"
    )
    assert obj["url"] == f"s3://{TEST_BUCKET_NAME}/prefix/schema/table/format/file.parquet"
    assert obj["bucket"] == TEST_BUCKET_NAME
    assert obj["key"] == "prefix/schema/table/format/file.parquet"


# should parse an s3a scheme into objects.
def test_parse_storage_url_s3a_scheme():
    obj = snowcross.aws.parse_storage_url(
        f"s3a://{TEST_BUCKET_NAME}/prefix/schema/table/format/file.parquet"
    )
    assert obj["url"] == f"s3a://{TEST_BUCKET_NAME}/prefix/schema/table/format/file.parquet"
    assert obj["bucket"] == TEST_BUCKET_NAME
    assert obj["key"] == "prefix/schema/table/format/file.parquet"


# should only parse the url for an invalid scheme.
def test_parse_storage_url_wrong_scheme():
    obj = snowcross.aws.parse_storage_url(
        f"http://{TEST_BUCKET_NAME}/prefix/schema/table/format/file.parquet"
    )
    assert obj["url"] == f"http://{TEST_BUCKET_NAME}/prefix/schema/table/format/file.parquet"
    assert "bucket" not in obj
    assert "key" not in obj


# should not parse anything from an empty scheme.
def test_parse_storage_url_none():
    obj = snowcross.aws.parse_storage_url(None)
    assert obj["url"] is None
    assert "bucket" not in obj
    assert "key" not in obj


# should get the SEMVER of the image tagged with latest.
def test_latest_image_version(fixture_ecr_image, fixture_ecr_client: ECRClient):
    latest_image_version = snowcross.aws.latest_image_version(
        registry_id=TEST_AWS_ACCOUNT_ID, repository_name=TEST_ECR_REPO_NAME
    )
    assert latest_image_version == TEST_IMAGE_TAG


def test_run_spark_job(glue_client, extract_job):
    run_id = snowcross.aws.run_spark_job(name=TEST_SPARK_JOB_NAME)
    job_run = glue_client.get_job_run(JobName=TEST_SPARK_JOB_NAME, RunId=run_id)
    assert job_run["JobRun"]["JobRunState"] == "SUCCEEDED"


def test_get_spark_job_state(glue_client, extract_job):
    run = glue_client.start_job_run(JobName=TEST_SPARK_JOB_NAME)
    assert snowcross.aws.get_spark_job_state(name=TEST_SPARK_JOB_NAME, run_id=run["JobRunId"])
