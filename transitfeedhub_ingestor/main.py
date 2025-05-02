import os
import time

from dotenv import load_dotenv
from helpers.setup_logger import logger
from helpers.VehiclePositionFeed import VehiclePositionFeed

if __name__ == "__main__":  # pragma: no cover
    load_dotenv()
    api_key = os.getenv("API_KEY", "")
    provider = os.getenv("PROVIDER", "")
    feed_url = os.getenv("FEED_URL", "")
    s3_bucket = os.getenv("S3_BUCKET", "")

    logger.info(type(s3_bucket))
    x = VehiclePositionFeed(feed_url, provider, f"./data/{provider}", s3_bucket=s3_bucket, timeout=30)
    running = True
    while running:
        x.consume_pb()
        time.sleep(x.timeout)
