from pythonforandroid.recipes.pyjnius import PyjniusRecipe as BasePyjniusRecipe
from os.path import exists, join


class PyjniusRecipe(BasePyjniusRecipe):
    patches = []

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        source_dir = join(build_dir, "jnius")
        if not exists(source_dir):
            return

        for name in ("jnius_utils.pxi", "jnius_conversion.pxi"):
            target = join(source_dir, name)
            if not exists(target):
                continue
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            # pyjnius still has Python 2 `long` checks that break Cython on py3.
            content = content.replace("isinstance(arg, (int, long))", "isinstance(arg, int)")
            content = content.replace("isinstance(py_arg, (int, long))", "isinstance(py_arg, int)")
            content = content.replace("isinstance(arg, long)", "False")
            with open(target, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)


recipe = PyjniusRecipe()
