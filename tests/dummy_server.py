#!/usr/bin/env python
import sys
import argparse
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f')
    parser.add_argument('-r', type=int, default=1)
    args = parser.parse_args()

    for _ in range(args.r):
        with open(args.f, 'r') as file:
            for line in file:
                sys.stdout.write(line)
                sys.stdout.flush()
                time.sleep(.1)
