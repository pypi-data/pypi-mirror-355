# mp-cron-parser

A lightweight cron expression parser for [MicroPython](https://micropython.org/) and Python.  
Perfect for task scheduling and timers in embedded, IoT, and microcontroller projects.
---
## Installation

`mpremote mip install github:aviram26/mp-cron-parser`

---
## Features

- **Standard cron syntax:** 5 fields—minute, hour, day, month, day-of-week (`min hour dom mon dow`)
- **Human-friendly aliases:** Supports `@yearly`, `@monthly`, `@weekly`, `@daily`, `@hourly`
- **Supports ranges, steps, and lists:** (e.g. `0-30/5`, `MON-FRI`, `JAN,JUN,DEC`)
- **Strict minimalism:** No dependencies except for Python’s standard `time` module
- **Rejects non-standard extensions:** (`L`, `W`, `#`) for smaller and safer code
- **Returns the next run time after any given timestamp**
- **Requires only the `time` standard module**

---

## Supported Syntax

| Field   | Allowed values        | Aliases            | Example        |
| ------- | --------------------- | ------------------ | -------------- |
| minute  | 0–59, `*`, `,`, `-`, `/`   | -                | `0,15,30,45`   |
| hour    | 0–23, `*`, `,`, `-`, `/`   | -                | `8-18/2`       |
| day     | 1–31, `*`, `,`, `-`, `/`   | -                | `1,15,29`      |
| month   | 1–12, `*`, `,`, `-`, `/`   | JAN–DEC          | `JAN,JUN,DEC`  |
| weekday | 0–7, `*`, `,`, `-`, `/`    | SUN–SAT (0 or 7) | `MON-FRI`      |

**Special Aliases:**

| Alias     | Equivalent     |
|-----------|---------------|
| `@yearly` | `0 0 1 1 *`   |
| `@monthly`| `0 0 1 * *`   |
| `@weekly` | `0 0 * * 0`   |
| `@daily`  | `0 0 * * *`   |
| `@hourly` | `0 * * * *`   |

**Note:** Non-standard cron features such as `L`, `W`, and `#` are _not_ supported and will raise a `ValueError`.

---
## Error Handling
Any cron expression that uses unsupported features or is malformed will raise a clear `ValueError`.

---

## Usage
Here is a simple example demonstrating how to use `mp-cron-parser` to schedule and compute the time of the next scheduled job:

```python
from cron_parser import Cron


cron = Cron('0 17 */2 * *')
n = cron.next_run()
```
---
## License
Licensed under the [MIT License](http://opensource.org/licenses/MIT).
