import subprocess
import argparse
import sys
import os
import re

def parse(argv):
    parser = argparse.ArgumentParser(description="builds ConTeXt files")
    parser.add_argument("file", metavar="f", type=str)
    return parser.parse_args()

def get_pdf_name(file):
    return os.path.splitext(os.path.basename(file))[0] + ".pdf"

def parse_error(output, encoding="ascii"):
    for line in reversed(output.decode(encoding).split("\n")):
        if re.match(r"l\.\d+.*", line):
            return "\n".join([
                line if line[-1] not in {"\n", "\r"} else line[:-1],
                "stopping"
            ])

def main():
    args = parse(sys.argv)
    print("running ConTeXt...", flush=True)
    process = subprocess.Popen(
        ["context", args.file, "--synctex=1", "--noconsole=1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, error = process.communicate()
    process.kill()
    if process.returncode == 0:
        print("success!")
        subprocess.Popen(["sumatraPDF", get_pdf_name(args.file)])
    else:
        print("error:", parse_error(out))

if __name__ == "__main__":
    main()
