#!/usr/bin/env python
"""
`di_bq.py` is a wrapper around the standard ceda-di tools to help parallelise
the processing of files using a batch queue.

This tool has two main functions:
    * Generate lists of files to be processed in individual jobs by the queue
    * Dispatch archive processing jobs to the batch queue

Usage:
    di_bq.py (--help | --version)
    di_bq.py gen-list <input-dir> <file-list-output-dir> [--num=<num>]
    di_bq.py submit-jobs <dir-containing-file-lists> [--delete-after]
    di_bq.py submit-job <individual-file-list> [--delete-after]

Options:
    --help              Show this screen.
    --version           Show version.
    --num=<num>         Number of paths to store in each file [default: 5000].
    --delete-after      Delete input files after job submission.
"""

import simplejson as json
import os

from docopt import docopt

from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract
import ceda_di.util.cmd as cmd


def dump_to_json(output_directory, seq, file_list):
    """
    Write the object specified in "file_list" to a JSON file list.

    :param str output_directory: The directory to write all of the files into.
    :param int seq: The sequence number of the file.
    :param list file_list: The list of files to serialise to JSON.
    """
    out_name = "{seq}.json".format(seq=seq)
    out_path = os.path.join(output_directory, out_name)

    with open(out_path, "w") as out_f:
        json.dump(file_list, out_f)


def construct_bsub_command(path, params={}):
    # Mapping of "bsub" command parameters to what they mean
    bsub_param = {
        "stdout": "-o",
        "stderr": "-e",
        "num-cores": "-n",
        "queue": "-q",
        "walltime": "-W",
        "jobname": "-J"
    }

    """
    command = "bsub"
    for k, v in params.iteritems():
        if k in bsub_param:
            opt = " {option} {value}".format(option=bsub_param[k], value=v)
            command += opt
    """
    command = "" ## RMEOVE
    print("PATH: " + path)
    command += " python {script} submit-job {args}".format(script=__file__,
                                                           args=path)
    return command


def bsub(path, params={}):
    """
    Submit job to batch queue for processing.
    """
    defaults = {
        "stdout": "%J.o",
        "stderr": "%J.e",
        "num-cores": 10,
        "queue": "lotus",
        "walltime": 45,
        "jobname": "ceda-di"
    }
    defaults.update(params)

    bsub_cmd = construct_bsub_command(path, defaults)
    os.system(bsub_cmd)
    print(bsub_cmd)


def main():
    # Get arguments from command line
    args = cmd.sanitise_args(docopt(__doc__, version=__version__))
    if 'config' not in args or not args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../config/ceda_di.json")
        args["config"] = conf_path

    config = cmd.get_settings(args["config"], args)
    if args["gen-list"]:
        # Set up variables from command-line parameters
        path = args["input-dir"]
        output_directory = args["file-list-output-dir"]
        max_files = int(args["num"])
        seq = 0

        # Begin sweeping for files
        flist = []
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                flist.append(fp)

                # Dump file paths to JSON document
                if len(flist) >= max_files:
                    dump_to_json(output_directory, seq, flist)
                    seq += 1  # Increment file sequence number
                    flist = []

        # Dump anything left over to JSON
        dump_to_json(output_directory, seq, flist)

    elif args["submit-jobs"]:
        input_directory = args["dir-containing-file-lists"]

        for root, dirs, files in os.walk(input_directory):
            for f in files:
                fp = os.path.join(root, f)

                # Submit job to batch queue
                bsub(fp)

    elif args["submit-job"]:
        file_list = args["individual-file-list"]
        with open(file_list, "r") as f:
            files = json.load(f)

        extract = Extract(config, files)
        extract.run()

if __name__ == "__main__":
    main()
