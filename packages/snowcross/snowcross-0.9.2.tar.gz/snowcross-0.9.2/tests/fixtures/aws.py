# pylint: disable=unused-import, unused-argument, redefined-outer-name, protected-access
import json
import os

import boto3
import botocore
import pytest
from moto import mock_aws
from mypy_boto3_ecr import ECRClient
from mypy_boto3_glue import GlueClient
from mypy_boto3_s3 import S3Client, S3ServiceResource
from mypy_boto3_ssm import SSMClient

from tests import (
    TEST_AWS_REGION,
    TEST_BUCKET_NAME,
    TEST_ECR_REPO_NAME,
    TEST_FILE_NAME,
    TEST_FILE_PATH,
    TEST_IMAGE_TAG,
    TEST_SPARK_JOB_NAME,
    TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT,
    TEST_SSM_PARAM_SNOWFLAKE_PASSWORD,
    TEST_SSM_PARAM_SNOWFLAKE_USERNAME,
)
from tests.helpers.docker import create_image_manifest


@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test_access_key_id"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test_secret_access_key"
    os.environ["AWS_SECURITY_TOKEN"] = "test_security_token"
    os.environ["AWS_SESSION_TOKEN"] = "test_session_token"
    os.environ["AWS_DEFAULT_REGION"] = TEST_AWS_REGION


@pytest.fixture(scope="module")
def fixture_sts_client(aws_credentials):
    with mock_aws():
        yield boto3.client("sts")


@pytest.fixture(scope="module")
def fixture_ssm_client(aws_credentials):
    with mock_aws():
        yield boto3.client("ssm")


@pytest.fixture(scope="module")
def fixture_s3_client(aws_credentials) -> S3Client:
    with mock_aws():
        yield boto3.client("s3")


@pytest.fixture(scope="module")
def fixture_ecr_client(aws_credentials):
    with mock_aws():
        yield boto3.client("ecr")


@pytest.fixture(scope="module")
def fixture_s3_resource(aws_credentials):
    with mock_aws():
        yield boto3.resource("s3")


@pytest.fixture(scope="module")
def glue_client(aws_credentials):
    with mock_aws():
        yield boto3.client(
            "glue",
            config=botocore.config.Config(
                retries={"mode": "adaptive"},
            ),
        )


@pytest.fixture(scope="function")
def extract_job(glue_client: GlueClient):
    job_name = TEST_SPARK_JOB_NAME
    glue_client.create_job(
        Name=job_name,
        Role="",
        Command={
            "Name": "test",
            "ScriptLocation": "test",
            "PythonVersion": "test",
            "Runtime": "test",
        },
    )
    yield
    glue_client.delete_job(JobName=job_name)


@pytest.fixture(scope="module")
def fixture_ecr(fixture_ecr_client: ECRClient):
    fixture_ecr_client.create_repository(repositoryName=TEST_ECR_REPO_NAME)
    yield
    fixture_ecr_client.delete_repository(repositoryName=TEST_ECR_REPO_NAME)


@pytest.fixture(scope="function")
def fixture_s3_bucket(fixture_s3_resource: S3ServiceResource, fixture_s3_client: S3Client):
    fixture_s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)
    yield
    fixture_s3_resource.Bucket(TEST_BUCKET_NAME).objects.all().delete()
    fixture_s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)


@pytest.fixture(scope="function")
def fixture_file(fixture_s3_bucket, fixture_s3_client: S3Client):
    fixture_s3_client.upload_file(
        Filename=TEST_FILE_PATH, Bucket=TEST_BUCKET_NAME, Key=TEST_FILE_NAME
    )
    yield
    fixture_s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=TEST_FILE_NAME)


@pytest.fixture(scope="function")
def fixture_ssm_params_snowflake(fixture_ssm_client: SSMClient):
    fixture_ssm_client.put_parameter(
        Name=TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT["name"],
        Type=TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT["type"],
        Value=TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT["value"],
    )
    fixture_ssm_client.put_parameter(
        Name=TEST_SSM_PARAM_SNOWFLAKE_PASSWORD["name"],
        Type=TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT["type"],
        Value=TEST_SSM_PARAM_SNOWFLAKE_PASSWORD["value"],
    )
    fixture_ssm_client.put_parameter(
        Name=TEST_SSM_PARAM_SNOWFLAKE_USERNAME["name"],
        Type=TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT["type"],
        Value=TEST_SSM_PARAM_SNOWFLAKE_USERNAME["value"],
    )
    yield
    fixture_ssm_client.delete_parameters(
        Names=[
            TEST_SSM_PARAM_SNOWFLAKE_ACCOUNT["name"],
            TEST_SSM_PARAM_SNOWFLAKE_PASSWORD["name"],
            TEST_SSM_PARAM_SNOWFLAKE_USERNAME["name"],
        ]
    )


@pytest.fixture(scope="function")
def fixture_ecr_image(fixture_ecr, fixture_ecr_client: ECRClient):
    image_manifest = create_image_manifest()
    for tag in ["latest", TEST_IMAGE_TAG]:
        fixture_ecr_client.put_image(
            repositoryName=TEST_ECR_REPO_NAME,
            imageManifest=json.dumps(image_manifest),
            imageTag=tag,
        )
    yield image_manifest
    fixture_ecr_client.batch_delete_image(
        repositoryName=TEST_ECR_REPO_NAME,
        imageIds=[{"imageDigest": image_manifest["config"]["digest"], "imageTag": TEST_IMAGE_TAG}],
    )
