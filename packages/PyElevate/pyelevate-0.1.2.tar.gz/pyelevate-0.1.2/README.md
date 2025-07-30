# Elevate: Request Root Privileges  

PyElevate is a small Python library that re-launches the current process with  
root/admin. This is essentially a fork of [BarneyGale's Elevate](https://github.com/barneygale/elevate) with some of the pull requests applied.  

## Usage  

To use, call `PyElevate.elevate()` early in your script. When run as root, this  
function does nothing. When not run as root, this function replaces the current  
process (Linux, macOS) or creates a new process, waits, and exits (Windows).  

There is also an `elevated()` function to check if the program is elevated.  
This will output a boolean value, with `True` meaning the program is elevated and `False` meaning it's not.

```python
from PyElevate import elevate, elevated

if not elevated():
    input("Before: " + str(elevated()) + "\nPress enter to elevate")

elevate()

input("After:" + str(elevated()) + "\nPress enter to elevate")
exit(0)
```  

On Windows, the new process's standard streams are not attached to the parent,  
which is an inherent limitation of UAC. By default, the new process runs in a  
new console window. To suppress this window, use  
`elevate(show_console=False)`.  

On Linux and macOS, graphical prompts are tried before `sudo` by default. To  
prevent graphical prompts, use `elevate(graphical=False)`.  