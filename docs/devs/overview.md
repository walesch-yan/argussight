# Architectural Overview

`Argussight` is built around four key components, each playing a vital role in its functionality.

- [Spawner](./spawner.md): The core of `Argussight`, responsible for controlling, spawning and terminating video processes.

- [GRPC Server](../usage/grpc.md): Thightly connected to the `Spawner`, it handles the communication with a client application.

- [Video processes](../usage/processes.md): Processes that are each running a specific video-related task, like generating or modifying camera streams.

- [Stream-Layer](./video-layer.md): An abstraction layer positioned between **streaming** processes and external systems. This layer simplifies access to the streams while enhancing security through port abstraction.

![Argussight Overview](../images/Overview.svg)

---

## Connecting to other Applications

The following section is explained in more detail in our [Setup](../usage/setup.md) section.

To connect Argussight to your application, you need to establish a connection via the integrated [GRPC server](../usage/grpc.md) for communication between both application and real-time stream modifications and process handling. The created streams can be accessed via websocket connection to the integrated [Abstraction-Layer](./video-layer.md).

### Connecting Streams to Processes

To add [video processes](../usage/processes.md) to your streams, you need to create [Redis Pub/Sub](https://redis.io/docs/latest/develop/interact/pubsub/) channels as input to the processes. For a full explanation on how to connect the input streams to the processes, check out the [Vprocess](./vprocess.md) class and our [Configurations](../usage/configurations.md) section.

We recommend using [MXCuBE's Video-Streamer](https://github.com/mxcube/video-streamer) to start a [Redis Pub/Sub](https://redis.io/docs/latest/develop/interact/pubsub/) Channel from any camera device or stream.

---

## Benefits of Source Obfuscation

The introduction of the [Abstraction-Layer](./video-layer.md) allows source obfuscation for streams, this has the following benefits:

- **Enhanced Security**: Prevents unauthorized access to the stream sources by exposing only the abstraction layer's port.
- **Simplified Client Configuration**: Clients need only the abstraction layer's port and endpoint, reducing configuration complexity.
- **Stream Source Independence**: Allows changes to stream sources without requiring client-side updates.
