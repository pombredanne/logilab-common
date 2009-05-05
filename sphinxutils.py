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
    def __init__(self, project_title, code_dir, dest_file):
        self.main_dir = code_dir
        self.dest_file = dest_file
        self.set_docdir()
        self.mod_names = []
        self.title = project_title

    def set_docdir(self, subfolder =""):
        """set the directory for the destination path"""
        self.output_fn = osp.join(self.main_dir, subfolder, self.dest_file)

    def make(self, mod_names, exclude_dirs):
        """make the module file"""
        self.mod_names = [osp.join(self.main_dir, name) for name in mod_names]
        self.exclude_dirs = exclude_dirs
        self.fn = open(self.output_fn, 'w')
        num = len(self.title) + 6
        title = "=" * num + "\n %s API\n" % self.title + "=" * num
        self.fn.write(self.file_header % title)
        self.find_modules()
        self.gen_modules()
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


def generate_modules_file(args):
    """generate all module files"""
    # TODO : use lgc options
    if len(args) != 3:

        print """
Two arguments required:
    generate_modules [project-title] [code-dir] [file-out]

[project-title] : title of the project to be documented
[code-dir] : full path to the code directory
[file-out] : rest file containing the list of modules for Sphinx
"""
        sys.exit()
    project_title = args[0]
    code_dir = args[1]
    destfile = args[2]
    mg = ModuleGenerator(project_title, code_dir, destfile)
    return mg

if __name__ == '__main__':
    # example :
    mg = generate_modules_file(sys.argv[1:])
    modnames = ['logilab']
    exclude = ('test', 'tests', 'examples', 'data', 'doc', '.hg', 'migration')
    mg.make(mod_names, exclude)

