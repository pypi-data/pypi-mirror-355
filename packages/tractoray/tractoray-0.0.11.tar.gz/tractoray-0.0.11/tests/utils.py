import random
import string
import time


FAT_DOCKER_IMAGE: str = (
    "cr.eu-north1.nebius.cloud/e00faee7vas5hpsh3s/tractoray/tests:2025-04-11-18-47-50-8e9b4e9b2"
)
SLIM_DOCKER_IMAGE: str = (
    "cr.eu-north1.nebius.cloud/e00faee7vas5hpsh3s/tractoray/slim_tests:2025-04-11-22-15-39-76a64a297"
)
DOCKER_IMAGE = SLIM_DOCKER_IMAGE


def get_random_string(length: int) -> str:
    return (
        str(int(time.time()))
        + "_"
        + "".join(random.choice(string.ascii_letters) for _ in range(length))
    )
