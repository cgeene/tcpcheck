 
#!/usr/bin/env python3
"""
TCP connectivity check 
Usage: ./flappy-ports.py port [file]
"""

import sys
import socket
import time
import signal
import asyncio
import functools

MAX_ATTEMPTS = 5
WAIT_TIME = .2 # seconds 
NUM_WORKERS = 5 # could easily be up to 250

# Required Port
try:
    port = sys.argv[1]
except IndexError:
    print("Usage: flappy-ports.py port [file...]")
    sys.exit(1)


async def worker(name, queue): 
    while True: 
        host = await queue.get()
        try:
            await test_host(port, host)
            queue.task_done()
        except asyncio.CancelledError: 
            print("CANCELLED!!!!!")
            break
    asyncio.get_event_loop().stop()


async def test_host(port, host, attempts=0, failures=0): 
    if attempts == MAX_ATTEMPTS: 
        if failures == 0:
            print("Host: {} is up".format(host))
            # return
        elif failures == attempts: 
            print("Host: {} is down".format(host))
        else:
            print("Host: {} is flappy".format(host))
        return

    s = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)

    try:
        await asyncio.get_event_loop().sock_connect(s, (host, int(port)))
        await asyncio.sleep(WAIT_TIME)
        await test_host(port, host, attempts + 1, failures)
    except Exception:
        await asyncio.sleep(WAIT_TIME)
        await test_host(port, host, attempts + 1, failures + 1)


tasks = []
async def main(): 
    loop = asyncio.get_event_loop()

    queue = asyncio.Queue()
    line = sys.stdin.readline()
    for i in range(NUM_WORKERS): 
        tasks.append(
            asyncio.create_task(worker(f'worker-{i}', queue))
        )

    while line: 
        if len(line) > 1:
            queue.put_nowait(line.strip())
        line = sys.stdin.readline()
    await queue.join()
    
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

asyncio.run(main())