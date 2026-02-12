from os import walk
from os.path import exists, join

from pythonforandroid.recipes.pyjnius import PyjniusRecipe as BasePyjniusRecipe


class PyjniusRecipe(BasePyjniusRecipe):
    patches = []

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        source_dir = join(build_dir, "jnius")
        if not exists(source_dir):
            return

        pyx_target = join(source_dir, "jnius.pyx")
        if exists(pyx_target):
            with open(pyx_target, "r", encoding="utf-8") as f:
                pyx_content = f.read()
            compat_block = "try:\n    long\nexcept NameError:\n    long = int\n\n"
            if "long = int" not in pyx_content:
                with open(pyx_target, "w", encoding="utf-8", newline="\n") as f:
                    f.write(compat_block + pyx_content)

        for root, _, files in walk(source_dir):
            for name in files:
                if not (name.endswith(".pxi") or name.endswith(".pyx")):
                    continue
                target = join(root, name)
                with open(target, "r", encoding="utf-8") as f:
                    content = f.read()
                # pyjnius still has Python 2 `long` checks that break Cython on py3.
                content = content.replace("(int, long)", "(int,)")
                content = content.replace("isinstance(arg, long)", "False")
                content = content.replace("isinstance(py_arg, long)", "False")
                with open(target, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)


recipe = PyjniusRecipe()
