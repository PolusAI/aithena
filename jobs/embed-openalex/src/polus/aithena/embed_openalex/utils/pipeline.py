"""Pipeline module to manage a sequence of asynchronous tasks."""

import asyncio
from typing import Any, Callable, Dict, Iterable
from polus.aithena.common.logger import get_logger

logger = get_logger(__name__)

class Step():
    """Pipeline Step.
    
    Each step is a processing unit that can be connected to other steps.
    Each step has an input queue and an output queue and executes a processing function on the input data.

    Args:
        id (int): Step identifier.
        workers (int): Maximum number of tasks to run in parallel.
        queue_size (int): Maximum size of the input queue.
        process (Callable): Processing function to apply to the input data.
    """
    id: int
    workers: list[asyncio.Task]
    queue_in: asyncio.Queue[Any]
    queue_out: asyncio.Queue[Any]
    process: Callable[[Any, Dict[str, Any]], Any]

    def __init__(self, id: int, workers_count: int, queue_size: int, process = lambda x: x) -> None:
        self.id = id
        self.workers = workers_count
        self.queue_in = asyncio.Queue(maxsize=queue_size)
        self.queue_out = None
        self.process = process

    def next(self, next_step : 'Step'):
        """Connect the output of this step to the input of the next step."""
        self.queue_out = next_step.queue_in

    async def run(self, kwargs):
        """Run the step."""
        while True:
            data = await self.queue_in.get()
            try:
                logger.debug(f"Step {self.id}, queue size: {self.queue_in.qsize()}. Processing data {data[0]}")
                res = await self.process(data, kwargs)
                if(self.queue_out is not None):
                    await self.queue_out.put(res)
                logger.debug(f'Step {self.id} completed for data : "{data[0]}"')
            except Exception as e:
                logger.error(f'Step {self.id} Data: [{data[0]}]. Exception: {e}')
            finally:
                self.queue_in.task_done()


class Pipeline(Step):
    """Pipeline run a set of steps.

    It is itself a step that can also be connected to other steps.
    
    Args:
        steps (list[Step]): List of steps to run.
            The first step input is the pipeline inputs.
            The last step output is the pipeline outputs.
        kwargs (dict): Arguments to pass to each processing step.
        on_result (Callable): Callback function to call when a pipeline output is produced.
    """
    steps: list[Step]

    def __init__(self, steps: list[Step], kwargs, on_result: Callable) -> None:
        """The pipeline is a sequence of steps that are executed in order.
        
        The first step is the input of the pipeline and the last step is the output of the pipeline.

        Args: 
            steps (list[Step]): List of steps to run.
            kwargs (dict): pipeline configuration to pass to each processing step.
            on_result (Callable): Callback function to call when a result is produced.

        Attributes:
            workers (list[list[asyncio.Task]]): available tasks for each step.
            queue_in (asyncio.Queue): input queue of the pipeline.
            queue_out (asyncio.Queue): output queue of the pipeline.
            final_output_task (asyncio.Task): task to process the output of the pipeline.
        """
        self.steps = steps
        self.workers = [[asyncio.create_task(step.run(kwargs)) for _ in range(step.workers)] for step in steps]
        self.queue_in = self.steps[0].queue_in
        self.queue_out = asyncio.Queue(self.steps[-1].queue_in.maxsize)
        self.steps[-1].queue_out = self.queue_out
        self.on_result = on_result
        self.final_output_task = asyncio.create_task(self.process_output(kwargs))

    async def start(self, data, all: bool = False):
        """Start the pipeline on the data.
        
        Each item in the data is put in the input queue of the first step.
        Data can be a list of items or an iterable of items.
        """
        if isinstance(data, Iterable):
            for start in data:
                end = min(data.stop, start + data.step)
                await self.queue_in.put((start,end))

    async def run_until_completed(self):
        """Run the pipeline until all steps are completed."""
        # Wait for all queues to be fully processed
        for step in self.steps:
            await step.queue_in.join()
        await self.queue_out.join()

        # Cancel all workers since there is no more item to process
        for step_workers in self.workers:
            for worker in step_workers:
                worker.cancel()
        self.final_output_task.cancel()
        await asyncio.gather(*[*[worker for step_workers in self.workers for worker in step_workers], self.final_output_task], return_exceptions=True)

    async def process_output(self, kwargs):
        """Process output of the pipeline."""
        while True:
            try:
                data = await self.queue_out.get()
                self.on_result(data, kwargs)
            except asyncio.CancelledError:
                break
            finally:
                self.queue_out.task_done()