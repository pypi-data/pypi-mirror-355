import luigi
from luigi_tasks.tasks.tasks import PrintTask
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    try:
        luigi.build(
            [PrintTask(message="Test message")],
            local_scheduler=False,
            scheduler_url="http://ae04168db8ba741ffb2d106170a40e99-419766040.us-east-1.elb.amazonaws.com:8082",
            workers=0,
            detailed_summary=True
        )
    except Exception as e:
        logging.error(f"Failed to run task: {str(e)}")
