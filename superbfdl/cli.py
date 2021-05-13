import sys
from pathlib import Path
import os
import multiprocessing

import superbfdl.core as core
import superbfdl.util as util


def fw_download(board_model, product_id, output_dir, fw_type):
    # This path can be a dir we can use to cache all downloaded files
    dl_path = f"/tmp/downloads/{board_model}/"

    board_path = Path(f"{output_dir}/{board_model}")

    util.mkdir(dl_path)

    # 2. Search for the latest bios/firmware information
    board_info = core.get_board_info(board_model,
                                     product_id=product_id,
                                     fw_type=fw_type)

    # board_info = core.parse_results(board_info)
    fw_url = board_info['download_url']

    # download
    fw_zip = util.download_file(fw_url, dl_path)

    # Extract
    # print(f"[*] Extracting {fw_zip}")
    util.extract_zip(fw_zip, dl_path)

    fw_path = os.path.join(board_path, fw_type)

    util.mkdir(fw_path)
    fw_file = util.locate_and_move(dl_path, fw_path, fw_type)

    if fw_file:
        print(f"[*] The new {fw_type} is located at {fw_file}")
        return True
    return None


def dispatch_job(board_model, output_dir):
    # 1. Take the board, and search for the ProductID
    product_id = core.query_product_id(board_model)

    if not product_id:
        return

    print(f"[*] Product ID: {product_id}")
    fw_type = ['bios', 'ipmi']
    jobs = []

    for fw in fw_type:

        mp = multiprocessing.Process(target=fw_download,
                                     args=(board_model, product_id, output_dir,
                                           fw))
        jobs.append(mp)
        mp.start()

    for j in jobs:
        j.join()


def main(*argv):
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-b", "--board", help="Motherboard Model")
    group.add_argument("-f", "--file", help="File containing a list of Boards")
    parser.add_argument(
        "-p",
        "--path",
        default="/tmp",
        help="Directory where to save the downloaded bios/ipmi")
    args = parser.parse_args()
    if not args.path:
        args.path = "."
    output_dir = Path(args.path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.board:
        board = args.board
        dispatch_job(board, output_dir)


if __name__ == '__main__':
    main(*sys.argv)
