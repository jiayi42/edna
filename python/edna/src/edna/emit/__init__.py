from __future__ import annotations
from typing import Dict
from edna.types.enums import EmitPattern
from edna.serializers import Serializable, EmptySerializer
import time
from edna.core.primitives import EdnaPrimitive

class BaseEmit(EdnaPrimitive):
    """BaseEmit is the base class for writing records from a process primitive to a sink, 
    such as a filestream, sql database, or Kafka topic.

    Any child class must:

    - Implement the `write()` method. The write method will write all messages in the `self.emit_buffer` variable.
        `self.emit_buffer` is a List of Serialized messages

    - Call `super().__init__()` at the end of initialization
    
    Child classes should NOT:

    - modify the `__call__()` method

    Attributes:
        emit_pattern (EmitPattern): The type of emit, either STANDARD_EMIT or BUFFERED_EMIT
    """
    emit_pattern: EmitPattern = EmitPattern.STANDARD_EMIT
    def __init__(self, serializer: Serializable = EmptySerializer(), 
            in_serializer: Serializable = None, 
            out_serializer: Serializable = None, 
            emit_buffer_batch_size: int = 10, 
            emit_buffer_timeout_ms: int = 100, 
            logger_name: str = None,
            *args, **kwargs):
        """Initializes the BaseEmit. This must be called by any inheriting classes using `super().__init__()`

        Args:
            serializer (Serializable): Serializer to use during emitting a record.
            emit_batch_size (int): How many items to emit at a time. Emit will collect 
                records until it has at least `emit_batch` records, then perform a write. 
                TODO Update this to byte size, instead
            emit_timeout_ms (int): How many ms to wait before emitting. This is to prevent 
                blocking on unfilled `emit_batch` if incoming stream is slow.
        """
        if logger_name is None:
            logger_name = self.__class__.__name__
        if serializer is None:
            serializer = EmptySerializer()
        super().__init__(serializer=serializer, in_serializer=in_serializer, out_serializer=out_serializer, logger_name=logger_name)


        if emit_buffer_batch_size <= 0:
            raise ValueError("emit_buffer_batch_size must be positive; received {emit_buffer_batch_size}".format(emit_buffer_batch_size = emit_buffer_batch_size))
        self.emit_buffer_batch_size = emit_buffer_batch_size
        self.emit_buffer = [None]*self.emit_buffer_batch_size
        self.emit_buffer_timeout_s = float(emit_buffer_timeout_ms) / 1000.
        self.emit_buffer_index = -1
        self.timer = time.time()
        
        

    def __call__(self, message):
        """Wrapper for emitting a record using the emitter's logic. This is the entry point for emitting and should not be modified.

        Args:
            message (List[object]): A list of message that should be Serializable to bytes with `serializer`
        """
        for item in message:
            self.call(item)
        
    def call(self, message):
        """Writes records to the internal buffer.

        Args:
            message (obj): A record.
        """
        self.emit_buffer_index += 1
        self.emit_buffer[self.emit_buffer_index] = self.out_serializer.write(message)
        # Write buffer and clear if throughput barriers are met
        self.checkBufferTimeout()
        self.checkBufferSize()
        

    def checkBufferTimeout(self):
        """Check if the buffer has timed out and flushes them.
        """
        if (time.time() - self.timer) > self.emit_buffer_timeout_s:    # Buffer timeout reached
            self.flush()

    def checkBufferSize(self):
        """Checks if the buffer is full and flushes them.
        """
        if self.emit_buffer_index+1 == self.emit_buffer_batch_size: # Buffer too large
            self.flush()

    def write_buffer(self):
        """Calls `write()` to write the buffer and resets the buffer"""
        self.write()
        self.reset_buffer()
    
    def reset_buffer(self):
        """Resets the internal buffer."""
        self.emit_buffer_index = -1
        self.emit_buffer = [None]*self.emit_buffer_batch_size
        self.timer = time.time()


    def write(self):        # For Java, need Emit to be a templated function for message type
        """Writes serialized messages. This should be implemented by inheriting classes to emit with the appropriate logic.
        Subclasses will write messages in the `emit_buffer` of the class. 

        Subclasses will also need to handle cases where the `emit_buffer` is not full by checking with `self.emit_buffer_index`.

        Raises:
            NotImplementedError: `write()` needs to be implemented in inheriting subclasses.
        """
        raise NotImplementedError()

    def flush(self):
        """Flushes the buffers and emits current contents
        """
        self.write_buffer()

    def build(self, build_configuration: Dict[str, str]):
        """Lazy building

        Args:
            build_configuration (Dict[str, str]): The build configuration.
        """
        pass

    def close(self):
        """Shutdown emit, including closing any connections if they have been made
        """
        pass

from .KafkaEmit import KafkaEmit
from .StdoutEmit import StdoutEmit
from .SQLEmit import SQLEmit
from .SQLUpsertEmit import SQLUpsertEmit
from .RecordCounterEmit import RecordCounterEmit

__pdoc__ = {}
__pdoc__["BaseEmit.__call__"] = True


