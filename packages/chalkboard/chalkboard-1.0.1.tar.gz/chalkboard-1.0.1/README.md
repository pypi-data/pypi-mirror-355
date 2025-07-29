# Chalkboard

"Chalkboard" is a utility package that provides advanced string formatting and ANSI colors.

## Top Features

 - Rich text formatting (all ANSI styles and colors)
 - Supports list of default colors as well as RGB and Hex colors. 
 - Easy and simple syntax
 - Seemless integration with Python CLI tools
 - Fully tested with pyest

## Installation
pip install chalkboard


## Usage

There are several options to choose from.

`from chalkboard import RichText`

**Import a pre-initialized class for your convenience**

`from chalkboard import rt`

**Import specific functions. These are just a few examples**

`from chalkboard import colorize, error, warn, ok, italicize`

## Quick Examples

```python
	from chalkboard import rt
	
	print(rt.colorize(text='Hello world', color='brightgreen'))
	
	print(rt.error(message='ERROR: Task Failed'))

	print(f'{rt.blue}Hello{rt.reset})

	print(rt.style(text='This is bold, italized, and red', color='red', bold=True, italic=True))

	print(rt.style(text='This is bold and using RGB', bold=True, r=247, g=5, b=227))


## Screenshot of some possible output
![Demo Output](https://raw.githubusercontent.com/KSimpson5624/chalkboard/main/assets/demo.png)
