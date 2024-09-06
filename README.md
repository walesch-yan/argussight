# Argussight
Argussight is a video processing tool, that allows you to run multiple different processes simultanuously from one single video stream.
Its core consists of two major components:
 - The `Collector`, which collects a video-stream from a redis database and updates internal shared data
 - The `Spawner`, a controlling system to start, manage and terminate running processes.

A gRPC server tightly connected to the `Spawner` allows communication with the outside world.

![Argussight-overview](https://github.com/user-attachments/assets/fb00a50a-a02d-4c27-acee-74fbe5f6a707)
