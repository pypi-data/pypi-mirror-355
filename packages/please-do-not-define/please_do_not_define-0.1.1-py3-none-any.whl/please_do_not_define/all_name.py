import ast

class NameUsageCollector(ast.NodeVisitor):
    def __init__(self):
        self.read_names = set()
        self.write_names = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            self.write_names.add(alias.name)
            if alias.asname:
                self.write_names.add(alias.asname)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.write_names.add(alias.name)
            if alias.asname:
                self.write_names.add(alias.asname)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.read_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.write_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            if isinstance(node.value, ast.Name):
                self.read_names.add(f"{node.value.id}.{node.attr}")
            elif isinstance(node.value, ast.Attribute):
                base = self._get_attribute_chain(node.value)
                self.read_names.add(f"{base}.{node.attr}")
        elif isinstance(node.ctx, ast.Store):
            if isinstance(node.value, ast.Name):
                self.write_names.add(f"{node.value.id}.{node.attr}")
        self.generic_visit(node)
    
    def _get_attribute_chain(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_attribute_chain(node.value)
            return f"{base}.{node.attr}"
        return ""
    
    def visit_FunctionDef(self, node):
        self.write_names.add(node.name)
        for arg in node.args.args:
            self.write_names.add(arg.arg)
        if node.args.vararg:
            self.write_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            self.write_names.add(node.args.kwarg.arg)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.write_names.add(node.name)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.write_names.add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.write_names.add(elt.id)
        self.generic_visit(node)
    
    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.write_names.add(node.target.id)
            self.read_names.add(node.target.id)
        self.generic_visit(node)

def get_name_usages(code):
    tree = ast.parse(code)
    collector = NameUsageCollector()
    collector.visit(tree)
    return collector.read_names, collector.write_names

# 示例用法
if __name__ == "__main__":
    sample_code = """
import sys
from os import path

x = 10
y = x + 5

class MyClass:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        print(f"Hello, {self.name}")

def calculate(a, b=2):
    result = a * b
    return result

obj = MyClass("Test")
obj.greet()
z = calculate(x, y)
    """
    
    read_names, write_names = get_name_usages(sample_code)
    
    print("Readed:")
    for name in sorted(read_names):
        print(f"- {name}")
    
    print("\nWrited:")
    for name in sorted(write_names):
        print(f"- {name}")
