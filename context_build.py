import subprocess
import platform
import argparse
import json
import sys
import os

class PlatformNotRecognizedError(Exception):
    pass

def parse_args():
    parser = argparse.ArgumentParser(description="builds ConTeXt files")
    parser.add_argument(
        "packages",
        metavar="p",
        type=str,
        help="the location of the packages folder")
    parser.add_argument(
        "file",
        metavar="f",
        type=str,
        help="the (name of the) ConTeXt file to compile")
    return parser.parse_args()

def load_settings(packages_dir):
    with open(os.path.join(
        packages_dir,
        "ConTeXtTools",
        "ConTeXtTools.sublime-settings")) \
    as f:
        return json.load(f)

def prep_path(settings):
    if platform.system() == "Windows":
        pass
    elif platform.system() == "Darwin":
        tex_bin_path = os.path.join(
            os.path.sep,
            *settings["mac"]["tex_binaries_location"])
        os.environ["PATH"] = ":".join(
            os.environ["PATH"].split(":") + [tex_bin_path])
    else:
        raise PlatformNotRecognizedError("Operating system not recognized!")

def open_pdf(tex_file, settings):
    pdf_name = os.path.splitext(os.path.basename(tex_file))[0] + ".pdf"
    if platform.system() == "Windows":
        pdf_app = settings["windows"]["PDF_viewer"]
        cmd = [pdf_app, pdf_name]
    elif platform.system() == "Darwin":
        pdf_app = settings["mac"]["PDF_viewer"]
        cmd = ["open", pdf_name, "-a", pdf_app]
    else:
        raise PlatformNotRecognizedError("Operating system not recognized!")
    subprocess.call(cmd)

def main():
    # initial stuff
    args = parse_args()
    settings = load_settings(args.packages)
    prep_path(settings)
    print("running ConTeXt...")
    sys.stdout.flush()
    # run ConTeXt
    process = subprocess.Popen(
        ["context", args.file, "--synctex=1", "--noconsole=1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    out, _ = process.communicate()
    # if the process still exists, make sure to close it
    try:
        process.terminate()
    except OSError as e:
        if e.errno == 3:  # no such process, it's already closed
            pass
        else:  # we've got the wrong guy... better re-raise the error then
            raise e
    # if things worked then open the PDF, if not then report what errors
    # occurred
    if process.returncode == 0:
        print("success!")
        sys.stdout.flush()
        open_pdf(args.file, settings)
    else:
        print("error:")
        # eventually let's parse the output and print the portion of it that
        # describes the error... for now, simply print everything
        print(out)

if __name__ == "__main__":
    main()
