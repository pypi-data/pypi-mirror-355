import time


class Times:
    times: dict = {}

    def begin_time(self, id):
        self.times[id] = time.time()

    def end_time(self, id):
        self.times[id] = time.time() - self.times[id]

    def get_times(self):
        return self.times

    def print_times(self, logger=None):
        if logger is not None:
            logger.info(self.times)
        else:
            print(self.times)
