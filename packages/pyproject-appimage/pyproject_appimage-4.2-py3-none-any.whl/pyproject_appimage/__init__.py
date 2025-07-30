from typing import Optional, Any, TypedDict
import desktop_entry_lib
import subprocess
import argparse
import requests
import platform
import tempfile
import pathlib
import shutil
import sys
import os


try:
    from tomllib import load as toml_load
except ModuleNotFoundError:
    from tomli import load as toml_load


PYPROJECT_SECTION = "tool.pyproject-appimage"


PyprojectDict = TypedDict("PyprojectDict", {
    "script": str,
    "icon": str,
    "rename-icon": str,
    "desktop-entry": str,
    "rename-desktop-entry": str,
    "gettext-desktop-entry": bool,
    "appstream": str,
    "rename-appstream": str,
    "gettext-appstream": bool,
    "gettext-directory": str,
    "python-version": str,
    "output": str
}, total=False)


def read_pyproject_file(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        try:
            return toml_load(f)
        except Exception as ex:
            if len(ex.args) == 1:
                print("Error while parsing " + os.path.join(args.project_dir, "pyproject.toml") + f": {ex.args[0]}", file=sys.stderr)
            else:
                print("Error while parsing " + os.path.join(args.project_dir, "pyproject.toml"), file=sys.stderr)
            sys.exit(1)


def check_key(project_dir: str, pyproject: PyprojectDict, key: str, error_list: list[str], checks: list[str]) -> None:
    if key not in pyproject:
        if "required" in checks:
            error_list.append(f"\"{key}\" is required but not present")
        return

    if "string" in checks:
        if not isinstance(pyproject[key], str):
            error_list.append(f"\"{key}\" must be a string")
        elif pyproject[key].strip() == "":
            error_list.append(f"\"{key}\" must not be empty")
        elif "path" in checks and not os.path.exists(os.path.join(project_dir, pyproject[key])):
            error_list.append("The path " + os.path.join(project_dir, pyproject[key]) + f" for \"{key}\" is not valid")
    if "bool" in checks:
        if not isinstance(pyproject[key], bool):
            error_list.append(f"\"{key}\" must be a bool")
    if "string-list" in checks:
        if not isinstance(pyproject[key], list):
            error_list.append(f"\"{key}\" must be a list of strings")
        else:
            for i in pyproject[key]:
                if not isinstance(i, str):
                    error_list.append(f"\"{key}\" must be a list of strings")


def check_pyproject(project_dir: str, pyproject: PyprojectDict) -> None:
    error_list: list[str] = []

    check_key(project_dir, pyproject, "script", error_list, ["required", "string"])
    check_key(project_dir, pyproject, "icon", error_list, ["string", "path"])
    check_key(project_dir, pyproject, "rename-icon", error_list, ["string"])
    check_key(project_dir, pyproject, "desktop-entry", error_list, ["string", "path"])
    check_key(project_dir, pyproject, "rename-desktop-entry", error_list, ["string"])
    check_key(project_dir, pyproject, "gettext-desktop-entry", error_list, ["bool"])
    check_key(project_dir, pyproject, "appstream", error_list, ["string", "path"])
    check_key(project_dir, pyproject, "rename-appstream", error_list, ["string"])
    check_key(project_dir, pyproject, "gettext-appstream", error_list, ["bool"])
    check_key(project_dir, pyproject, "gettext-directory", error_list, ["string", "path"])
    check_key(project_dir, pyproject, "python-version", error_list, ["string"])
    check_key(project_dir, pyproject, "output", error_list, ["string"])
    check_key(project_dir, pyproject, "updateinformation", error_list, ["string"])
    check_key(project_dir, pyproject, "compression", error_list, ["string"])
    check_key(project_dir, pyproject, "additional-packages", error_list, ["string-list"])

    if ("gettext-desktop-entry" in pyproject or "gettext-appstream" in pyproject) and not "gettext-directory" in pyproject:
        error_list.append("\"gettext-directory\" must be set when using gettext")

    if "gettext-directory" in pyproject and shutil.which("msgfmt") is None:
        error_list.append("msgfmt must be installed when using gettext")

    if len(error_list) > 0:
        print(f"There are errors in the {PYPROJECT_SECTION} section of your pyproject.toml:", file=sys.stderr)
        print("\n".join(error_list), file=sys.stderr)
        sys.exit(1)


def download_file(url: str, path: str) -> None:
    print(f"Download {url} as {path}")
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f"{url} returns {r.status_code}", file=sys.stderr)
        sys.exit(1)
    with open(path, "wb") as f:
        shutil.copyfileobj(r.raw, f)


def get_python_download_link(version: str) -> str:
    for i in requests.get("https://api.github.com/repos/niess/python-appimage/releases").json():
        if i["tag_name"] == f"python{version}":
            for asset in i["assets"]:
                if asset["name"].endswith("manylinux2014_x86_64.AppImage"):
                    return asset["browser_download_url"]
    return None


def get_exec_prefix(app_root: str) -> Optional[str]:
    try:
        result = subprocess.run([os.path.join(app_root, "usr", "bin", "python"), "-c", "import sys; print(sys.exec_prefix)"], capture_output=True, check=True)
        return result.stdout.decode("utf-8").strip()
    except Exception:
        return None


def find_script(app_root: str, name: str) -> Optional[str]:
    usr_path = os.path.join(app_root, "usr", "bin", name)
    if os.path.isfile(usr_path):
        return usr_path

    if (exec_prefix := get_exec_prefix(app_root)) is not None:
        prefix_path = os.path.join(exec_prefix, "bin", name)
        if os.path.isfile(prefix_path):
            return prefix_path

    return None


def get_image_magick_command(work_dir: str) -> str:
    if shutil.which("magick") is not None:
        return "magick"

    work_magick = os.path.join(work_dir, "magick")

    if os.path.isfile(work_magick):
        return work_magick

    download_file("https://download.imagemagick.org/ImageMagick/download/binaries/magick", work_magick)
    subprocess.run(["chmod", "+x", work_magick], check=True)
    return work_magick


def get_icon_size(work_dir: str, icon_path: str) -> tuple[int, int]:
    cmd = [get_image_magick_command(work_dir), "identify", "-format", '%w %h', icon_path]
    size = subprocess.run(cmd, check=True, capture_output=True).stdout.decode("utf-8")
    width, height = size.split(" ")
    return (int(width), int(height))


def handle_icon(project_dir: str, work_dir: str, app_root: str, pyproject: PyprojectDict) -> None:
    if "icon" not in pyproject:
        shutil.copyfile(os.path.join(os.path.dirname(__file__), "default.png"), os.path.join(app_root, ".DirIcon"))
        shutil.copyfile(os.path.join(os.path.dirname(__file__), "default.png"), os.path.join(app_root, "pyproject-appimage-default.png"))
        return

    icon_path = os.path.join(project_dir, pyproject["icon"])

    if icon_path.endswith(".png"):
        shutil.copyfile(icon_path, os.path.join(app_root, ".DirIcon"))
    else:
        # If a Icon is not PNG, convert it
        if icon_path.endswith(".svg"):
            # https://stackoverflow.com/a/55370062
            subprocess.run([get_image_magick_command(work_dir), "-background", "none", icon_path, "PNG:" + os.path.join(app_root, ".DirIcon")], check=True)
        else:
            subprocess.run([get_image_magick_command(work_dir), icon_path, "PNG:" + os.path.join(app_root, ".DirIcon")], check=True)

    if "rename-icon" in pyproject:
        icon_name = pyproject["rename-icon"]
    else:
        icon_name = os.path.basename(pyproject["icon"])

    shutil.copyfile(icon_path, os.path.join(app_root, icon_name))

    if icon_name.endswith(".svg"):
        icon_dir = os.path.join(app_root, "usr", "share", "icons", "hicolor", "scalable", "apps")
    else:
        icon_size = get_icon_size(work_dir, os.path.join(app_root, icon_name))
        icon_dir = os.path.join(app_root, "usr", "share", "icons", "hicolor", f"{icon_size[0]}x{icon_size[1]}", "apps")

    if not os.path.isdir(icon_dir):
        os.makedirs(icon_dir)

    shutil.copyfile(os.path.join(app_root, icon_name), os.path.join(icon_dir, icon_name))


def create_desktop_entry(project_dir: str, app_root: str, pyproject: PyprojectDict) -> None:
    full_pyproject = read_pyproject_file(os.path.join(project_dir, "pyproject.toml"))

    entry = desktop_entry_lib.DesktopEntry()

    if "project" in full_pyproject:
        entry.Name.default_text = full_pyproject["project"].get("name", "App")
        if "description" in full_pyproject["project"]:
            entry.Comment.default_text = full_pyproject["project"]["description"]
    else:
        entry.Name.default_text = "App"

    entry.Icon = "pyproject-appimage-default"
    entry.Exec = pyproject["script"]

    entry.Categories.append("Utility")

    entry.write_file(os.path.join(app_root, "pyproject-appimage-default.desktop"))


def handle_desktop_entry(project_dir: str, app_root: str, pyproject: PyprojectDict) -> None:
    if "desktop-entry" not in pyproject:
        create_desktop_entry(project_dir, app_root, pyproject)
        return

    desktop_source_path = os.path.join(project_dir, pyproject["desktop-entry"])
    desktop_dest_path = os.path.join(app_root, pyproject.get("rename-desktop-entry", os.path.basename(pyproject["desktop-entry"])))

    if pyproject.get("gettext-desktop-entry", False):
        subprocess.run(["msgfmt", "--desktop", "--template", desktop_source_path, "-d", os.path.join(project_dir, pyproject["gettext-directory"]), "-o", desktop_dest_path], check=True)
    else:
        shutil.copyfile(desktop_source_path, desktop_dest_path)

    desktop_share_dir = os.path.join(app_root, "usr", "share", "applications")

    if not os.path.isdir(desktop_share_dir):
        os.makedirs(desktop_share_dir)

    shutil.copyfile(desktop_dest_path, os.path.join(desktop_share_dir, os.path.basename(desktop_dest_path)))


def build_appimage(project_dir: str, work_dir: str, pyproject: PyprojectDict, args: argparse.Namespace) -> None:
    if args.python_version is not None:
        python_version = args.python_version
    elif "python-version" in pyproject:
        python_version = pyproject["python-version"]
    else:
        python_version = platform.python_version_tuple()[0] + "." + platform.python_version_tuple()[1]

    download_link = get_python_download_link(python_version)

    if download_link is None:
        print(f"Python version {python_version} is not aviable. Use --list-available-versions to get all aviable versions.", file=sys.stderr)
        sys.exit(1)

    download_file(download_link, os.path.join(work_dir, "Python.AppImage"))

    if args.appimagekit_url:
        download_file(args.appimagekit_url, os.path.join(work_dir, "Appimagetool.AppImage"))
    else:
        download_file("https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage", os.path.join(work_dir, "Appimagetool.AppImage"))

    subprocess.run(["chmod", "+x", os.path.join(work_dir, "Python.AppImage")], check=True)
    subprocess.run(["chmod", "+x", os.path.join(work_dir, "Appimagetool.AppImage")], check=True)

    subprocess.run([os.path.join(work_dir, "Python.AppImage"), "--appimage-extract"], cwd=work_dir, check=True, stdout=subprocess.DEVNULL)

    app_root = os.path.join(work_dir, "squashfs-root")

    shutil.rmtree(os.path.join(work_dir, "squashfs-root", "usr", "share"))
    for i in os.listdir(app_root):
        full_path = os.path.join(app_root, i)
        if os.path.isfile(full_path) or os.path.islink(full_path):
            os.remove(full_path)

    subprocess.run([os.path.join(app_root, "usr", "bin", "pip"), "install", "--no-warn-script-location", project_dir], check=True)

    script_path = find_script(app_root, pyproject["script"])
    if script_path is None:
        print("The script " + pyproject["script"] + " was not found")
        sys.exit(1)

    app_run = os.path.join(app_root, "AppRun")

    with open(app_run, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\n")
        f.write('exec "${APPDIR}/usr/bin/python" "${APPDIR}/' + str(pathlib.Path(script_path).relative_to(app_root)) + '" "$@"\n')

    subprocess.run(["chmod", "+x", app_run], check=True)

    handle_icon(project_dir, work_dir, app_root, pyproject)

    handle_desktop_entry(project_dir, app_root, pyproject)

    if "appstream" in pyproject:
        appstream_path = os.path.join(app_root, "usr", "share", "metainfo")

        appstream_source_path = os.path.join(project_dir, pyproject["appstream"])
        appstream_dest_path = os.path.join(appstream_path, pyproject.get("rename-appstream", os.path.basename(pyproject["appstream"])))

        # .metainfo.xml is currently not supported by AppImage
        if appstream_dest_path.endswith(".metainfo.xml"):
            appstream_dest_path = appstream_dest_path.removesuffix(".metainfo.xml") + ".appdata.xml"

        if not os.path.isdir(appstream_path):
            os.makedirs(appstream_path)

        if pyproject.get("gettext-desktop-entry", False):
            subprocess.run(["msgfmt", "--xml", "--template", appstream_source_path, "-d", os.path.join(project_dir, pyproject["gettext-directory"]), "-o", appstream_dest_path], check=True)
        else:
            shutil.copyfile(appstream_source_path, appstream_dest_path)

    if "additional-packages" in pyproject:
        subprocess.run([os.path.join(app_root, "usr", "bin", "pip"), "install"] +  pyproject["additional-packages"], check=True)

    if args.output is not None:
        output = args.output
    elif "output" in pyproject:
        output = pyproject["output"]
    else:
        output = "MyApp.AppImage"

    imagetool_cmd = [os.path.join(work_dir, "Appimagetool.AppImage")]

    if args.no_fuse:
        imagetool_cmd.append("--appimage-extract-and-run")

    if "updateinformation" in pyproject:
        imagetool_cmd.append("--updateinformation")
        imagetool_cmd.append(pyproject["updateinformation"])

    if "compression" in pyproject:
        imagetool_cmd.append("--comp")
        imagetool_cmd.append(pyproject["compression"])

    imagetool_cmd.append("--no-appstream")
    imagetool_cmd.append(app_root)
    imagetool_cmd.append(output)

    subprocess.run(imagetool_cmd, check=True)

    print()
    print(f"Saving AppImage as {os.path.abspath(output)}")


def list_available_versions() -> None:
    version_dict: dict[int, list[int]] = {}
    for i in requests.get("https://api.github.com/repos/niess/python-appimage/releases").json():
        version_split = i["tag_name"].removeprefix("python").split(".")

        if int(version_split[0]) not in version_dict:
            version_dict[int(version_split[0])] = []

        version_dict[int(version_split[0])].append(int(version_split[1]))

    for key in sorted(version_dict.keys()):
        for value in sorted(version_dict[key]):
            print(f"{key}.{value}")


def get_toml_section(data: dict[str, Any], name: str) -> Optional[dict[str, Any]]:
    current_data = data
    for i in name.split("."):
        if i not in current_data:
            return None

        current_data = current_data[i]

    return current_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Sets the putput filename")
    parser.add_argument("--project-dir", help="Sets the project dir", default=os.getcwd())
    parser.add_argument("--python-version", help="Set a custom Python version")
    parser.add_argument("--appimagekit-url", help="Set a custom download URL for AppImageKit")
    parser.add_argument("--work-dir", help="Set a custom directory to work in. Existing Directories will be removed.")
    parser.add_argument("--list-available-versions", action="store_true", help="Print available Python versions and exit")
    parser.add_argument("--no-fuse", action="store_true", help="Use this, if FUSE is not available e.g. inside a Docker container")
    parser.add_argument("-v", "--version", action="store_true", help="Prints the version and exit")
    parser.prog = "pyproject-appimage"
    args = parser.parse_args()

    if args.version:
        with open(os.path.join(os.path.dirname(__file__), "version.txt"), "r", encoding="utf-8") as f:
            print("pyproject-appimage " + f.read().strip())
        sys.exit(0)

    if args.list_available_versions:
        list_available_versions()
        sys.exit(0)

    if not os.path.isfile(os.path.join(args.project_dir, "pyproject.toml")):
        print(os.path.join(args.project_dir, "pyproject.toml") + " does not exists", file=sys.stderr)
        sys.exit(1)

    data = read_pyproject_file(os.path.join(args.project_dir, "pyproject.toml"))

    pyproject = get_toml_section(data, PYPROJECT_SECTION)

    if pyproject is None:
        print(os.path.join(args.project_dir, "pyproject.toml") + " has no section " + PYPROJECT_SECTION, file=sys.stderr)
        sys.exit(1)

    check_pyproject(args.project_dir, pyproject)

    if args.work_dir is not None:
        try:
            shutil.rmtree(args.work_dir)
        except Exception:
            pass

        try:
            os.makedirs(args.work_dir)
        except Exception:
            pass

        try:
            build_appimage(args.project_dir, os.path.abspath(args.work_dir), pyproject, args)
        except subprocess.CalledProcessError as ex:
            print("Error while running " + str(ex.cmd), file=sys.stderr)
            sys.exit(1)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                build_appimage(args.project_dir, tmpdir, pyproject, args)
            except subprocess.CalledProcessError as ex:
                print("Error while running " + str(ex.cmd), file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
