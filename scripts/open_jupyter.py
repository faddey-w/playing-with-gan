import argparse
import time
import webbrowser
import boto3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=["small"])
    args = parser.parse_args()

    session = boto3.Session(profile_name="sagemaker_project_template")
    client = session.client("sagemaker")

    instance = client.describe_notebook_instance(NotebookInstanceName=args.name)

    if instance["NotebookInstanceStatus"] != "InService":
        if instance["NotebookInstanceStatus"] != "Pending":
            client.start_notebook_instance(NotebookInstanceName=args.name)
        while True:
            time.sleep(10)
            instance = client.describe_notebook_instance(NotebookInstanceName=args.name)
            state = instance["NotebookInstanceStatus"]
            if state != "InService":
                print("instance state:", state)
                if state == "Failed":
                    print("reason:", instance["FailureReason"])
                    exit(1)
            else:
                break

    url = client.create_presigned_notebook_instance_url(NotebookInstanceName=args.name)
    webbrowser.open(url["AuthorizedUrl"])


if __name__ == "__main__":
    main()
