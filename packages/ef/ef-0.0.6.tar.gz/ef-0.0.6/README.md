# ef
An example of connecting the flush of one buffer to the push of another.

To install:	```pip install ef```

## Overview
The `ef` package provides a comprehensive suite of tools designed to handle data buffering operations efficiently. This includes the ability to chain buffers together, where the output (flush) of one buffer can be directed as input (push) to another, facilitating complex data processing pipelines. The package includes various buffer implementations, such as threshold-based buffers, routers, and wrappers that allow for flexible buffer operations.

## Key Features
- **Threshold Buffers**: Automatically flush data based on a predefined condition.
- **Router and Pipeline Buffers**: Enable routing of data through multiple buffer stages or in parallel to multiple buffers.
- **Buffer Wrappers**: Enhance buffers with additional functionality like pre-push processing or post-flush handling.
- **Bucket Buffer**: Organizes data into buckets based on specified criteria, useful for time-segmented data accumulation.

## Usage Examples

### Basic Buffer Operations
```python
from ef import ThreshBuffer

# Create a buffer that flushes when it has 3 items
buffer = ThreshBuffer(thresh=3)
buffer.push(1)
buffer.push(2)
print(buffer.push(3))  # This will flush the buffer and print [1, 2, 3]
```

### Chaining Buffers
```python
from ef import ThreshBuffer, BufferPipeline

# Define custom flush behavior
class SumBuffer(ThreshBuffer):
    def _flush(self):
        total = sum(self._buf)
        self._buf = []
        return total

# Create a pipeline of buffers
buffer_a = SumBuffer(thresh=2)
buffer_b = SumBuffer(thresh=3)
pipeline = BufferPipeline(buf_list=[buffer_a, buffer_b])

# Push data through the pipeline
for i in range(5):
    pipeline.push(i)

# Flush all remaining data in the pipeline
print(pipeline.flush())  # Output will be the sum of all pushed items
```

### Using Bucket Buffers
```python
from ef import BucketBuffer

# Create a buffer that accumulates data in time-based buckets
bucket_buffer = BucketBuffer(thresh=2, index_field='time', bucket_step=10)
bucket_buffer.push({'time': 5, 'value': 'data1'})
bucket_buffer.push({'time': 15, 'value': 'data2'})
print(bucket_buffer.flush())  # Flushes the earliest bucket if threshold is reached
```

### Router Example
```python
from ef import Router, ThreshBuffer

# Define simple buffers
buffer1 = ThreshBuffer(thresh=2)
buffer2 = ThreshBuffer(thresh=2)

# Create a router to push items to both buffers
router = Router([buffer1, buffer2])

# Push data
router.push(1)
router.push(2)  # This will cause both buffers to flush

# Flush the router (note: router flush typically returns None)
router.flush()
```

## Documentation
- **`ThreshBuffer`**: A buffer that flushes based on a threshold condition.
- **`Router`**: Manages a list of buffers and routes pushed items to each buffer.
- **`BufferPipeline`**: A sequential chain of buffers where the output of one buffer is pushed to the next.
- **`BucketBuffer`**: Organizes pushed items into buckets based on specified criteria, flushing when buckets reach a threshold size.

For more detailed examples and advanced usage, refer to the docstrings provided within the code. Each class and function is equipped with a detailed explanation of its purpose and usage.