import threading
import time

class AgentScheduler:
    def __init__(self):
        self.tasks = []

    def add_task(self, interval, task_fn, args=None):
        if args is None:
            args = ()
        task = threading.Thread(target=self._run_task, args=(interval, task_fn, args))
        task.daemon = True  # Terminates with main program
        self.tasks.append(task)
        task.start()

    def _run_task(self, interval, task_fn, args):
        while True:
            task_fn(*args)
            time.sleep(interval)
