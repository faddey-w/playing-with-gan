import argparse
from my_project import infrastructure


def main():
    parser = argparse.ArgumentParser(
        description="Runs the simplest job - one instance, no intermediate checkpoints, no outputs."
        " In this example, it will download the dataset to EFS."
    )
    parser.parse_args()

    src_pkg_path = infrastructure.build_source_distribution(suppress_stdout=True)
    src_pkg_s3_path = infrastructure.upload_source_distribution(
        "cifar10/prepare_data", src_pkg_path
    )

    infrastructure.run_job(
        src_s3_path=src_pkg_s3_path,
        entry_point_module="my_project.cifar10_example.jobs.prepare_data",
        instance_count=1,
        instance_type="ml.m5.large",
        job_base_name="cifar10-prepare-data",
        max_run_time=3 * 3600,
        s3_output_path="nothing",
        allow_efs_write=True,  # we are going to save data to EFS
        wait=True,
    )


if __name__ == "__main__":
    main()
