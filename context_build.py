import subprocess
import argparse
import platform
import sys
import os
import re

MAC_TEX_BIN_DIR = os.path.join(os.path.sep, "usr", "texbin")
MAC_PDF_APP = "Skim"
WIN_PDF_APP = "SumatraPDF"

class PlatformNotRecognizedError(Exception):
  pass

def parse():
  parser = argparse.ArgumentParser(description="builds ConTeXt files")
  parser.add_argument("file", metavar="f", type=str, help="the (name of the) ConTeXt file to compile")
  return parser.parse_args()

def parse_error(output, encoding="ascii"):
  for line in reversed(output.decode(encoding).split("\n")):
    if re.match(r"l\.\d+.*", line):
      return "\n".join([
        line if line[-1] not in {"\n", "\r"} else line[:-1],
        "stopping"
      ])

def get_pdf_name(tex_file):
  return os.path.splitext(os.path.basename(tex_file))[0] + ".pdf"

def open_pdf(tex_file):
  if platform.system() == "Windows":
    cmd = [WIN_PDF_APP, get_pdf_name(tex_file)]
  elif platform.system() == "Darwin":
    cmd = ["open", get_pdf_name(tex_file), "-a", MAC_PDF_APP]
  else:
    raise PlatformNotRecognizedError("Operating system not recognized!")
  subprocess.check_call(cmd)

def main():
  args = parse()
  # append the location of all the tex binaries to PATH
  os.environ["PATH"] = ":".join(os.environ["PATH"].split(":") + [MAC_TEX_BIN_DIR])
  # call ConTeXt on the file
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
    print("error:", parse_error(out))

if __name__ == "__main__":
  main()
