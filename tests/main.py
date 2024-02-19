from importlib import import_module

def execute_tests(module):
    module = import_module(module)
    for key in dir(module):
        if key.startswith('test_'):
            getattr(module, key)()

def all():
    execute_tests('tests.test_insert')
    execute_tests('tests.test_select')
