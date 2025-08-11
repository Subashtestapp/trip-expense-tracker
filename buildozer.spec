[app]
# (str) Title of your application
title = Trip Expense Tracker

# (str) Package name
package.name = tripexpensetracker

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy,jnius

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

[android]
# (str) Android SDK version to use
api = 31

# (str) Android NDK version to use
ndk = 23b

# (bool) Use --private data storage (True) or --dir public storage (False)
private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#ndk_dir = 

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#sdk_dir = 

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1