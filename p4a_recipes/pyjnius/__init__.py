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
        content = content.replace(
            "if isinstance(arg, int) or (\n"
            "                    (isinstance(arg, long) and arg < 2147483648)):",
            "if isinstance(arg, int):",
        )
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)


recipe = PyjniusRecipe()
