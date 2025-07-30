import logging
import queue
import threading
from abc import abstractmethod, ABC


class ProcessExitSignal(object):
    pass


class MessagePump(ABC):
    def __init__(self, thread_name: str):
        self.logger = logging.getLogger(f"{__class__.__name__}[{thread_name}]")
        self.message_queue = queue.Queue()
        self.pump_thread = threading.Thread(target=self.process_messages, name=thread_name, daemon=True)
        self.pump_thread.start()

    def post_message(self, message):
        self.message_queue.put_nowait(message)

    def process_messages(self):
        self.logger.info(f'Message pump on thread [{threading.current_thread().name}] started.')
        while True:
            message = self.message_queue.get()  # This will block until a message is available
            if isinstance(message, ProcessExitSignal):
                break
            else:
                try:
                    self.handle_message(message)
                except:
                    self.logger.exception('Error processing message')

    @abstractmethod
    def handle_message(self, message):
        pass

    def set_process_exit(self):
        self.message_queue.put(ProcessExitSignal())
