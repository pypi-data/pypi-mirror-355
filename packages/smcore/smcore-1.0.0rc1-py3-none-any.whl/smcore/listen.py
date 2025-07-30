import os
import argparse
import sys
import asyncio
import random
from . import hardcore
from . import agent

global bb_addr
bb_addr = "localhost:8080"


class bcolors:
    OKRED = "\033[31m"
    OKGREEN = "\033[32m"
    OKYELLOW = "\033[33m"
    OKBLUE = "\033[34m"
    OKMAGENTA = "\033[35m"
    OKCYAN = "\033[36m"
    OKBBLUE = "\033[94m"
    OKBCYAN = "\033[96m"
    OKBGREEN = "\033[92m"
    ENDC = "\033[0m"
    UNDERLINE = "\033[4m"


source_colors = {
    bcolors.OKRED,
    bcolors.OKGREEN,
    bcolors.OKYELLOW,
    bcolors.OKBLUE,
    bcolors.OKMAGENTA,
    bcolors.OKCYAN,
    bcolors.OKBBLUE,
    bcolors.OKBCYAN,
    bcolors.OKBGREEN,
}


# class bcolors:
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKCYAN = '\033[96m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'


async def main():
    if bb_addr is None or bb_addr == "":
        print("Error: invalid BB address")
        sys.exit(1)
    else:
        print(f"blackboard address is: {bb_addr}")

    if bb_addr.endswith(".db") or bb_addr.endswith(".sqlite"):
        transit = hardcore.SQLiteTransit(bb_addr)
    else:
        transit = hardcore.HTTPTransit(bb_addr)

    bb = transit
    a = agent.Agent(bb)
    a.start()

    ch = await a.listen_for([])
    sources = {}
    while True:
        # await asyncio.sleep(1.0)
        # print(await a.bb.len())

        # TODO: some light formatting of the post for nicer display
        p = await ch.get()

        if p.source() not in sources:
            sources[p.source()] = random.choice(list(source_colors))

        print(
            f"{p.index():08d} {sources[p.source()]}{p.source():24s}{bcolors.ENDC} {str(p.replying_to()):8s} {[tag[0:24] for tag in p.tags()]} "
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="smcore.listen")
    ap.add_argument(
        "--addr",
        default="localhost:8080",
        help="set the blackboard address",
    )
    args = ap.parse_args()
    bb_addr = args.addr

    asyncio.run(main())
