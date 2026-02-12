from pythonforandroid.recipes.libffi import LibffiRecipe as BaseLibffiRecipe


class LibffiRecipe(BaseLibffiRecipe):
    # Upstream tag names include the leading 'v', e.g. v3.4.4, so override the URL
    url = "https://github.com/libffi/libffi/archive/refs/tags/v{version}.tar.gz"


recipe = LibffiRecipe()
