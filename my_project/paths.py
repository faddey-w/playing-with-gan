import os
import my_project


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(my_project.__file__)))


TMP = os.path.join(REPO_ROOT, "tmp")


AWS_PROFILE = "sagemaker_project_template"

S3_BUCKET = "sagemaker-project-template"
S3_BUCKET_URL = "s3://" + S3_BUCKET + "/"

S3_SRC_BUILDS_ROOT = "src-builds"
