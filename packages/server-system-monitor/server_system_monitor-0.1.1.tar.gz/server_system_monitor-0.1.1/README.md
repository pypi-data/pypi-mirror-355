# Server System Monitor

This is package can monitor a server ping, CPU and memory using SSH, but in a short time it will be able to monitor disk usage.

All of the methods are wrappers to common Linux commands like:

```python
Monitor.from_user_password("example.com","pwd","user").server_client.send_ram()
```

is the same as:

```shell
ssh user@example.com "free"
```

## Commands and wrappers

`ConnectionMonitor` wrappers:

| command | wrapper  |
| ------- | -------- |
| ping    | get_ping |

`ServerClientMonitor` wrappers:

| command | wrapper  |
| ------- | -------- |
| free    | send_ram |
| mpstat  | send_cpu |

## Quick usage

For monitoring connection specs and server's system specs at the same time you can use the `Monitor` object:

```python
from server_system_monitor import Monitor

monitor = Monitor.from_user_password("example.com","pwd","user")

ram = monitor.server_client.send_ram()

ping = monitor.connection.get_ping()

print(ram)
print(ping)
```

But if only one is necessary you can use `ConnectionMonitor` (for connection specs) or `ServerClientMonitor` (for server specs):

```python
from server_system_monitor import ServerClientMonitor,ConnectionMonitor

server_client_monitor = ServerClientMonitor.from_user_password("example.com","pwd","user")

connection_monitor = ConnectionMonitor("example.com")

ram = server_client_monitor.send_ram()

ping = connection_monitor.get_ping()

print(ram)
print(ping)
```

## License

The server-system-monitor library is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).
