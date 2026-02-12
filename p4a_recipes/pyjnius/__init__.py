from pythonforandroid.recipes.pyjnius import PyjniusRecipe as BasePyjniusRecipe
from os.path import exists, join


class PyjniusRecipe(BasePyjniusRecipe):
    patches = []

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        target = join(build_dir, "jnius", "jnius_utils.pxi")
        if not exists(target):
            return
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        # pyjnius uses Python 2's `long`; replace checks for Python 3 builds.
        content = content.replace("isinstance(arg, long)", "False")
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)


recipe = PyjniusRecipe()
