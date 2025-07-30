This tool is supports microcontrollers to which MicroPython is ported.

### Help
```sh
upy
```
or
```sh
upy --help
```

### Finding the serial port on a board with MicroPython
- Explore a serially connected MicroPython device.
- The MicroPython version and device type are printed. 
- Currently supported devices are Digi XBee3 and Raspberry Pi Pico 2 W

```sh
upy scan
```

- The --raw (or -r) option returns low-level board information.
```sh
upy scan -r
```

### Option Rules
- Options and values can have spaces or omit spaces.
- Options and values can be inserted with the = character.

```sh
<option><value>  
<option> <value>
<option>=<value> 
```

### Environment
- Convert a VSCode workspace into a MicroPython workspace
- Assuming the result of the scan argument is COM3
```sh
upy -sport com3 env
```

```sh
upy sport
```
```out
Current serial port: COM8
```

```sh
upy sport com4
```
```
erial port set to: COM4
```

### Initialize Microcontroller file system
- If you created MicroPython workspace in the current path, omit the --sport(or -s) options in all subsequent commands.
```sh
upy init
```

or, You can also use the --sport(or -s) options explicitly.
```sh
upy --sport <your_port_name> init
```

Behavior is not guaranteed if you explicitly specify the device name.
```sh
upy init ticle
```

### Check list of Microcontroller file systems
- If path is omitted, the output will be the files or directories contained in the top-level directory.

```sh
upy ls [<path>/][remote_directory]
```

### Put PC file or directroy into Microcontroller
- If path or remote name is omitted, a remote name identical to the local name is created in the top-level directory.
```sh
upy put <local_name> [[path][/remote_name]]
```

### Get Microcontroller file to PC
- Getting the current directory is not supported.
```sh
upy get <remote_file_name> <local_file_name>
```

### Delete Microcontroller file or directory
```sh
upy rm [path/]<remote_name>
```

### Executes the PC's MicroPython script by sequentially passing it to the Microcontroller
- Wait for serial input/output until the script finishes  
- To force quit in running state, press Ctrl+c

```sh
upy <micropython_script_file>
```
or
```sh
upy run [-i | -n] <micropython_script_file>
```

**Additional Options**
- -i: Display the pressed key in the terminal window (Echo on)
- -n: Does not wait for serial output, so it appears as if the program has terminated on the PC side.
  - Script continues to run on Microcontroller
  - Used to check data output serially from Microcontroller with other tools (PuTTY, etc.)
