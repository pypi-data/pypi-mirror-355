# naturalsize
A Python toolkit for getting human-readable size of file and more
## History
Originally designed only to return the human-readable size of a file,<br/>
naturalsize has developed itself to a Python toolkit with many useful functions.
## Installation
### Using *pip*
You can install naturalsize via pip using
<li>in a commandline:</li><br/>

```
py -m pip install naturalsize
```
<br/>
<li>in a python script:</li><br/>

```python
import os
os.system('py -m pip install naturalsize')
```
## Usage
naturalsize has many functions:
<li><code>about()</code> returns information about your release</li>
<li><code>nsize</code> returns the human-readable filesize:

```python
naturalsize.nsize(556677)
```
returns the size of a 556677 B large file.<br/>
The args are:<br/>
<code>size</code> for the files size in B<br/>
<code>comma</code> for the rounding of the size (default: <code>2</code>)<br/>
<code>base2</code> uses 1024 instead of 1000 as the base for the size (default: <code>True</code>)<br/>
<code>names</code> as a list of names you give to file size units (default: <code>["B", "KB", "MB", "GB", ...]</code>)</li>
<li><code>randprinter</code> prints random signs the following:

```python
naturalsize.randprinter(2000)
```
This prints 2000 random signs.<br/>
Args are:<br/>
<code>numb</code> for the number of signs (default: <code>1000</code>)<br/>
<code>signs</code> as the list signs are chosen from (default: <code>["a", "b", "c", ...]</code>)</li>
<li><code>randprinter_</code> returns a callable randprinter object with the given specifications</li>
<li><code>special_starter</code> waits for a given time and returns whether the user pressed Ctrl+c in this time:

```python
naturalsize.special_starter(100000000)
```
passes 100 000 000 times and returns then <code>False</code> if the user hasn't interrupted the process.<br/>
<code>True</code> is returned if the user interrupted.<br/>
Args are:<br/>
<code>numb</code>The number the program passes before returning <code>False</code> (default: <code>150000000</code>)</li>
<li><code>isInt</code> returns whether a given object is an integer or a float, if this is accepted via the <code>acceptFloat</code> arg</li>
<li><code>listToInt</code> sums up all integer or float, if this is accepted via the <code>acceptFloat</code> arg, and returns this<br/>
Note that the <code>acceptFloat</code> arg is <code>False</code> by default.</li>
<li><code>reverse</code> inverses the given boolean</li>
<li><code>replStr</code> replaces a part of a string the following:

```python
naturalsize.replStr(1, "adc", "b")
```
returns <code>'abc'</code> as it replaces the value at index of a string with another string.<br/>
The args are:<br/>
<code>index</code> for the index the replacement is to be at (default: <code>0</code>)<br/>
<code>strObj</code> as the string replaced in (default: <code>'a'</code>)<br/>
<code>setIn</code> as the string set in the other string (default: <code>'b'</code>)</li>
<li><code>replStrPassage</code> replaces a passage of a string using the above function the following:

```python
naturalsize.replStrPassage(1, 2, "adec", "b")
```
returns <code>'abc'</code> as it replaces the values from indexstart to indexend of a string with another string.<br/>
The <code>index</code> arg is split up into <code>indexstart</code> and <code>indexend</code> args<br/>
for the begin and the end of the to-be-replaced passage (default: <code>0</code>/<code>1</code>).

### More coming soon...