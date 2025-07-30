# **ltoolboxLib**

*A Swiss Army knife for Python scripting and automation*

[![PyPI version](https://badge.fury.io/py/ltoolboxlib.svg)](https://pypi.org/project/ltoolboxLib/)

`ltoolboxLib` is a powerful utility library for Python that simplifies file operations, text manipulation, encoding, system tasks, and more, with built-in **sandbox mode** for safe testing.

---

## **Features**

* **File Operations** - Read, write, copy, grep, and manage files (with sandbox support).
* **Dynamic Strings** - `S()` and `M()` for runtime string interpolation.
* **Encoding/Decoding** - Secure `encode()`/`decode()` with shadow keys.
* **System Utilities** - Cross-platform notifications, clipboard access, and public IP fetching.
* **ANSI Styling** - RGB colors and text formatting for terminals.
* **Sandbox Mode** - Virtual filesystem for testing without touching real files.
* **Smart Functions** - Fuzzy matching, random generators, UUIDs, and more.
* **Temporary Variables** - Values that expire over time, after use, or permanently transform.
* **Debugging Tools** - Tracebacks, watches, pauses, and safe evaluations.
* **Utility Classes** - Including `Toggle`, `Undo`, and `Lock` for stateful logic and memory control.
* **Discord Message Simulation** - For when you want to test out a discord bot, but without actually making one.

---

## **Quick Start**

### **1. File Operations (Sandbox Supported)**

```python
from ltoolboxLib import *

debug.sandbox(True)
rw_file("test.txt", "Hello, sandbox!")
print(file_exists("test.txt"))  # True (in sandbox)

debug.sandbox(False)
rw_file("real_file.txt", "This writes to disk.")
```

### **1-B. JSON**

```python
data = rwe_json("config.json") # Returns full JSON
rwe_json("config.json", {"a": {"b": 2}}) # Sets entire JSON
print(rwe_json("config.json", E="a/b"))  # Returns a nested value (ie. a: {b: 2})
rwe_json("config.json", 42, E="x/y/z") # Sets that nested value (ie. x: {y: {z: 42}})
```

### **2. Dynamic Strings (`S` and `M`)**

```python
user = "Alice"
id_num = 42

greeting = S("User {user} (ID: {id_num}) logged in at {timestamp()}")
m_greeting = M("User {user} (ID: [id_num]) logged in at {timestamp()}")

user = "Bob"
id_num = 99

print(greeting)     # User Bob (ID: 99) ...
print(m_greeting)   # User Bob (ID: 42) ...
```

### **3. Encoding & Security**

```python
encoded = encode("Secret Message")
decoded = decode(encoded)
print(decoded.decode())
```

### **4. System Utilities**

```python
notify("Done!", "Script complete!")
clipboard_copy("Text copied.")
print(censor(get_public_ip(), '-'))  # "118.---.---.93"
```

### **5. Temporary Variables**

```python
t = Temporary("Code: 1337", delay=5, expiry="Expired")
print(t)  # "Code: 1337"
time.sleep(5)
print(t)  # "Expired"

t2 = Temporary("Limited use", uses=2, expiry="Gone")
print(t2)  # "Limited use"
print(t2)  # "Limited use"
print(t2)  # "Gone"
```

### **6. Other Classes**

```python
Toggle("A", "B", "C")  # Cycles through values
Undo("Initial").set("Change 1").undo()  # Reverts
Lock("Secret").lock().set("Still secret")  # Cannot overwrite if locked
```

### **7. Discord Fake Messages**

```python
message = FakeMessage("This is a demonstation.", author="You")
print(message.content) # Would print: This is a demonstation.
message.reply("Hello demonstation") # Would print a fake reply message.
```

### **8. Run the Full Demo**

```python
tech_demo()  # Try it all in one shot
```

---

## **API Highlights**

| Function/Class          | Description                                             |
| ----------------------- | ------------------------------------------------------- |
| `rw_file()`             | Read/write files (sandbox-aware).                       |
| `S()` / `M()`           | Dynamic and static-evaluated strings.                   |
| `encode()` / `decode()` | Secure encoding with shadow keys.                       |
| `notify()`              | OS-level notification popup.                            |
| `file_grep()`           | Regex search across files.                              |
| `ansi()`                | RGB terminal styling.                                   |
| `debug.sandbox()`       | Toggle sandbox mode.                                    |
| `Temporary()`           | Create time/use-expiring or permanent-transform values. |
| `Toggle()`              | Cycle between given values.                             |
| `Undo()`                | Versioned string that supports undo/redo/history.       |
| `Lock()`                | Prevent changes unless explicitly unlocked.             |

---

## **DEBUG Features**

```python
debug.sandbox(True/False)        # Enable/disable sandbox
debug.death(True/False)          # Enable/disable forced errors
debug.status()                   # Show sandbox and death state
debug.peek_vars(dict, keys=None) # View contents of variables
debug.safe_eval(expr, ...)       # Evaluate expressions safely
debug.trace(msg="Trace")         # Print a trace stack
debug.pause("...")               # Pause execution
debug.watch("myVar", globals())  # Watch variable value
```

---

## **Why Use ltoolboxLib?**

* **All-in-One Utility** - A single import covers dozens of use cases.
* **Safe Testing** - Sandbox mode protects your real files.
* **Smarter Code** - Logic and flow tools like `Toggle`, `Undo`, and `Temporary`.
* **Pretty Output** - Styled output for terminal nerds.
* **Quick Start, Quick Results** - Minimal setup, maximum value.
* **Batteries included** - Not really though. No batteries.