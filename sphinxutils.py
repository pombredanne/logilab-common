"""
Sphinx utils:

* ModuleGenerator: Generate a file that lists all the modules of a list of
    packages in order to pull all the docstring.
    /!\ This should not be used in a makefile to systematically generate
    sphinx documentation!
"""

import os, sys
import os.path as osp


class ModuleGenerator:

    file_header = """.. -*- coding: utf-8 -*- \n\n%s\n"""
    def __init__(self, project_title, output_fn, mod_names, exclude_dirs):
        self.mod_names =  mod_names
        self.fn = open(output_fn, 'w')
        num = len(project_title) + 6
        title = "=" * num + "\n %s API\n" % project_title + "=" * num
        self.fn.write(self.file_header % title)
        self.exclude_dirs = exclude_dirs

    def make(self):
        """make the module file"""
        self.find_modules()
        self.gen_modules()
        self.done()

    def done(self):
        """close the file with the listed modules"""
        self.fn.close()

    def gen_modules(self):
        """generate all modules"""
        for mod_name in self.find_modules():
            mod_entry = """
:mod:`%s`
%s

.. automodule:: %s
   :members:
""" % (mod_name, '='*(len(':mod:``' + mod_name)), mod_name)
            self.fn.write(mod_entry)

    def find_modules(self):
        """find all python modules to be documented"""
        modules = []
        for mod_name in self.mod_names:
            for root, dirs, files in os.walk(mod_name):
                if not self.keep_module(root):
                    continue
                for name in files:
                    if name == "__init__.py":
                        self._handle_module(root, mod_name, modules)
                    elif (name.endswith(".py") and name != "__pkginfo__.py"
                          and "__init__.py" in files):
                        filename = osp.join(root, name.split('.py')[0])
                        self._handle_module(filename, mod_name, modules)
        return modules

    def _handle_module(self, filename, modname, modules):
        """handle a module"""
        if self.format_mod_name(filename, modname) not in modules:
            modules.append(self.format_mod_name(filename, modname))

    def format_mod_name(self, path, mod_name):
        mod_root = mod_name.split('/')[-1]
        mod_end = path.split(mod_root)[-1]
        return mod_root + mod_end.replace('/', '.')

    def keep_module(self, mod_end):
        """Filter modules in order to exclude specific package directories"""
        for dir in self.exclude_dirs:
            if mod_end.find(dir) != -1:
                return False
        return True

