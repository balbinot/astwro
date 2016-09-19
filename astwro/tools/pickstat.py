#! /usr/bin/env python
# coding=utf-8

from __future__ import print_function, division

from scipy.stats import sigmaclip

from astwro.pydaophot import daophot
from astwro.pydaophot import fname
from astwro.pydaophot import allstar
from astwro.starlist import read_dao_file
from astwro.starlist import write_ds9_regions
import __commons as commons

# TODO: expand this script to (optionally) leave result files - make it allstar runner
# TODO: implement creating ds9 region (why? or remove that option)

# image = args.image
# coo = args.coo
# lst = args.lst


def main(**kwargs):
    # 1 do daophot aperture and psf photometry and run allstar

    args = commons.bunch_kwargs(**kwargs)
    dp = daophot(image_file=args.image)
    dp.copy_to_working_dir(args.coo, fname.COO_FILE)
    dp.PHotometry()
    dp.copy_to_working_dir(args.lst, fname.LST_FILE)
    dp.PSf()
    dp.run(wait=True)
    al = allstar(dp.dir)
    al.run()
    all_s = read_dao_file(al.file_from_working_dir(fname.ALS_FILE))
    # all_s.hist('psf_chi')
    return sigmaclip(all_s.psf_chi)[0].mean()

    # 2 write regions
    # if args.regions:
    #
    #     write_ds9_regions(coo_file+'.reg', )


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=commons.version_string(),
        description='Runs daophot photometry and allstar. Find mean chi of allstar stars. \n\n'
                    'Takes FITS image and star lists: coo - all stars, lst - PSF stars\n'
                    'then performs daophot\'s PH, PS and allstar on them.\n'
                    '(chi is calculated by allstar for every star as \n'
                    '  \"the observed pixel-to-pixel scatter from the model image profile \n'
                    '  DIVIDED BY the expected pixel-to-pixel scatter from the image profile\").\n'
                    'The same mean chi is used as function to be minimized by genetic \n'
                    'algorithm in pickga.py. This script allows quick comparison \n'
                    'between different PSF stars sets.',)
    parser.add_argument('image', type=str,
                        help='FITS image file')
    parser.add_argument('coo', type=str,
                        help='all stars list: coo file')
    parser.add_argument('lst', type=str,
                        help='PSF stars list: lst file')
    parser.add_argument('--reg', action='store_true',
                        help='create ds9 region files <name>.coo.reg and <name>.lst.reg')
    return parser


def info():
    commons.info(__arg_parser())


if __name__ == '__main__':

    parser = __arg_parser()
    args = parser.parse_args()
    print (main(**args.__dict__))
