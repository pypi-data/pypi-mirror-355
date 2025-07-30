# pyproject-appimage

![PyPI - License](https://img.shields.io/pypi/l/pyproject-appimage)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyproject-appimage)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyproject-appimage)

pyproject-appimage allows you to create a AppImage in a few seconds. To get started, just add this to your pyproject.toml:

```toml
[tool.pyproject-appimage]
script = "my-app"
output = "MyApp.AppImage"
```
`script` is here the script that should be run when executing the AppImage. You can use the `project.scripts` section of your pyproject.toml or the `entry_points` argument of your setup.py to create scripts.

To create a AppImage, just run this command in your project directory:
```
pyproject-appimage
```

## Pyproject options
The following options can be used in your pyproject.toml:

| Option | Type |Description |
| ------ | ------ | ------ |
| script | string | The script that should be run |
| output | string | The filename of your AppImage. Can be overwritten with the cli. |
| icon   | string | The path to your Icon |
| rename-icon | string | Give your Icon another name inside the AppImage |
| desktop-entry | string | The path to your .desktop file |
| rename-desktop-entry | string | Give your .desktop file another name inside the AppImage |
| gettext-desktop-entry | bool | If your .desktop file should be translated using gettest |
| appstream | string | The path to your AppStream file |
| rename-appstream | string | Give your AppStream file another name inside the AppImage |
| gettext-appstream | bool | If your AppStream file should be translated using gettest |
| gettext-directory | string | The path to your gettext directory |
| python-version | string | The Python version that is used. Default is your current version. Can be overwritten with the cli. |
| updateinformation | string | The [update information](https://github.com/AppImage/AppImageSpec/blob/master/draft.md#update-information)
| compression | string | The Squashfs compression
| additional-packages | list of strins | A list of packages that should also be installed

Note: All paths are relativ to your project directory

## Cli options
pyproject-appimage provides the following cli options:
```
usage: pyproject-appimage [-h] [--output OUTPUT] [--project-dir PROJECT_DIR] [--python-version PYTHON_VERSION] [--appimagekit-url APPIMAGEKIT_URL] [--work-dir WORK_DIR]
                          [--list-available-versions] [--no-fuse] [-v]

options:
  -h, --help            show this help message and exit
  --output OUTPUT       Sets the putput filename
  --project-dir PROJECT_DIR
                        Sets the project dir
  --python-version PYTHON_VERSION
                        Set a custom Python version
  --appimagekit-url APPIMAGEKIT_URL
                        Set a custom download URL for AppImageKit
  --work-dir WORK_DIR   Set a custom directory to work in. Existing Directories will be removed.
  --list-available-versions
                        Print available Python versions and exit
  --no-fuse             Use this, if FUSE is not available e.g. inside a Docker container
  -v, --version         Prints the version and exit
```

## Projects using pyproject-appimage
* [jdMinecraftLauncher](https://codeberg.org/JakobDev/jdMinecraftLauncher)
* [jdNBTExplorer](https://codeberg.org/JakobDev/jdNBTExplorer)
* [jdReplace](https://codeberg.org/JakobDev/jdReplace)
* [jdMrpackInstaller](https://codeberg.org/JakobDev/jdMrpackInstaller)
* [jdDesktopEntryEdit](https://codeberg.org/JakobDev/jdDesktopEntryEdit)
* [jdAppStreamEdit](https://codeberg.org/JakobDev/jdAppStreamEdit)

[pyproject-appimage is of course also available as AppImage](https://codeberg.org/JakobDev/pyproject-appimage/releases/latest)

pyproject-appimage is based [on the work of niess](https://github.com/niess/python-appimage)
