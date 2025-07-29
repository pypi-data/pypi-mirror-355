# Quote `arg` for `cmd`

## Overview

`def quote_arg_for_cmd(string)` ensures that Python 2 `str`s and Python 3 `str`s (after encoding) are passed verbatim through `cmd.exe` to the target program's `argv[]`, by:

1. Escaping internal double quotes and backslashes
2. Quoting the entire argument to preserve spaces and special characters.
3. Escaping special characters (`^`, `&`, `|`, `<`, `>`) only outside quoted segments.

⚠️ Limitations and Warnings:

- This quoting is **only for use with** `cmd.exe` invocations (e.g., `os.system(...)` or `subprocess.Popen(..., shell=True)`).
  - ❌ **Do not use** this quoting for direct process creation via `CreateProcessA`/`CreateProcessW` (e.g., `subprocess.Popen(..., shell=False)`).
- Only supports Python 2 `str` (properly encoded) and Python 3 `str`. No support for Python 2 `unicode` or Python 3 `bytes`. No encoding conversions for Python 2 `str`.
- Escape sequences already in the string are passed verbatim, not interpreted.
- Environment variables like `%PATH%` or delayed expansion like `!VAR!` are **not processed or escaped** - these are left for `cmd.exe` to interpret.  
  - 👉 It is **your responsibility** to use such variables correctly and safely.

## Examples

- `` -> `""`
- `\` -> `"\\"`
- `"` -> `"\""`
- `\\` -> `"\\\\"`
- `""` -> `"\"\""`
- `"\` -> `"\"\\"`
- `\"` -> `"\\\""`
- `""\` -> `"\"\"\\"`
- `\""` -> `"\\\"\""`
- `"\"` -> `"\"\\\""`
- `""\\` -> `"\"\"\\\\"`
- `\\""` -> `"\\\\\"\""`
- `"\\"` -> `"\"\\\\\""`
- `C:\Documents and Settings` -> `"C:\Documents and Settings"`
- `"abc" & "def"` -> `"\"abc\" & \"def\""`
- `"abc" ^& "def"` -> `"\"abc\" ^& \"def\""`
- `"a&"b"c"d""` -> `"\"a^&\"b\"c\"d\"\""`
- `"%PATH%"` -> `"\"%PATH%\""` (`cmd.exe` will then process the `%PATH%` part)

## Test program

`print_argv.c`:

```c
#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("Received %d arguments:\n", argc);
    for (int i = 0; i < argc; i++) {
        printf("argv[%d] = `%s`\n", i, argv[i]);
    }
    return 0;
}
```

## Test cases

```
C:\>print_argv.exe ""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = ``

C:\>print_argv.exe "\\"
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `\`

C:\>print_argv.exe "\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"`

C:\>print_argv.exe "\\\\"
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `\\`

C:\>print_argv.exe "\"\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `""`

C:\>print_argv.exe "\"\\"
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"\`

C:\>print_argv.exe "\\\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `\"`

C:\>print_argv.exe "\"\"\\"
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `""\`

C:\>print_argv.exe "\\\"\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `\""`

C:\>print_argv.exe "\"\\\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"\"`

C:\>print_argv.exe "\"\"\\\\"
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `""\\`

C:\>print_argv.exe "\\\\\"\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `\\""`

C:\>print_argv.exe "\"\\\\\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"\\"`

C:\>print_argv.exe "C:\Documents and Settings"
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `C:\Documents and Settings`

C:\>print_argv.exe "\"abc\" & \"def\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"abc" & "def"`

C:\>print_argv.exe "\"abc\" ^& \"def\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"abc" ^& "def"`

C:\>print_argv.exe "\"a^&\"b\"c\"d\"\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"a&"b"c"d""`

C:\>print_argv.exe "\"%PATH%\""
Received 2 arguments:
argv[0] = `print_argv.exe`
argv[1] = `"C:\TDM-GCC-32\bin;C:\Python27\;C:\Python27\Scripts;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\;"
```

Note: The actual result of `%PATH%` will vary by system.

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
