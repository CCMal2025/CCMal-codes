import tolerantjson
import os.path
import tarfile
import traceback
import zipfile

from extractor.utils import purify_bash_code, remove_setup_args

class PackageExtractor:

    def __init__(self, file_path):
        if os.path.isdir(file_path):
            self.tarball_type = "dir"
            self.tar_members = []
            for filepath, dirnames, filenames in os.walk(file_path):
                for filename in filenames:
                    self.tar_members.append(os.path.relpath(os.path.join(filepath, filename), file_path))
        else:
            try:
                self.tar = tarfile.open(file_path)
                self.tar_members = [member.name for member in self.tar.getmembers()]
                self.tarball_type = "targz"
            except:
                # Maybe not a tarball
                self.tar = zipfile.ZipFile(file_path)
                self.tar_members = self.tar.namelist()
                self.tarball_type = "zip"
        self.tar_name = os.path.basename(file_path)
        self.package_path = file_path

    def load_tar_file_handler(self, path):
        if self.tarball_type == "targz":
            return self.tar.extractfile(path)
        elif self.tarball_type == "zip":
            return self.tar.open(path)
        elif self.tarball_type == "dir":
            return open(os.path.join(self.package_path, path), "rb")

    def find_package_json_script(self):
        default_package_json_path = "package/package.json"
        if default_package_json_path in self.tar_members:
            return default_package_json_path
        else:
            for member in self.tar_members:
                if member.find("package.json") != -1:
                    # print("Find package.json: ", member.name)
                    return member  # rel path
        return None

    def load_package_json_script(self, package_json_path):
        try:
            f = self.load_tar_file_handler(package_json_path)
            raw_json_str = f.read()
            json_str = raw_json_str.decode('utf-8', errors='ignore').strip()
            package_json = tolerantjson.tolerate(json_str)
        except UnicodeDecodeError as e:
            print("Cannot decode package.json", e)
            return
        except Exception as e:
            traceback.print_exc()
            print("Json decode failed of package.json", e)
            print(json_str)
            return
        if "scripts" in package_json:
            for key in package_json["scripts"]:
                if not isinstance(package_json["scripts"][key], str):
                    continue
                bash_line = package_json["scripts"][key].encode('utf-8')
                bash_line = purify_bash_code(bash_line)
                bash_line.strip()
                if len(bash_line) == 0:
                    continue
                yield key, bash_line

    def traverse_bash(self, package_json_in_one_file=False):
        package_json_path = self.find_package_json_script()
        if package_json_path is not None:
            if package_json_in_one_file:
                codes = ""
                for key, bash_code in self.load_package_json_script(package_json_path):
                    codes = codes + "\n" + bash_code
                codes.lstrip("\n")
                yield "package_json", codes
            else:
                for key, bash_code in self.load_package_json_script(package_json_path):
                    yield f"package_json_{key}", bash_code
        for path, content in self._traverse_tarfile(suffix=("sh", "bat")):
            yield path, content

    def traverse_js(self):
        return self._traverse_tarfile(suffix=("js", "ts", "cts", "mts", "mjs", "cjs"))

    def traverse_all(self):
        return self._traverse_tarfile(all_file=True)

    def _traverse_tarfile(self, all_file=False, suffix=tuple()):
        for member in self.tar_members:
            if not all_file and member.split(".")[-1] not in suffix:
                continue
            try:
                f = self.load_tar_file_handler(member)
            except KeyError as e:
                f = None
                print(e)
            if f is not None:
                yield member, f.read()

    JS_SUFFIX = ("js", "ts", "cts", "mts", "mjs", "cjs")
    PY_SUFFIX = ("py",)

    def load_packages_to_dict(self):
        packages_list = {
            "js": [],
            "py": [],
            "sh": [],
        }
        for path, code in self._traverse_tarfile(suffix=self.JS_SUFFIX + self.PY_SUFFIX):
            if not code:
                continue  # ignore those blank files
            suffix = path.split(".")[-1]
            if suffix in self.JS_SUFFIX:
                lang = "js"
            elif suffix in self.PY_SUFFIX:
                lang = "py"
                if path.find("setup.py") != -1:
                    code = remove_setup_args(code)
            else:
                continue
            packages_list[lang].append({"path": path, "code": code})

        for path, code in self.traverse_bash(False):
            packages_list["sh"].append({"path": path, "code": code})

        return packages_list

    # for testing only
    def print_package_files(self):
        for path, code in self._traverse_tarfile(suffix=('js', 'ts', 'py', 'sh')):
            if not code:
                continue  # ignore those blank files
            suffix = path.split(".")[-1]
            if suffix in ["js", "ts"]:
                lang = "js"
            elif suffix in ["py"]:
                lang = "py"
            elif suffix in ["sh"]:
                lang = "sh"
            else:
                continue
            print(lang, path, hash(code))
