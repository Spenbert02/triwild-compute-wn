"""
TESTED LOCALLY
"""

import argparse


def main(logfile, outfile):
    # read nums
    nums = []
    try:
        with open(logfile, 'r') as f_in:
            for line in f_in:
                parts = line.split(" ")
                if len(parts) == 10:
                    nums.append(int(parts[2][1:-4]))
    except FileNotFoundError:
        print(f"Error: log file [{logfile}] does not exist")
        return
    
    # write nums to output file
    with open(outfile, 'w') as f_out:
        for n in nums:
            f_out.write(f"{n}\n")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract completed meshes from .out file from 'compute_wn'")
    parser.add_argument("-l", "--logfile", required=True, help="Path to .out log file")
    parser.add_argument("-o", "--outfile", required=True, help="Path to output .txt file to save completed indices")
    args = parser.parse_args()
    main(args.logfile, args.outfile)
