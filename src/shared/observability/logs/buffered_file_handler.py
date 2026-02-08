import logging
from logging.handlers import BufferingHandler


class BufferedFileHandler(BufferingHandler):
    def __init__(self, filename: str, buffer_capacity: int = 100):
        super().__init__(buffer_capacity)

        self.target = logging.FileHandler(filename, mode='a')

    def flush(self):
        self.acquire()
        try:
            if self.buffer:
                for record in self.buffer:
                    self.target.handle(record)
                self.buffer.clear()
        finally:
            self.release()

    def close(self):
        self.flush()
        self.target.close()
        super().close()
