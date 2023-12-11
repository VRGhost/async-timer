# Async timer

This package provides an async timer object, that should have been part of batteries.

[![Tests](docs/badges/tests.svg)](docs/badges/tests.svg)
[![Coverage](docs/badges/coverage.svg)](docs/badges/coverage.svg)

[![CI](https://github.com/VRGhost/async-timer/actions/workflows/main.yml/badge.svg)](https://github.com/VRGhost/async-timer/actions/workflows/main.yml)

## Purpose

Sometimes, you need a way to make something happen over and over again at certain times, like updating information or sending reminders. That's where Async Timer comes in. It lets you set up these repeated actions easily.

This package is particularly useful for tasks like automatically updating caches in the background without disrupting the primary application's workflow.

## Features

* **Zero Dependencies**: Written entirely in Python, Async Timer operates independently without needing any external libraries.
* **Versatility in Callables**: It accommodates various callable types, including:
  * Synchronous functions
  * Asynchronous functions
  * Synchronous generators
  * Asynchronous generators
* **Wait for the Next Tick**: You can set it up so your program waits for the timer to do its thing, and then continues.
* **Keep Getting Updates**: You can use it in a loop to keep getting updates every time the timer goes off.

## Example Usage

```python

import async_timer

# Simple timer example
timer = async_timer.Timer(12, target=lambda: 42)
timer.start()
val = await timer.join()  # `val` will be 42 after 12 seconds

# Async for loop example
import time
with async_timer.Timer(14, target=time.time) as timer:
    async for time_rv in timer:
        print(f"{time_rv=}")  # Prints current time every 14 seconds

```