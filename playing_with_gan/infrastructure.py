import os
import sys
import subprocess
import boto3
import sagemaker
import json
from . import paths


SOURCE_DIST_DIR = os.path.join(paths.TMP, "dist")


def build_source_distribution(output_dir=None, suppress_stdout=False):
    """
    Creates pip-installable .tar.gz archive by running python setup.py sdist over the project.
    Returns path to the created file.
    """
    if output_dir is None:
        output_dir = SOURCE_DIST_DIR
    subprocess.check_call(
        [
            sys.executable,
            os.path.join(paths.REPO_ROOT, "setup.py"),
            "sdist",
            "--dist-dir",
            output_dir,
        ],
        stdout=subprocess.DEVNULL if suppress_stdout else None,
        stderr=subprocess.STDOUT,
    )
    dist_filename = max(os.listdir(output_dir), key=_get_version)
    return os.path.join(output_dir, dist_filename)


def _get_version(dist_name):
    try:
        version_part = dist_name.rstrip(".tar.gz").rpartition("-")[2]
        return tuple(map(int, version_part.split(".")))
    except (ValueError, IndexError):
        return (-1,)


def get_source_distribution_s3_path(name):
    return os.path.join(paths.S3_SRC_BUILDS_ROOT, name + ".tar.gz")


def upload_source_distribution(name, local_path):
    s3_path = get_source_distribution_s3_path(name)
    boto3.Session(profile_name=paths.AWS_PROFILE).client("s3").upload_file(
        local_path, paths.S3_BUCKET, s3_path
    )
    return s3_path


def run_job(
    src_s3_path,
    entry_point_module,
    job_base_name,
    s3_output_path,
    instance_type,
    instance_count,
    max_run_time,
    allow_efs_write=False,
    wait=False,
):

    infrastructure_params = json.loads(
        subprocess.check_output("terraform output -json", shell=True)
    )

    ecr_image_url = infrastructure_params["worker_image_url"]["value"]
    role_arn = infrastructure_params["sagemaker_role_arn"]["value"]
    efs_id = infrastructure_params["efs_id"]["value"]
    security_group_id = infrastructure_params["security_group_id"]["value"]
    subnet_id = infrastructure_params["subnet_id_jobs"]["value"]

    api_session = sagemaker.Session(boto3.Session(profile_name=paths.AWS_PROFILE))
    estimator = sagemaker.estimator.Estimator(
        image_uri=ecr_image_url,
        role=role_arn,
        instance_count=instance_count,
        instance_type=instance_type,
        max_run=max_run_time,  # timeout for job to finish, otherwise it is stopped
        output_path=paths.S3_BUCKET_URL + s3_output_path,
        # checkpoint_s3_uri=paths.S3_BUCKET_URL + "checkpoints/" + model_name,
        base_job_name=job_base_name,
        hyperparameters={"entry_point": entry_point_module},
        use_spot_instances=True,
        max_wait=max_run_time,  # timeout for job including waiting for free spot instances
        enable_network_isolation=False,
        security_group_ids=[security_group_id],
        subnets=[subnet_id],
        sagemaker_session=api_session,
    )
    # noinspection PyTypeChecker
    estimator.fit(
        inputs={
            "training": sagemaker.inputs.FileSystemInput(
                file_system_id=efs_id,
                file_system_type="EFS",
                directory_path="/",
                file_system_access_mode="rw" if allow_efs_write else "ro",
            ),
            "code": paths.S3_BUCKET_URL + src_s3_path,
        },
        wait=wait,
    )
