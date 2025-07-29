import ast
import importlib
import inspect
import logging
import os

from japy.japy_function_wrapper import JapyFunctionWrapper

logger = logging.getLogger(__name__)

class JapyFileScanner:
    __root_dirs: list[str]

    def __init__(self, base_dir_paths: list[str]):
        self.__root_dirs = base_dir_paths

    def __find_python_files(self, root_package):
        python_files = []
        for dirpath, _, filenames in os.walk(root_package):
            for filename in filenames:
                if filename.endswith('.py'):
                    full_path = os.path.join(dirpath, filename)
                    python_files.append(full_path)
        return python_files

    def __load_imports(self, tree, func_locals=None):
        if func_locals is None:
            func_locals = {}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    module = importlib.import_module(module_name)
                    func_locals[module_name] = module
                    for attr in dir(module):
                        if not attr.startswith("__"):
                            func_locals[attr] = getattr(module, attr)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                module = importlib.import_module(module_name)
                for alias in node.names:
                    func_locals[alias.name] = getattr(module, alias.name)

        return func_locals

    def __is_japy_function(self, func):
        for decorator in func.decorator_list:
            if decorator.id == "japy_function":
                return True
        return False

    def __load_functions(self, tree, func_locals):
        functions = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and self.__is_japy_function(node):
                func_code = compile(ast.Module(body=[node], type_ignores=[]), filename="<ast>", mode="exec")
                exec(func_code, func_locals)
                functions[node.name] = node

        return func_locals, functions

    def __load_classes(self, tree, func_locals):
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                func_code = compile(ast.Module(body=[node], type_ignores=[]), filename="<ast>", mode="exec")
                exec(func_code, func_locals)

        return func_locals

    def __load_functions_for_file(self, filepath):
        with open(filepath, 'r') as file:
            source_code = file.read()

        tree = ast.parse(source_code)

        func_locals = self.__load_imports(tree)
        func_locals, functions = self.__load_functions(tree, func_locals)
        func_locals = self.__load_classes(tree, func_locals)
        return func_locals, functions

    def __to_function(self, func_name, func_locals, ast_func):
        return JapyFunctionWrapper(func_name, func_locals, ast_func)


    def scan_for_decorated_functions(self):
        python_files = [self.__find_python_files(dir) for dir in self.__root_dirs]
        all_decorated_functions = {}

        for filepaths in python_files:
            for filepath in filepaths:
                func_locals, functions = self.__load_functions_for_file(filepath)
                for func_name in functions:
                    all_decorated_functions[func_name] = self.__to_function(func_name, func_locals,
                                                                            functions[func_name])

        return all_decorated_functions


def from_relative_paths(relative_to: list[str]) -> JapyFileScanner:
    """
    Builds a JapyFileScanner from multiple paths relative to the path of the caller file.

    Example:
        - Caller filepath: /home/python/src/japy/scanner/scanner.py
        - relative_to: [../../methods]
        -> /home/python/src/methods/
    """
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    caller_file_path = caller_frame.f_code.co_filename
    base_dir = os.path.dirname(caller_file_path)
    base_dirs = [os.path.normpath(os.path.join(base_dir, relative)) for relative in relative_to]
    logger.debug(f"Searching for japy-functions in dir {base_dirs}")
    return JapyFileScanner(base_dirs)


def from_relative_path(relative_to: str) -> JapyFileScanner:
    """
    Builds a JapyFileScanner from a path relative to the path of the caller file.

    Example:
        - Caller filepath: /home/python/src/japy/scanner/scanner.py
        - relative_to: ../../methods
        -> /home/python/src/methods/
    """
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    caller_file_path = caller_frame.f_code.co_filename
    base_dir = os.path.dirname(caller_file_path)
    base_dir = os.path.normpath(os.path.join(base_dir, relative_to))
    logger.debug(f"Searching for japy-functions in dir {base_dir}")
    return JapyFileScanner([base_dir])
