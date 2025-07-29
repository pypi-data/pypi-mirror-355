# Foxglove Python SDK

## Requirements

- Python 3.9+

### Examples

To get started, install Poetry https://python-poetry.org/docs/#installation, and then the project dependencies. For example:

```sh
pipx install poetry
poetry install
```

Examples are available in [foxglove-sdk-examples](https://github.com/foxglove/foxglove-sdk/tree/main/python/foxglove-sdk-examples).

## Overview

To record messages, you need at least one sink and at least one channel.

A "sink" is a destination for logged messages — either an MCAP file or a live visualization server.
Use `open_mcap` to register a new MCAP sink. Use `start_server` to create a new live visualization
server.

A "channel" gives a way to log related messages which have the same schema. Each channel is
instantiated with a unique topic name.

The SDK provides classes for well-known schemas. These can be used in conjunction with associated
channel classes for type-safe logging, which ensures at compile time that messages logged to a
channel all share a common schema. For example, you may create a `SceneUpdateChannel` on which you
will log `SceneUpdate` messages.

You can also log messages with arbitrary schemas and provide your own encoding, by instantiating a
`Channel` class.

See the examples for more details.
