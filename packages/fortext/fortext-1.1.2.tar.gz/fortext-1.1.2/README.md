# [fortext](https://4mbl.link/gh/fortext)

Text stylizer for Python. Mainly useful for CLI output.

## Table of Contents

* [Table of Contents](#table-of-contents)
  * [Installation](#installation)
* [Usage](#usage)
  * [Text styling](#text-styling)
  * [Print all styles](#print-all-styles)
  * [Syntax highlighting](#syntax-highlighting)
  * [String permutations](#string-permutations)

### Installation

Use pip to install `fortext`.

```bash
python3 -m pip install --upgrade fortext
```

## Usage

### Text styling

```python
from fortext import style, Bg, Frmt
print(style('Hi, human.', fg='#ff0000'))
print(style('RGB tuple or list also works.', fg=(0, 255, 0)))
print(style('You can also use predefined colors.', bg=Bg.BLACK))
print(style('Want to be bold?.', frmt=[Frmt.BOLD]))

print(
    style('Want to go all in?',
          fg='#ff0000', bg=Bg.BLACK,
          frmt=[Frmt.BOLD, Frmt.UNDERLINE, Frmt.ITALIC]))
```

### Print all styles

```python
from fortext import print_styles_all
print_styles_all()
```

### Syntax highlighting

```python
from fortext import highlight
print(highlight({'somekey': 'somevalue', 'anotherkey': [12.4, True, 23]}))
```

Output:

![syntax highlighting output](./img/syntax_highlighting.png)

### String permutations

```python
from fortext import permutations
for perm in permutations('abc'):
    print(perm)
```

Output:

```text
a
b
c
ab
ac
ba
bc
ca
cb
abc
acb
bac
bca
cab
cba
```
