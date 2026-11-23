import sys

from main import main

if __name__ == "__main__":
    sys.exit(main(["gui", "--debug", *sys.argv[1:]]))
