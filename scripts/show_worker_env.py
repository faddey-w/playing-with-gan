import argparse
from my_project import infrastructure


def main():
    parser = argparse.ArgumentParser(
        description="A minimal job that prints the file tree and environment"
        " in which the workers run. For debugging purposes."
    )
    parser.parse_args()

    src_pkg_path = infrastructure.build_source_distribution(suppress_stdout=True)
    src_pkg_s3_path = infrastructure.upload_source_distribution("show_worker_env", src_pkg_path)

    infrastructure.run_job(
        src_s3_path=src_pkg_s3_path,
        entry_point_module="my_project.show_worker_env_job",
        instance_count=1,
        instance_type="ml.m5.large",
        job_base_name="show-worker-env",
        max_run_time=30 * 60,
        s3_output_path="nothing",
        wait=True,
    )


if __name__ == "__main__":
    main()
