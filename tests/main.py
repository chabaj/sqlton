from importlib import import_module

def execute_tests(module):
    module = import_module(module)
    for key in dir(module):
        if key.startswith('test_'):
            print(f'-- {module.__name__} -- {key}:\n')
            getattr(module, key)()
            print('')

def all():
    execute_tests('tests.test_insert')
    execute_tests('tests.test_select')
    execute_tests('tests.test_expression')
