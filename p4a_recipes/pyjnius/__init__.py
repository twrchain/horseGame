from pythonforandroid.recipes.pyjnius import PyjniusRecipe as BasePyjniusRecipe


class PyjniusRecipe(BasePyjniusRecipe):
    # Fix Python 3 build: replace obsolete `long` checks in jnius_utils.pxi
    patches = ['pyjnius-long-py3.patch']


recipe = PyjniusRecipe()
