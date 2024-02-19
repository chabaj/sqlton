# SQLTOn

SQLTOn parse sql statements (according to Sqlite3 gramar description) into a easily browseable/processable tree.

```python
from sqlton import parse
from sqlton.ast import Select

statement = parse('select Something from SomeTable whern SomethingElse=SomeValue')
if not isinstance(statement, Select):
	print('only select statement are accepted')
	exit()
	
if not hasattr(statement, 'limit'):
	print('select statement shall have a limit clause !')
	exit()
	
def compute(expression):
	...
	
if compute(statement.limit[0]) > 100:
	print('too much entry requested !')
```
