import os
import time

import ray


@ray.remote(scheduling_strategy="SPREAD")
def remote_task(i: int) -> str:
    time.sleep(2)
    assert os.environ["ENV_VAR_1"] == "VALUE_1"
    assert os.environ["ENV_VAR_2"] == "VALUE_2"
    return f"Task {i} has been completed on host {ray.get_runtime_context().node_id}"


tasks = [remote_task.remote(i) for i in range(10)]

results = ray.get(tasks)
for result in results:
    print(result)
