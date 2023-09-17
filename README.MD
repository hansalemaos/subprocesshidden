# Executes subprocesses without console (Windows), reads stdout/stderr

### pip install subprocesshidden

```python

from subprocesshidden import Popen
import os

os.chdir("c:\\windows")
p1 = Popen("ls -la", timeout=1, shell=True)

p2 = Popen("dir /s", timeout=3, shell=True) # tasks are killed with taskkill

p3 = Popen("dir /xsd")


print(p1.stdout_lines)
print(p2.stdout_lines)
print(p3.stdout_lines)
print(p3.stderr_lines)
print(p2.stderr_lines)
print(p1.stderr_lines)

print(p1.stdout)
print(p2.stdout)
print(p3.stdout)
print(p3.stderr)
print(p2.stderr)
print(p1.stderr)


```
