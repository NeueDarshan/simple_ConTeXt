# ------------------------------------------------------------------------------------------------------------------------------------------------- #
import subprocess
import platform
import argparse
import json
import sys
import os
import re

class PlatformNotRecognizedError(Exception):
  pass

# ------------------------------------------------------------------------------------------------------------------------------------------------- #
def parse_args():
  parser = argparse.ArgumentParser(description="builds ConTeXt files")
  parser.add_argument("packages", metavar="p", type=str, help="the location of the packages folder")
  parser.add_argument("file", metavar="f", type=str, help="the (name of the) ConTeXt file to compile")
  return parser.parse_args()

def load_settings(packages_dir):
  with open(os.path.join(packages_dir, "ConTeXtTools", "ConTeXtTools.sublime-settings")) as f:
    return json.load(f)

def prep_path(settings):
  if platform.system() == "Windows":
    pass
  elif platform.system() == "Darwin":
    tex_bin_path = os.path.join(os.path.sep, *settings.mac.tex_binaries_location)
    os.environ["PATH"] = ":".join(os.environ["PATH"].split(":") + [tex_bin_path])
  else:
    raise PlatformNotRecognizedError("Operating system not recognized!")

#def parse_error(output, encoding="ascii"):
#  for line in reversed(output.decode(encoding).split("\n")):
#    if re.match(r"l\.\d+.*", line):
#      return "\n".join([
#        line if line[-1] not in {"\n", "\r"} else line[:-1],
#        "stopping"
#      ])

def open_pdf(tex_file, pdf_app):
  pdf_name = os.path.splitext(os.path.basename(tex_file))[0] + ".pdf"
  if platform.system() == "Windows":
    cmd = [pdf_app, pdf_name]
  elif platform.system() == "Darwin":
    cmd = ["open", pdf_name, "-a", pdf_app]
  else:
    raise PlatformNotRecognizedError("Operating system not recognized!")
  subprocess.call(cmd)

# ------------------------------------------------------------------------------------------------------------------------------------------------- #
def main():
  args = parse_args()
  settings = load_settings(args.packages)
  prep_path(settings)
  print("running ConTeXt...")
  sys.stdout.flush()
  process = subprocess.Popen(
    ["context", args.file, "--synctex=1", "--noconsole=1"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT) # pipe stderr to stdout (not that we expect anything here, as context seems to only make use of stdout and not stderr)
  out, _ = process.communicate()
  # if the process still exists, make sure to close it
  try:
    process.terminate()
  except OSError as e:
    if e.errno == 3: # no such process, it's already closed
      pass
    else: # we've got the wrong guy... better re-raise the error then
      raise e
  # we're done now: if things worked then open the PDF, if not then kindly return the appropriate error message(s)
  if process.returncode == 0:
    print("success!")
    sys.stdout.flush()
    open_pdf(args.file)
  else:
    print("error:")#, parse_error(out))
    print(out)

if __name__ == "__main__":
  pass
  #main()
