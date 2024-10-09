import logging

import torch

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def find_available_gpu(min_mem: int = 8 * 10**9):
    """Find gpus with enough free memory.

    Args:
        min_mem: the minimum memory that should be free on the device. Default to 8Gb.
    """
    for device_id in range(torch.cuda.device_count()):
        _, free = get_gpu_free_memory(device_id)
        if free > min_mem:
            yield device_id


def get_gpu_free_memory(device_id):
    t = torch.cuda.get_device_properties(device_id).total_memory
    a = torch.cuda.memory_allocated(device_id)
    free = t - a
    free2, _ = torch.cuda.mem_get_info(device_id)
    return free, free2


def print_gpu_info(device_id):
    free, free2 = get_gpu_free_memory(device_id)
    logger.debug(
        f"gpu {device_id} - estimated free memory 1: {free/1024**2} MB, estimated free memory 2: {free2/1024**2}MB",
    )
