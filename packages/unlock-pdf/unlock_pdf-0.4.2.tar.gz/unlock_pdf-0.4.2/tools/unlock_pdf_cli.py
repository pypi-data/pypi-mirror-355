import os
import sys
import argparse
from pathlib import Path
from unlock_pdf.core import unlock_pdf

if not __package__:
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)

def main():
    parser = argparse.ArgumentParser(
        prog='Unlock PDF',
        description="Unlock a pdf",
        epilog="Written by Elvis Mak"
        )
    parser.add_argument("path", type=str, help="Specify the file path")
    parser.add_argument("-d", "--directory", action="store_true", 
                        help='Add this flag if the path provided is a directory and you need to unlock all PDFs in that directory')
    parser.add_argument("-s", "--suffix", type=str, default="_unlocked", help="Specify the suffix for the unlocked pdf.")

    args = parser.parse_args()
    path = Path(args.path)
    print(args.directory)

    if (not args.directory) and path.is_dir():
        print("A folder is provided. Use the '-d' flag to loop through all pdfs in this folder.")
        return

    if args.directory:
        p = path.glob('**/*.pdf') # Generator object
        _ = [unlock_pdf(path=x, suffix=args.suffix) for x in p if x.is_file()] # use a list comprehension to loop through files.
        return
    else:
        unlock_pdf(path=path, suffix=args.suffix)
        return


if __name__ == "__main__":
    print("Starting Application")
    sys.exit(main())