import argparse
from my_project import infrastructure, paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args()

    dist_local_file = infrastructure.build_source_distribution()
    infrastructure.upload_source_distribution(args.name, dist_local_file)
    print(paths.S3_BUCKET_URL + infrastructure.get_source_distribution_s3_path(args.name))


if __name__ == "__main__":
    main()
