[app]

# (str) Title of your application
# It will appear on Android launcher
# and in the task switcher
#
#title = HorseGame
title = HorseGame

# (str) Package name
#
#package.name = horsegame
package.name = horsegame

# (str) Package domain (needed for Android/IOS packaging)
#
#package.domain = org.test
package.domain = org.horsegame

# (str) Source code where the main.py live
#
source.dir = .

# (str) The main file to be executed
#
source.main = main.py

# (list) Source files to include (let buildozer filter by extension)
#
source.include_exts = py,png,mp3,MP3

# (list) Application requirements
#
requirements = python3,kivy,libffi==3.4.4,cython==0.29.33

# (str) Application versioning (internal)
#
version = 1.0

# (str) Application icon
#
#icon.filename = %(source.dir)s/data/icon.png

# (str) Application splash screen
#
#presplash.filename = %(source.dir)s/data/presplash.png

# (list) Permissions
#
android.permissions =

# (bool) Accept Android SDK licenses automatically
android.accept_sdk_license = True

# (str) Supported orientation (one of landscape, portrait, all)
#
orientation = landscape

# (bool) Indicate if the application should be fullscreen
#
fullscreen = 1

# (list) Android architectures to build for
#
android.archs = arm64-v8a

# (int) Target Android API
#
android.api = 33

# (int) Minimum API your APK will support
#
android.minapi = 24

# (bool) Enable AndroidX
#
android.enable_androidx = True

p4a.local_recipes = ./p4a_recipes

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# (int) Number of processes to use for build
#
#build_threads = 4

# (str) Build directory
#
#build_dir = .buildozer

