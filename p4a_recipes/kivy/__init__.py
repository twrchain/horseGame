from os import walk
from os.path import exists, join

from pythonforandroid.recipes.kivy import KivyRecipe as BaseKivyRecipe


class KivyRecipe(BaseKivyRecipe):
    patches = []

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        source_dir = join(build_dir, "kivy")
        if not exists(source_dir):
            return

        compat_block = "try:\n    long\nexcept NameError:\n    long = int\n\n"
        for root, _, files in walk(source_dir):
            for name in files:
                if not name.endswith(".pyx"):
                    continue
                target = join(root, name)
                with open(target, "r", encoding="utf-8") as f:
                    content = f.read()
                if "long" in content and "long = int" not in content:
                    content = compat_block + content
                content = content.replace("return long(", "return int(")
                content = content.replace("(int, long)", "(int,)")
                with open(target, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)


recipe = KivyRecipe()
