import argparse

import src.turtlebyte as turtlebyte

parser = argparse.ArgumentParser(
    prog="turtlebyte.py",
    description="A completely useless virtual memory storage device using python's turtle module."
)

parser.add_argument('-p', '--parse', help='Parse a file using turtlebyte. Can be used with -o or --output to save an image after processing. Usage: -p filepath -o target_filepath')

def write_file(source: str):
    with open(source, 'rb') as f:
        data = f.read()
    
    tb.write_bytes(b'\x00', data)

if __name__ == "__main__":
    args = parser.parse_args()

    tb = turtlebyte.Turtlebyte()

    if args.parse:
        write_file(args.parse)

    input('Press "Enter" to quit turtlebyte.py >>')
        