import os
import playing_with_gan


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(playing_with_gan.__file__)))


TMP = os.path.join(REPO_ROOT, "tmp")


AWS_PROFILE = "playing_with_gan"

S3_BUCKET = "playing-with-gan"
S3_BUCKET_URL = "s3://" + S3_BUCKET + "/"

S3_SRC_BUILDS_ROOT = "src-builds"
