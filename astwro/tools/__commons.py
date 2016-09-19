from __future__ import print_function, division


def bunch_kwargs(**kwargs):
    from collections import namedtuple
    """Makes object from arguments dict. used to have common interface
    for arguments passed to main() from command line or calling script."""
    return namedtuple('ArgsBunch', kwargs.keys())(*kwargs.values())


def version_string():
    import _version
    return 'AstWro tools v. {} [github.com/majkelx/astwro]'.format(_version.__version__)


def main_info():
    return 'For use in script call main(**kwargs), with command line arguments as named arguments'


def info(parser):
    parser.print_help()
    print (main_info())

