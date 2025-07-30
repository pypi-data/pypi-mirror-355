# Core-Py

## Example

### Prerequisites

#### Install smcore

```bash
pip install smcore
```

#### Get the address of a blackboard to talk to

If you don't have an address already (something like `bb.myhost.com:8080` or
`bb.host.com`), you can install the core tool and run your own locally.

```
go install gitlab.com/hoffman-lab/core@latest
core start server
```

The default address when running locally is `localhost:8080`

This is great for debugging and getting started.  The `core` tool also has
other good stuff.

### Use an agent to post data

```python
from smcore import agent
from smcore import hardcore

bb_addr = "localhost:8080"

async def main():
  bb = hardcore.HTTPTransit(bb_addr)
  a = agent.Agent(bb)
  

  for i in range(n_messages):
    metadata=b"hello"
    data=b"world"
    tags = ["upload-test", str(i)]
    await a.post(metadata, data, tags)
  
if __name__=="__main__":
  asyncio.run(main())
```

### Use an agent to listen for data

```python
from smcore import agent
from smcore import hardcore

bb_addr = "localhost:8080"

async def main():
  bb = hardcore.HTTPTransit(bb_addr)
  a = agent.Agent(bb)

  # Listen for messages matching the listed tags
  in_queue = a.listen_for(["important","segmentation"])

  # listening is an active process and must be started.
  # although listen_for can be called after start it is 
  # best practice to make all calls in advance.
  # 
  task = a.start()
  while True:
    post = await in_queue.get()
    await a.reply([post], None, None, ["received!"])
  
  # The started coroutine for listening can be cancelled normally
  task.cancel()

if __name__=="__main__":
  asyncio.run(main())
```

### (De)serialization

Serialization is the process of converting abstract structures into
binary-encodable formats for saving and sharing.  Common language allows agents to
communicate.

```python

from smcore import serialize, deserialize

data = serialize.file("path/to/file.ext")
deserialize.file(data, "path/to/new/file.ext")

data = serialize.numpy(np.random.random((512,512,1)))
array = deserialize.numpy(data)
```

The `serialize/deserialize` modules give you some basics to get started.

These allow you to easily set data and metadata in your posts:

```python
bb = hardcore.HTTPTransit(bb_addr)
post = bb.message_post()

fp_to_upload = "data/for/sharing/file.ext"
post.set_data(serialize.file(fp_to_upload))
post.set_metadata(serialize.dictionary({"path": fp_to_upload}))
```

You can decode it in other agents using the paired `deserialize` function:

```python

post = await incoming.get()

finfo = deserialize.dictionary(post.metadata())
deserialize.file(post.data(), finfo["path"])
```

## Motivation

The main [core]() repo is getting a little unwieldy.  CI/CD and organization could
benefit from giving the python API for Core a little breathing room.

## Short term goals

1. Get the Python API updated to utilize the hardcore protocol
2. Debug the message stoppage issue @mattbrown7 has identified
3. Discuss, enumerate, and begin prototyping key tests to validate that the Core
API fulfills its contract

## Long term goals

- Resilient CI/CD that runs tests in real world conditions
- Shared maintenance of the Python API with other developers
