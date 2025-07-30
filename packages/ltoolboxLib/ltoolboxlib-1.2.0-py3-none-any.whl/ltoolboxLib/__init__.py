# py

import re
import random
import time
import datetime
import inspect
import os
import json
import shutil
import tempfile
import hashlib
import subprocess
import uuid as uuid_lib
import pyperclip  # Requires pyperclip package
import platform
from pathlib import Path
import requests
import string
import sys
import io
import base64
from functools import wraps
from difflib import SequenceMatcher

#-> temporary

class Temporary:
    def __init__(self, content, delay=None, expiry="", uses=1, permanent=False):
        self.otp = delay is None
        self.uses = uses
        self.used = False
        self.timer = time.time() + delay if delay is not None else None
        self.content = content
        self.expiry = expiry
        self.delay = delay
        self.permanent = permanent

    def __str__(self):
        if self.is_expired:
            if self.permanent:
                self.content = self.expiry
            return self.expiry
        if self.otp:
            self.uses -= 1
            if self.uses <= 0:
                self.used = True
        return self.content

    def __repr__(self):
        return f"Temporary({self.content!r}, {self.delay}, {self.expiry!r})"

    @property
    def original(self):
        return self.content

    @property
    def is_expired(self):
        if self.otp:
            return self.used
        return time.time() >= self.timer

#-> word_formatting

def title_case(text):
    """Convert a string to title case while preserving small words like 'and', 'of', etc."""
    small_words = {"and", "or", "the", "a", "an", "in", "on", "at", "to", "but", "for", "nor", "with", "as", "by", "of"}
    words = text.split()
    if not words:
        return ""
    titled = [words[0].capitalize()]  # Always capitalize the first word
    for word in words[1:]:
        titled.append(word if word.lower() in small_words else word.capitalize())
    return " ".join(titled)

def acronym(text):
    text = title_case(text)
    bext = ''
    for ch in str(text).split(" "):
        bext+=ch[0]
    return bext

def c_encode(text, formatting=[], splitter=" "):
    return safe_convert(f"{splitter}".join(str(ord(ch)) for ch in str(text)), formatting, f"{splitter}")

def c_decode(encoded, splitter=" "):
    return "".join(chr(int(code)) for code in encoded.split(splitter))

def compare_versions(v1, v2):
    """Compare two version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2."""
    def parse(v):
        return [int(x) for x in re.findall(r'\d+', v)]

    parts1 = parse(v1)
    parts2 = parse(v2)
    length = max(len(parts1), len(parts2))
    parts1 += [0] * (length - len(parts1))
    parts2 += [0] * (length - len(parts2))

    for a, b in zip(parts1, parts2):
        if a < b:
            return -1
        elif a > b:
            return 1
    return 0

def fuzzy_match(a, b):
    """Returns similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a, b).ratio()

#-> function_wrappers

def silent(func):
    """Silences all print output from the function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            return func(*args, **kwargs)
        finally:
            sys.stdout = old_stdout
    return wrapper

def redirect(func):
    """
    Captures all print output from the function and returns it as a string.
    The function's return value and its printed output are both preserved.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        old_stdout = sys.stdout
        stream = io.StringIO()
        sys.stdout = stream
        try:
            result = func(*args, **kwargs)
            output = stream.getvalue()
            return result, output
        finally:
            sys.stdout = old_stdout
    return wrapper

#-> tools

def get_public_ip(timeout=5):
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]

    for url in services:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            ip = response.text.strip()
            if ip:
                return ip
        except requests.RequestException:
            continue
    return None

# Provide your own function to get .ltools path or replace below:
def get_ltools_path(filename):
    home = os.path.expanduser("~")
    ltools_dir = os.path.join(home, ".ltools")
    os.makedirs(ltools_dir, exist_ok=True)
    return os.path.join(ltools_dir, filename)

# Helpers for sandbox management
def get_sandbox(sandbox_path):
    if not os.path.exists(sandbox_path):
        return {}
    with open(sandbox_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

#-> colors

SANDBOX_PATH = get_ltools_path("sandbox.file.json")

class Colors:
    RESET = "\x1b[0m"
    STRING = "\x1b[38;5;114m"
    NUMBER = "\x1b[38;5;75m"
    BOOLEAN = "\x1b[38;5;220m"
    NULL = "\x1b[38;5;244m"
    BRACE = "\x1b[38;5;248m"
    KEY = "\x1b[38;5;81m"

def colorize_json(obj, indent=0):
    space = "  " * indent
    if obj is None:
        return f"{Colors.NULL}null{Colors.RESET}"
    elif isinstance(obj, bool):
        return f"{Colors.BOOLEAN}{str(obj).lower()}{Colors.RESET}"
    elif isinstance(obj, (int, float)):
        return f"{Colors.NUMBER}{obj}{Colors.RESET}"
    elif isinstance(obj, str):
        return f"{Colors.STRING}\"{obj}\"{Colors.RESET}"
    elif isinstance(obj, list):
        items = [colorize_json(i, indent + 1) for i in obj]
        inner = ",\n".join(f"{'  '*(indent+1)}{item}" for item in items)
        return f"{Colors.BRACE}[\n{inner}\n{space}]{Colors.RESET}"
    elif isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            colored_key = f"{Colors.KEY}\"{k}\"{Colors.RESET}"
            colored_val = colorize_json(v, indent + 1)
            items.append(f"{'  '*(indent+1)}{colored_key}: {colored_val}")
        inner = ",\n".join(items)
        return f"{Colors.BRACE}{{\n{inner}\n{space}}}{Colors.RESET}"
    else:
        return str(obj)

def pretty_print_json_color(data):
    print(colorize_json(data))

#-> tech_demo

def tech_demo():
    """ULTIMATE TECH DEMO - Shows EVERY function with MAXIMUM DETAIL"""
    global __SANDBOX_ENABLED__, __DEATH_ENABLED__

    # Preserve original states
    orig_sandbox = __SANDBOX_ENABLED__
    orig_death = __DEATH_ENABLED__

    try:
        clear()
        print(ansi(fg="#00ff00", bg="#000000", features="**,__") +
              "┏━━━ ltools TECH DEMO ━━━┓" + ansi(reset=True))
        print(ansi(fg="#00ffff") + "This demo will show almost ever function." + ansi(reset=True))

        title = M('\n[ansi(features="**")]=== {get_ltools_path(category.lower())} === [ansi(reset=True)]')

        try:
            # ===== 1. SYSTEM INFORMATION =====
            category = "SYSTEM INFORMATION"
            death()
            print(title())
            print(f"• Operating System: {platform.system()} {platform.release()}")
            print(f"• Username: {get_username()}")
            print(f"• Shell: {env('SHELL', 'Not detected')}")
            print(f"• Python Version: {platform.python_version()}")

            ip = get_public_ip()
            print(f"• Public IP: {censor(ip) if ip else 'Unable to determine'}")
            print(f"• Current Directory: {os.getcwd()}")
            print(f"• Current Time: {timestamp()} ({now_ms()} ms)")
        except Exception as e:
            print(f"Whoops! Looks like we hit a small hiccup in the {category} category! Error: {ansi('#FF0000')}{e}{ansi(reset=True)}")

        try:
            # ===== 2. FILE OPERATIONS =====
            category = "FILE OPERATIONS"
            death()
            print(title())

            # Create test environment
            test_dir = "ltools_demo_temp"
            mkdir(test_dir)
            dir_exists(test_dir)
            print(f"\nCreated test directory: {test_dir}")

            # Create test files
            files = {
                "demo.txt": "Initial content\nLine two\nLine three",
                "data.json": '{"name": "Test", "values": [1,2,3], "active": true}',
                "binary.bin": bytes([i % 256 for i in range(1024)])
            }

            print("\nCreating test files:")
            for filename, content in files.items():
                try:
                    rw_file(filename, content)
                    size = file_size(filename)
                    print(f"• Created {filename} ({human_readable_size(size)})")
                except Exception as e:
                    print(f"• Failed to make, as: {e}.")

            # File operations demo
            print("\n" + ansi(features="__") + "FILE OPERATIONS DEMO:" + ansi(reset=True))

            # Append to file
            append_content = "\nAppended at: " + timestamp()
            append_file("demo.txt", append_content)
            print(f"\nAppended to demo.txt:\n{ansi(fg='#ffff00')}{append_content}{ansi(reset=True)}")

            # Copy file
            copy("demo.txt", "demo_copy.txt")
            print(f"\nCopied demo.txt to demo_copy.txt")
            print(f"Original size: {file_size('demo.txt')} bytes")
            print(f"Copy size: {file_size('demo_copy.txt')} bytes")

            # File comparison
            diff, size1, size2 = file_size_difference("demo.txt", "demo_copy.txt")
            print(f"\nFile size difference: {diff} bytes (should be 0)")

            # File tree
            print("\nCurrent directory structure:")
            file_tree('.', max_depth=2)

            # File search
            print("\nSearching for files containing 'content':")
            matches = file_grep(r'content', '.')
            for m in matches:
                print(f"- {m}")
        except Exception as e:
            print(f"Whoops! Looks like we hit a small hiccup in the {category} category! Error: {ansi('#FF0000')}{e}{ansi(reset=True)}")

        try:
            # ===== 3. DATA MANIPULATION =====
            category = "DATA MANIPULATION"
            death()
            print(title())

            # Number conversions
            print("\n" + ansi(features="__") + "NUMBER CONVERSIONS:" + ansi(reset=True))
            print(f"• clamp(300, 0, 255) = {clamp(300, 0, 255)}")
            print(f"• lerp(10, 20, 0.3) = {lerp(10, 20, 0.3)}")
            print(f"• format_int('Price: $123abc45') = {format_int('Price: $123abc45')}")
            print(f"• binary_to_number('1010') = {binary_to_number('1010')}")
            print(f"• convert_int(25, to_base=3) = {convert_int(25, to_base=3)}")
            lisssp = ['V1.1.2', 'V.1.2.1']
            print(f"• compare_versions() = {compare_versions('V1.1.2', 'V.1.2.1')} = {lisssp[compare_versions('V1.1.2', 'V.1.2.1')]}")

            # List operations
            print("\n" + ansi(features="__") + "LIST OPERATIONS:" + ansi(reset=True))
            nested = [[1,2], [3,[4,5]], 6]
            print(f"• flatten({nested}) = {flatten(nested)}")
            dupes = [1,2,2,3,3,3,4]
            print(f"• unique({dupes}) = {unique(dupes)}")
            print(f"• is_equal([5,5,5]) = {is_equal([5,5,5])}")

            # JSON operations
            print("\n" + ansi(features="__") + "JSON OPERATIONS:" + ansi(reset=True))
            data = read_json("data.json")
            print("Original JSON:")
            pretty_print_json_color(data)

            # Modify and save
            data['modified'] = timestamp()
            write_json("data_modified.json", data)
            print("\nModified JSON saved to data_modified.json")
        except Exception as e:
            print(f"Whoops! Looks like we hit a small hiccup in the {category} category! Error: {ansi('#FF0000')}{e}{ansi(reset=True)}")

        try:
            # ===== 4. ADVANCED FEATURES =====
            category = "ADVANCED FEATURES"
            death()
            print(title())

            # S-strings
            print("\n" + ansi(features="__") + "DYNAMIC S-STRINGS (Smart Strings):" + ansi(reset=True))
            user = "Alice"
            id = 42
            greeting = S("User {user} (ID: {id}) logged in at {timestamp()}")
            print(f"• Initial: {greeting}")
            print("• Raw: \"User {user} (ID: {id}) logged in at {timestamp()}\"")
            user = "Bob"
            id = 99
            print(f"• Updated: {greeting}")

            print("\n" + ansi(features="__") + "DYNAMIC-STATIC M-STRINGS (Mixed Strings):" + ansi(reset=True))
            user = "Alice"
            key = "Bringus"
            greeting = M("User {user}, Key [key]")
            print(f"• Initial: {greeting}")
            print("• Raw: \"User {user}, Key [key]\"")
            print("• Changes: user = \"Bob\", key = \"abc123\"")
            user = "Bob"
            key = "abc123"
            print(f"• Updated: {greeting}")

            print("\n" + ansi(features="__") + "Temporary VARIABLES:" + ansi(reset=True))
            t = Temporary(f"Special fake expiring code: {random.randint(int(1e3), int(1e5))}!", 5, "Expired", permanent=True)
            print(f'• Temporary(f"{t}",5,"Expired", permanent=True)')
            print(f'• t.is_expired: {t.is_expired}')
            print(f'• Waiting for 5 seconds...')
            time.sleep(5)
            print(f'• New temporary value: {t}')
            print(f'• t.original: {t.original}')
            print(f'• t.is_expired: {t.is_expired}')

            tt = Temporary(f"Special fake expiring code: {random.randint(int(1e3), int(1e5))}!",expiry="Expired",uses=3)
            print(f'\n• Temporary(f"{tt.original}",expiry="Expired",uses=3)')
            print(f'• t.is_expired: {tt.is_expired}')
            print(f'• This now will expire once used.')
            print(f'• Use 1: {tt}')
            print(f'• Use 2: {tt}')
            print(f'• Uses left: {tt.uses}')
            print(f'• Use 3: {tt}')
            print(f'• Use 4: {tt}')
            print(f'• t.original: {tt.original}')
            print(f'• t.is_expired: {tt.is_expired}')

            print("\n" + ansi(features="__") + "GENERAL TEXT:" + ansi(reset=True))
            print(f"• title_case(\"mY cAptialIZAtioN is BaD PLEase heLP\") = {title_case('mY cAptialIZAtioN is BaD PLEase heLP')}")
            print(f"• acronym(\"genetic lifeform and disc operating system\") = {acronym('genetic lifeform and disc operating system')}")
            print(f"• fuzzy_match(\"I eat pizza\",\"I eat fish\") = {fuzzy_match('I eat pizza','I eat fish'):.2f}% match")
            c_cod = c_encode("Encrypt me!", "","-")
            print(f"• c_encode(\"Encrypt me!\",\"\", \"-\") = {c_cod}")
            print(f"• c_decode({c_cod}, \"-\") = {c_decode(c_cod,'-')}")

            # Encoding
            print("\n" + ansi(features="__") + "ENCODING DEMO:" + ansi(reset=True))
            secret = "MySecret123"
            print(f"• Original: {secret}")
            encoded = encode(secret)
            print(f"• Encoded: {encoded}")
            decoded = decode(encoded)
            print(f"• Decoded: {decoded.decode()}")
        except Exception as e:
            print(f"Whoops! Looks like we hit a small hiccup in the {category} category! Error: {ansi('#FF0000')}{e}{ansi(reset=True)}")

        try:
            # ===== 5. CLEANUP =====
            category = "CLEANUP"
            death()
            print(title())
            os.chdir('..')
            rm_dir(test_dir)
            print(f"Removed test directory: {test_dir}")
            print(f"The ACTUAL end!")
        except Exception as e:
            print(f"Whoops! Looks like we hit a small hiccup in the {category} category! Error: {ansi('#FF0000')}{e}{ansi(reset=True)}")

    finally:
        # Restore original states
        debug.sandbox(orig_sandbox)
        debug.death(orig_death)

        # Final output
        print("\n" + ansi(fg="#00ff00", features="**") + "DEMO COMPLETE!" + ansi(reset=True))
        print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

#-> system

def clear():
    """Clear terminal screen (cross-platform)"""
    os.system('cls' if os.name == 'nt' else 'clear')

def quantum_random():
    """Get true random numbers from quantum fluctuations (requires internet)"""
    try:
        return int(requests.get('https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint8').json()['data'][0])
    except:
        return random.randint(0, 255)

def get_username():
    # Get the user's home dir
    home = os.path.expanduser("~")

    # Detect correct path separator
    symbol = "/" if "/" in home else "\\"

    # Split the home path
    home_parts = home.split(symbol)

    # Find "Users" and return the next part
    for i in range(len(home_parts)):
        if home_parts[i].lower() == "users" and i + 1 < len(home_parts):
            return home_parts[i + 1]

    return False

def clipboard_copy(text):
    """Copy text to system clipboard"""
    pyperclip.copy(text)

def clipboard_paste():
    """
    Get clipboard content using pyperclip.
    Returns a string or an empty string if clipboard is empty.
    """
    try:
        return pyperclip.paste()
    except pyperclip.PyperclipException:
        return ""

def notify(title, message, sound=True):
    """Cross-platform system notifications
    - Windows: Uses win10toast or native PowerShell
    - Linux: Requires 'libnotify-bin' (notify-send)
    - macOS: Uses osascript
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            cmd = f'osascript -e \'display notification "{message}" with title "{title}"\''
            os.system(cmd)

        elif system == "Linux":
            # Check if notify-send is available
            if shutil.which("notify-send"):
                sound_opt = "--hint=int:transient:1" if sound else ""
                os.system(f'notify-send "{title}" "{message}" {sound_opt}')
            else:
                print(f"Linux: Install 'libnotify-bin' for notifications: {title} - {message}")

        elif system == "Windows":
            try:
                # Try modern Windows 10+ toast notifications
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5)
            except ImportError:
                # Fallback to PowerShell notification
                ps_script = f'''
                [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
                [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")
                '''
                subprocess.run(["powershell", "-command", ps_script], check=False)

    except Exception as e:
        print(f"Notification failed: {e}")


def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

#-> classes_s_m

def clamp(value, min_val, max_val):
    """Constrain value between min and max"""
    return max(min_val, min(value, max_val))

def lerp(a, b, t):
    """Linear interpolation between a and b"""
    return a + (b - a) * t

class S:
    def __init__(self, template):
        self.template = template

    def __str__(self):
        # Grab the calling frame's local & global vars
        frame = inspect.currentframe().f_back
        local_vars = frame.f_locals
        global_vars = frame.f_globals

        # Replace {var} with their actual value in the context
        def replacer(match):
            expr = match.group(1)
            try:
                return str(eval(expr, global_vars, local_vars))
            except Exception as e:
                return f"<{e}>"

        return re.sub(r"\{([^}]+)\}", replacer, self.template)

    def __repr__(self):
        return f'S("{self.template}")'

class M:
    def __init__(self, template, static_vars=None):
        self.template = template
        self.static_vars = static_vars or {}

        # Static resolution — use *caller* frame at creation
        frame = inspect.currentframe().f_back
        local_vars = frame.f_locals
        global_vars = frame.f_globals

        def static_replacer(match):
            expr = match.group(1)
            try:
                if expr in self.static_vars:
                    return str(self.static_vars[expr])
                return str(eval(expr, global_vars, local_vars))
            except Exception as e:
                return f"<{e}>"

        self.processed_template = re.sub(r"\[([^\]]+)\]", static_replacer, template)

    def __call__(self):
        # Get the **true** calling frame: go up past __call__ and str layers
        frame = inspect.currentframe()
        while frame:
            code = frame.f_code.co_name
            if code not in {"__call__", "__str__"}:
                break
            frame = frame.f_back

        local_vars = frame.f_locals
        global_vars = frame.f_globals

        def dynamic_replacer(match):
            expr = match.group(1)
            try:
                return str(eval(expr, global_vars, local_vars))
            except Exception as e:
                return f"<{e}>"

        return re.sub(r"\{([^}]+)\}", dynamic_replacer, self.processed_template)

    def __str__(self):
        return self()

    def __repr__(self):
        return f'M("{self.template}")'

#-> formatting

def safe_convert(content, example, splitter=None):
    target_type = type(example)
    try:
        if target_type is bool:
            return str(content).lower() in ("1", "true", "yes", "on")
        if target_type is list:
            if splitter == None:
                return target_type(content)
            else:
                return content.split(splitter)
        return target_type(content)
    except:
        return example


def stable_multitude(seed, round_index):
    data = f"-{seed}.{round_index}".encode('utf-8')
    h = hashlib.sha256(data).digest()
    return sum(h) % 256 or 1


def format_int(ins, allow_negative=False, base=None):
    s = ins.strip().lower()
    sign = -1 if allow_negative and s.startswith('-') else 1
    if sign == -1:
        s = s[1:].lstrip()

    if base is None:
        # Detect base by prefix
        if s.startswith('0x'):
            base = 16
            digits = s[2:]
        elif s.startswith('0o'):
            base = 8
            digits = s[2:]
        elif s.startswith('0b'):
            base = 2
            digits = s[2:]
        else:
            base = 10
            digits = ''.join(c for c in s if c.isdigit())
    else:
        digits = ''.join(c for c in s if c.isalnum())  # Keep alnum for bases > 10

    return sign * int(digits, base) if digits else 0


def binary_to_number(inputplease):
    inputplease = int(str(format_int(inputplease,base=2))[::-1])
    binaryval = 1
    decimalval = 0
    # print(binaryval)
    for val in str(inputplease):
        decimalval += int(val) * binaryval
        binaryval = binaryval + binaryval
        # print(binaryval)
    return decimalval

#-> time_chance

def wait(seconds):
    time.sleep(seconds)

def now_ms():
    return int(time.time() * 1000)

def timeit(fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    t1 = time.perf_counter()
    return result, t1 - t0

def chance(p:int=100,starter=0):
    return random.randint(starter,p) == p

def who_called_me():
    frame = inspect.stack()[2]
    return f"{frame.filename}:{frame.lineno} in {frame.function}()"

def debug_vars(*names):
    caller = inspect.currentframe().f_back
    return {name: caller.f_locals.get(name, "<undefined>") for name in names}

def env(name, default=None):
    return os.environ.get(name, default)

#-> debug

# Global sandbox toggle
__SANDBOX_ENABLED__ = False
__DEATH_ENABLED__ = False
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class debug:
    @staticmethod
    def sandbox(enable=None):
        global __SANDBOX_ENABLED__
        if enable is not None:
            __SANDBOX_ENABLED__ = bool(enable)
        return f"Sandbox {'enabled' if __SANDBOX_ENABLED__ else 'disabled'}"

    @staticmethod
    def death(enable=None):
        global __DEATH_ENABLED__
        if enable is not None:
            __DEATH_ENABLED__ = bool(enable)
        return f"Death {'enabled' if __DEATH_ENABLED__ else 'disabled'}"

    @staticmethod
    def status():
        s = globals().get("__SANDBOX_ENABLED__", False)
        d = globals().get("__DEATH_ENABLED__", False)
        return f"Sandbox: {'ON' if s else 'OFF'}, Death: {'ON' if d else 'OFF'}"

    # --- Dev Helpers below ---

    @staticmethod
    def peek_vars(vars_dict, keys=None):
        """Show selected vars from a dict (locals or globals) — keys=None shows all"""
        if keys is None:
            keys = vars_dict.keys()
        return {k: vars_dict.get(k) for k in keys}

    @staticmethod
    def safe_eval(expr, globals_=None, locals_=None):
        """Try evaluating an expression safely, returns error string if fails"""
        try:
            return eval(expr, globals_ or {}, locals_ or {})
        except Exception as e:
            return f"<eval error: {e}>"

    @staticmethod
    def trace(msg="Trace", pause=False, lines=2):
        """Print a quick stack trace (2 frames up) with a message"""
        import traceback
        print(f"{ansi('#00FF00')}[TRACE]{ansi(reset=True)} {ansi(features='__')}{ansi(features='**')}{msg}")
        for line in traceback.format_stack(limit=lines+1)[:-1]:
            print(line.strip())
        print(f"{ansi(reset=True)}", end="")
        if pause:
            input("\nPaused. Press enter to continue code.")

    @staticmethod
    def pause(msg="\nPaused. Press enter to continue code."):
        input(msg)

    @staticmethod
    def watch(var_name, scope, prefix="[WATCH]"):
        """Print a var's value from given scope (locals or globals)"""
        val = scope.get(var_name, "<not found>")
        print(f"{prefix} {var_name} = {val}")

def save_sandbox(data, sandbox_path):
    with open(sandbox_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def resolve_name(name, sandbox):
    renames = sandbox.get("__renames__", {})
    for old, new in renames.items():
        if name == new:
            return old  # resolve back to original
    return name

#-> files
#--------------------------------------------------

def file_tree(startpath, max_depth=3, indent=4, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox

    # Combine real and sandbox files
    all_items = {}

    # Get real filesystem items
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        if level > max_depth:
            continue
        rel_path = os.path.relpath(root, startpath)
        if rel_path == '.':
            rel_path = ''
        for d in dirs:
            path = os.path.join(rel_path, d) if rel_path else d
            all_items[path] = 1  # 1 represents folder
        for f in files:
            path = os.path.join(rel_path, f) if rel_path else f
            all_items[path] = 2  # 2 represents real file

    # Get sandbox items if enabled
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        for path, content in sandbox.items():
            if path == "__renames__":
                continue
            if isinstance(content, int):
                # Skip deleted items (0) but keep folders (1)
                if content == 1:
                    all_items[path] = 1
            else:
                all_items[path] = 3  # 3 represents sandbox file

    # Print the combined tree
    def print_tree(base, items, current_depth=0):
        if current_depth > max_depth:
            return
        indent_str = ' ' * indent * current_depth
        for path, item_type in sorted(items.items()):
            parts = path.split(os.sep)
            if len(parts) > 1 or not base:
                continue
            name = parts[0]
            if item_type == 0:
                continue  # Skip deleted items
            elif item_type == 1:
                print(f"{indent_str}📁 {name}/")
                # Find all items in this subfolder
                sub_items = {k[len(name)+1:]: v for k, v in all_items.items()
                           if k.startswith(name + os.sep) and v != 0}
                print_tree(os.path.join(base, name), sub_items, current_depth + 1)
            elif item_type == 2:
                print(f"{indent_str}📄 {name} (real)")
            elif item_type == 3:
                print(f"{indent_str}📄 {name} (sandbox)")

    print_tree(startpath, {k: v for k, v in all_items.items()
                         if not os.sep in k or k.endswith(os.sep)})

def mkdir(path, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        # Mark as folder (1)
        sandbox[path] = 1
        save_sandbox(sandbox, sandbox_path)
    else:
        Path(path).mkdir(parents=True, exist_ok=True)

def rm_dir(path, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if not enabled:
        os.removedirs(path)
        return

    sandbox = get_sandbox(sandbox_path)

    # Mark folder and all its contents as deleted (0)
    path = os.path.normpath(path)
    to_delete = [k for k in sandbox.keys()
                if k == path or k.startswith(path + os.sep)]

    for k in to_delete:
        sandbox[k] = 0  # Mark as deleted

    save_sandbox(sandbox, sandbox_path)

def rw_file(filename, content=None, binary=None, use_sandbox=None, rename_to=None, sandbox_path=SANDBOX_PATH):
    binary = isinstance(content, bytes) if binary is None else binary
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    mode = 'rb' if binary and content is None else 'wb' if binary else 'r' if content is None else 'w'
    encoding = None if binary else 'utf-8'

    sandbox = get_sandbox(sandbox_path)
    effective_name = resolve_name(filename, sandbox)

    # === HANDLE RENAME ===
    if rename_to:
        if not enabled:
            os.rename(filename, rename_to)
        else:
            sandbox["__renames__"] = sandbox.get("__renames__", {})
            sandbox["__renames__"][filename] = rename_to
            if filename in sandbox and sandbox[filename] != 0:
                sandbox[rename_to] = sandbox.pop(filename)
            save_sandbox(sandbox, sandbox_path)
        return

    # === HANDLE READ ===
    if content is None:
        if enabled:
            if effective_name in sandbox:
                data = sandbox[effective_name]
                if isinstance(data, int):  # deleted marker or folder
                    return b'' if binary else ''
                if isinstance(data, dict) and data.get("__b64__"):
                    return base64.b64decode(data["data"])
                return data if binary else str(data)
        try:
            with open(filename, mode, encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            return b'' if binary else ''

    # === HANDLE WRITE ===
    if enabled:
        if filename in sandbox and sandbox[filename] == 0:
            del sandbox[filename]
        if binary:
            encoded = base64.b64encode(content).decode('ascii')
            sandbox[filename] = {"__b64__": True, "data": encoded}
        else:
            sandbox[filename] = content
        save_sandbox(sandbox, sandbox_path)
    else:
        with open(filename, mode, encoding=encoding) as f:
            f.write(content)

def file_exists(path, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        effective_path = resolve_name(path, sandbox)
        if effective_path in sandbox:
            return sandbox[effective_path] != 0  # Not deleted
    return os.path.isfile(path)

def list_files(folder, pattern=".*", full_path=False, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    files = []

    if enabled:
        sandbox = get_sandbox(sandbox_path)
        # Get sandbox files that aren't marked as deleted (0) or folders (1)
        sandbox_files = [f for f in sandbox.keys()
                        if f != "__renames__" and
                        f.startswith(folder) and
                        not isinstance(sandbox[f], int)]
        # Filter by pattern
        sandbox_files = [f for f in sandbox_files if re.match(pattern, os.path.basename(f))]
        files.extend(sandbox_files)

    try:
        real_files = [f for f in os.listdir(folder) if re.match(pattern, f)]
        if full_path:
            real_files = [os.path.join(folder, f) for f in real_files]
        files.extend(real_files)
    except FileNotFoundError:
        pass

    # Remove duplicates
    files = list(set(files))
    if full_path:
        files = [os.path.join(folder, f) if not os.path.isabs(f) else f for f in files]

    return files

def touch(filename, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        if filename not in sandbox or sandbox[filename] == 0:
            sandbox[filename] = ""
            save_sandbox(sandbox, sandbox_path)
    else:
        with open(filename, 'a', encoding='utf-8'):
            os.utime(filename, None)

def rm(path, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        effective_path = resolve_name(path, sandbox)
        sandbox[effective_path] = 0  # Mark as deleted
        save_sandbox(sandbox, sandbox_path)
    else:
        if os.path.isfile(path):
            os.remove(path)

def copy(src, dst, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    is_binary = src.lower().endswith(('.bin', '.png', '.jpg', '.jpeg', '.exe'))

    contento = rw_file(src, use_sandbox=enabled, binary=is_binary)
    if contento is not None:
        rw_file(dst, content=contento, use_sandbox=enabled, binary=is_binary)

def read_json(path, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        effective_path = resolve_name(path, sandbox)
        if effective_path in sandbox and not isinstance(sandbox[effective_path], int):
            try:
                return json.loads(sandbox[effective_path])
            except:
                return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def write_json(path, data, atomic=False, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    try:
        if enabled:
            sandbox = get_sandbox(sandbox_path)
            # Remove deleted mark if exists
            if path in sandbox and sandbox[path] == 0:
                del sandbox[path]
            sandbox[path] = json.dumps(data, indent=2)
            save_sandbox(sandbox, sandbox_path)
            return True
        else:
            if atomic:
                dir_name = os.path.dirname(path)
                with tempfile.NamedTemporaryFile('w', delete=False, dir=dir_name, encoding='utf-8') as tmp:
                    json.dump(data, tmp, indent=2)
                    temp_name = tmp.name
                os.replace(temp_name, path)
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            return True
    except:
        return False

def append_file(filename, content, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    encoding = 'utf-8'
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox

    try:
        if enabled:
            sandbox = get_sandbox(sandbox_path)
            effective_name = resolve_name(filename, sandbox)
            if effective_name in sandbox and isinstance(sandbox[effective_name], int):
                sandbox[effective_name] = ""  # Restore deleted file
            prev_content = sandbox.get(effective_name, "")
            sandbox[effective_name] = prev_content + content
            save_sandbox(sandbox, sandbox_path)
            return True
        else:
            with open(filename, 'a', encoding=encoding) as f:
                f.write(content)
            return True
    except:
        return False

def backup_file(filename, suffix='.bak', use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        effective_name = resolve_name(filename, sandbox)
        if effective_name in sandbox and not isinstance(sandbox[effective_name], int):
            sandbox[effective_name + suffix] = sandbox[effective_name]
            save_sandbox(sandbox, sandbox_path)
            return True
        return False
    else:
        if not file_exists(filename):
            return False
        shutil.copy2(filename, filename + suffix)
        return True

def file_size(in_location, use_sandbox=None):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    try:
        if enabled:
            sandbox = get_sandbox(SANDBOX_PATH)
            content = sandbox.get(resolve_name(in_location, sandbox), "")
            if isinstance(content, int):  # Deleted or folder
                return 0
            return len(content)
        else:
            return os.path.getsize(in_location)
    except FileNotFoundError as e:
        return f"(×_×;) file error: {e}", 0, 0

def file_size_difference(in_location, out_location, use_sandbox=None):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    try:
        in_size = file_size(in_location, use_sandbox=enabled)
        out_size = file_size(out_location, use_sandbox=enabled)
        diff = out_size - in_size
        return diff, in_size, out_size
    except FileNotFoundError as e:
        return f"(×_×;) file error: {e}", 0, 0

def file_grep(pattern, path=".", recursive=True, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox
    matches = []

    def find_files(base_path, pattern, recursive):
        for root, dirs, files in os.walk(base_path):
            for f in files:
                if re.match(pattern, f):
                    yield os.path.join(root, f)
            if not recursive:
                break

    # Search sandbox files
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        for f, content in sandbox.items():
            if f == "__renames__" or isinstance(content, int):
                continue
            # Ensure content is text-like
            try:
                content_str = content if isinstance(content, str) else json.dumps(content)
                if re.search(pattern, f) or re.search(pattern, content_str):
                    matches.append(f)
            except Exception:
                continue

    # Search real files
    for filepath in find_files(path, ".*", recursive):
        try:
            with open(filepath, 'r', errors='ignore') as f:
                if re.search(pattern, f.read()):
                    matches.append(filepath)
        except:
            continue

    return matches

def dir_exists(path, use_sandbox=None, sandbox_path=SANDBOX_PATH):
    """
    Check if a directory exists, with sandbox support.

    Args:
        path: Path to directory to check
        use_sandbox: Whether to use sandbox (None for global setting)
        sandbox_path: Path to sandbox file

    Returns:
        bool: True if directory exists, False otherwise
    """
    enabled = __SANDBOX_ENABLED__ if use_sandbox is None else use_sandbox

    # First check real filesystem
    if os.path.isdir(path):
        return True

    # Check sandbox if enabled
    if enabled:
        sandbox = get_sandbox(sandbox_path)
        path = os.path.normpath(path)

        # Case 1: Explicitly marked as folder (1)
        if path in sandbox and sandbox[path] == 1:
            return True

        # Case 2: Any sandboxed file exists in this directory
        for f in sandbox.keys():
            if f == "__renames__":
                continue
            if isinstance(sandbox[f], int):  # Skip special entries
                continue
            # Check if file is inside this directory
            if os.path.dirname(f) == path:
                return True

        # Case 3: Check renamed directories
        if "__renames__" in sandbox:
            for original, renamed in sandbox["__renames__"].items():
                if os.path.dirname(renamed) == path:
                    return True

    return False

#--------------------------------------------------

#-> variable_formatting

def wait_until(condition, timeout=5, interval=0.1):
    """Wait until `condition()` returns True or timeout expires"""
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(interval)
    return False

def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def track(func):
    name = getattr(func, '__name__', str(func))
    print(f"Started {name}: {time.perf_counter()}")
    cont, times = timeit(func)
    print(f"Ended {name}: {time.perf_counter()}")
    print(f"Difference: {times}")
    print()
    print(f"Returned Content:\n\n{cont}")

def flatten(lst):
    return [item for sublist in lst for item in (sublist if isinstance(sublist, list) else [sublist])]

def strip_comments(text, marker="#"):
    return "\n".join(line.split(marker, 1)[0].rstrip() for line in text.splitlines())

def normalize_ws(text):
    return ' '.join(text.split())

def unique(seq):
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def invert_dict(d):
    return {v: k for k, v in d.items()}

def random_choice_weighted(items, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for item, w in zip(items, weights):
        if upto + w >= r:
            return item
        upto += w
    return items[-1]  # fallback

def is_equal(things=None):
    # If it's not a list, treat as iterable of its string form
    if not isinstance(things, (list, tuple)):
        stuff = list(str(things))
    else:
        stuff = things

    if not stuff or stuff == None:
        return True  # empty means “all equal” by default

    old_z = stuff[0]
    for z in stuff[1:]:
        if old_z != z:
            return False
    return True

#-> extra

def ansi(fg=None, bg=None, features=None, reset=False):

    def parse_color(color):
        if not color:
            return None
        color = color.strip()
        # Hex format
        if color.startswith("#"):
            hexc = color[1:]
            if len(hexc) == 3:  # short form like #f0a
                hexc = ''.join(c*2 for c in hexc)
            if len(hexc) != 6 or not re.fullmatch(r'[0-9a-fA-F]{6}', hexc):
                raise ValueError(f"Invalid hex color: {color}")
            r, g, b = tuple(int(hexc[i:i+2], 16) for i in (0, 2, 4))
            return r, g, b
        # RGB format
        elif ',' in color:
            parts = color.split(',')
            if len(parts) != 3:
                raise ValueError(f"Invalid RGB color: {color}")
            r, g, b = (int(p.strip()) for p in parts)
            if not all(0 <= v <= 255 for v in (r, g, b)):
                raise ValueError(f"RGB values must be between 0 and 255: {color}")
            return r, g, b
        else:
            raise ValueError(f"Unknown color format: {color}")
    if not reset:
        codes = []

        # Text features mapping with italic fix
        feats_map = {
            '**': '1',  # bold
            '*': '3',   # italic
            '__': '4',  # underline
            '~~': '9',  # strikethrough
        }
        if features:
            feats = [f.strip() for f in features.split(',')]
            for f in feats:
                if f in feats_map:
                    codes.append(feats_map[f])

        # Foreground RGB color
        if fg:
            r, g, b = parse_color(fg)
            codes.append(f"38;2;{r};{g};{b}")

        # Background RGB color
        if bg:
            r, g, b = parse_color(bg)
            codes.append(f"48;2;{r};{g};{b}")

        content = f"\033[{';'.join(codes)}m" if codes else ''
    else:
        content = "\033[0m"
    return content

def find_files(directory, pattern="*", recursive=True):
    """Find files matching a pattern (glob syntax)"""
    return list(Path(directory).rglob(pattern) if recursive else Path(directory).glob(pattern))

def convert_int(num, to_base=10, from_base=10, prefix=True):
    if not (2 <= from_base <= 36) or not (2 <= to_base <= 36):
        raise ValueError("Bases must be between 2 and 36")

    digits = "0123456789abcdefghijklmnopqrstuvwxyz"

    # Step 1: Convert to base 10
    if isinstance(num, int):
        base10 = num
    elif isinstance(num, str):
        num = num.lower().strip()
        neg = num.startswith("-")
        num = num[1:] if neg else num
        base10 = 0
        for char in num:
            if char not in digits[:from_base]:
                raise ValueError(f"Invalid digit '{char}' for base {from_base}")
            base10 = base10 * from_base + digits.index(char)
        if neg:
            base10 = -base10
    else:
        raise TypeError("num must be an int or str")

    # Step 2: Convert from base 10 to to_base
    if base10 == 0:
        return "0"

    neg = base10 < 0
    base10 = abs(base10)
    res = []
    while base10:
        res.append(digits[base10 % to_base])
        base10 //= to_base
    res_str = ''.join(reversed(res))

    if prefix:
        if to_base == 2:
            res_str = "0b" + res_str
        elif to_base == 8:
            res_str = "0o" + res_str
        elif to_base == 16:
            res_str = "0x" + res_str

    if neg:
        res_str = "-" + res_str

    return res_str

def human_readable_size(size_bytes):
    """Convert bytes to human-readable format (KB, MB, etc.)"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

def truncate(text, length=100, suffix="..."):
    """Smart truncate with word boundary awareness"""
    if len(text) <= length:
        return text
    return text[:length-len(suffix)].rsplit(' ', 1)[0] + suffix

def random_string(length=8, charset=None):
    """Generate random string from given charset"""
    charset = charset or string.ascii_letters + string.digits
    return ''.join(random.choice(charset) for _ in range(length))

def uuid(short=False):
    """Generate UUID (short version available)"""
    return str(uuid_lib.uuid4())[:8] if short else str(uuid_lib.uuid4())

def vaporwave(text: str) -> str:
    """Convert text to full-width vaporwave aesthetic."""
    return ''.join(
        chr(ord(char) + 0xFEE0) if '!' <= char <= '~' else char
        for char in text
    )

class DeathError(Exception):
    pass

def death():
    ext = __DEATH_ENABLED__
    if ext:
        raise DeathError("i ded")

def censor(text, amount=False):
    if amount:
        return f"{str(text)[0:3]}{'_'*len(str(text)[3:-3])}{str(text)[-3:]}"
    # Split while capturing delimiters
    parts = re.split(r'([.,/\\\-_])', text)

    segments = parts[::2]
    delimiters = parts[1::2] + [""]

    # Indices of numeric or alphanumeric segments to censor in middle (all except first and last)
    # But censor all middle segments regardless if you want strict censor

    # We'll only keep first and last segment as-is, censor middle fully

    for i in range(1, len(segments)-1):
        seg = segments[i]
        # Replace each char with 'X' preserving length
        segments[i] = "X" * len(seg)

    # Rebuild string
    censored = "".join(seg + delim for seg, delim in zip(segments, delimiters))
    return censored

SHADOW_KEY = rw_file(get_ltools_path("shadowkey.sfef"))

def encode(text, shadowkey=SHADOW_KEY):
    out = bytearray()
    for i, c in enumerate(text):
        mult = stable_multitude(shadowkey, i)
        val = (ord(c) + mult) % 256  # <-- ord() converts char to int
        out.append(val)
    return bytes(out)

def decode(data, shadowkey=SHADOW_KEY):
    out = bytearray()
    for i, c in enumerate(data):
        mult = stable_multitude(shadowkey, i)
        val = (c - mult) % 256
        out.append(val)
    return bytes(out)

def ltools_file(filename, content=None):
    try:
        rw(get_ltools_path(filename), content)
        return True
    except:
        return False

def rwe_json(filename, content=None, E=None):
    raw = rw_file(filename)
    if not isinstance(raw, str) or raw.strip() == "":
        data = {}
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return False if content is not None else None

    if E is None:
        if content is None:
            return data
        try:
            stringified = json.dumps(content)
            return rw_file(filename, stringified) is True
        except (TypeError, ValueError):
            return False

    keys = E.strip("/").split("/")

    if content is None:
        ref = data
        for k in keys:
            if isinstance(ref, dict) and k in ref:
                ref = ref[k]
            else:
                return "mid"
        return ref

    ref = data
    for k in keys[:-1]:
        if k not in ref or not isinstance(ref[k], dict):
            ref[k] = {}
        ref = ref[k]

    try:
        ref[keys[-1]] = content
        stringified = json.dumps(data)
        return rw_file(filename, stringified) is True
    except Exception:
        return False


class FakeMessage:
    def __init__(self, content, author="Anonymous"):
        self.activity = {}
        self.application = None
        self.application_id = None
        self.attachments = []
        self.author = author
        self.call = None
        self.channel = self
        self.channel_mentions = []
        self.clean_content = content.strip()
        self.components = []
        self.content = content
        self.created_at = datetime.datetime.now()
        self.edited_at = None
        self.embeds = []
        self.flags = None
        self.guild = None
        self.id = random.randint(1_000_000, 9_999_999)
        self.interaction = None
        self.interaction_metadata = None
        self.jump_url = f"https://discord.com/channels/@me/{self.id}"
        self.mention_everyone = "@everyone" in content or "@here" in content
        self.mentions = []
        self.message_snapshots = []
        self.nonce = random.randint(100000, 999999)
        self.pinned = False
        self.poll = None
        self.position = 0
        self.purchase_notification = None
        self.raw_channel_mentions = []
        self.raw_mentions = []
        self.raw_role_mentions = []
        self.reactions = []
        self.reference = None
        self.role_mentions = []
        self.role_subscription = None
        self.stickers = []
        self.system_content = False
        self.thread = None
        self.tts = False
        self.type = "default"
        self.webhook_id = None

    def __eq__(self, other):
        return isinstance(other, FakeMessagee) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def send(self, text):
        print(f"[Channel] {text}")

    def add_files(self, files):
        self.attachments.extend(files)

    def add_reaction(self, reaction):
        self.reactions.append(reaction)

    def clear_reaction(self, reaction):
        self.reactions = [r for r in self.reactions if r != reaction]

    def clear_reactions(self):
        self.reactions.clear()

    def create_thread(self, name, auto_archive_duration=None, slowmode_delay=None, reason=None):
        self.thread = {
            "name": name,
            "auto_archive_duration": auto_archive_duration,
            "slowmode_delay": slowmode_delay,
            "reason": reason
        }

    def delete(self, delay=None):
        print(f"[Message Deleted] ID: {self.id}, Delay: {delay}")

    def edit(self, new_content):
        self.content = new_content
        self.clean_content = new_content.strip()
        self.edited_at = datetime.datetime.now()

    def end_poll(self):
        self.poll = None

    def fetch(self):
        return self

    def fetch_thread(self):
        return self.thread

    def forward(self, destination_channel, fail_if_not_exists=True):
        if destination_channel:
            destination_channel.send(self.content)

    def is_system(self):
        return self.system_content

    def pin(self, reason=None):
        self.pinned = True

    def publish(self):
        print(f"[Message Published] {self.content}")

    def remove_attachments(self):
        self.attachments = []

    def remove_reaction(self, reaction, member=None):
        if reaction in self.reactions:
            self.reactions.remove(reaction)

    def reply(self, content=None, **kwargs):
        print(f"{self.author} > {content}")

    def to_reference(self, fail_if_not_exists=True, type=None):
        return f"Message Reference ID: {self.id}"

    def unpin(self, reason=None):
        self.pinned = False
