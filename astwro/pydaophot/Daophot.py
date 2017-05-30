# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os
from .DAORunner import DAORunner
from .OutputProviders import *
from .config import find_opt_file
import astwro.starlist as sl


# TODO: Zarządzanie listami gwiazd, poza plikami obiekty StarList - output providers

class Daophot(DAORunner):
    """ `daophot` runner

    Object of this class maintains single process of `daophot` and it's working directory.
    Methods of this class corresponds to `daophot`'s commands, each of those methods
    returns result object providing access to daophot screen output as well as easy access
    to files generated by `daophot` command.
    
    Instance attributes:
    :var str daophotopt:   daophotopt.opt file to be copied
    :var DPOP_OPtion      OPtion_result:     results of command OPtion  or initial options reported by `daophot`
    :var DPOP_ATtach      ATtach_result:     results of command ATtach
    :var DpOp_FInd        FInd_result:       results of command FInd
    :var DpOp_PHotometry  PHotometry_result: results of command PHotometry
    :var DpOp_PIck        PIck_result:       results of command PIck
    :var DpOp_PSf         PSf_result:        results of command PSf
    :var DpOp_SOrt        SOrt_result:       results of command SOrt    (not implemented)
    :var DpOp_SUbstar     SUbstar_result:    results of command SUbstar 
    :var str auto_attach:  image which will be automatically ATTACHed before every run
    :var     auto_options: options which will be automatically added as OPTION command before every run,
                    can be either:
                                dictionary:
                                                        >>> dp = Daophot()
                                                        >>> dp.auto_options = {'GAIN': 9, 'FI': '6.0'}
                                iterable of tuples:
                                                        >>> dp.auto_options = [('GA', 9.0), ('FITTING RADIUS', '6.0')]
                                filename string of daophot.opt-formatted file:
                                                        >>> dp.auto_options = 'config/pydaophot.opt'
    """

    def __init__(self, dir=None, image=None, daophotopt=None, options=None, batch=False):
        # type: ([str,object], [str], [str], [list,dict], bool) -> Daophot
        """
        :param [str] dir:          pathname or TmpDir object - working directory for daophot,
                                   if None temp dir will be used and deleted on `Daophot.close()`
        :param [str] image:        if provided this file will be automatically attached (AT) as first daophot command
                                   setting auto_attach property has same effect
        :param [str] daophotopt:   daophot.opt file, if None build in default file will be used, can be added later
                                   by `Runner.copy_to_runner_dir(file, 'daophot.opt')`
        :param [list,dict] options: if provided OPTION command will be automatically attached
                                   setting auto_options property has same effect; list of tuples or dict
        :param bool batch:         whether Daophot have to work in batch mode. 
        """
        if daophotopt is not None:
            self.daophotopt = daophotopt
        else:
            self.daophotopt = find_opt_file('daophot.opt')

        self.auto_attach = image
        self.auto_options = options

        super(Daophot, self).__init__(dir=dir, batch=batch)
        # base implementation of __init__ calls `_reset` also
        self._update_executable('daophot')

    def _reset(self):
        super(Daophot, self)._reset()

        self.OPtion_result = None
        self.ATtach_result = None
        self.FInd_result = None
        self.PHotometry_result = None
        self.PIck_result = None
        self.PSf_result = None
        self.SOrt_result = None
        self.SUbstar_result = None


    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = super(Daophot, self).__deepcopy__(memo)

        new.daophotopt = deepcopy(self.daophotopt, memo)

        # new.OPtion_result = deepcopy(self.OPtion_result, memo)
        # new.ATtach_result = deepcopy(self.ATtach_result, memo)
        # new.FInd_result = deepcopy(self.FInd_result, memo)
        # new.PHotometry_result = deepcopy(self.PHotometry_result, memo)
        # new.PIck_result = deepcopy(self.PIck_result, memo)
        # new.PSf_result = deepcopy(self.PSf_result, memo)
        # new.SOrt_result = deepcopy(self.SOrt_result, memo)
        # new.SUbstar_result = deepcopy(self.SUbstar_result, memo)

        new.auto_attach = deepcopy(self.auto_attach, memo)
        new.auto_options = deepcopy(self.auto_options, memo)
        return new

    def _pre_run(self, wait):
        super(Daophot, self)._pre_run(wait)
        if self.auto_options:
            self._enqueueOPtions(self.auto_options, on_beginning=True)
        if self.auto_attach:
            self._equeueATtach(self.auto_attach, on_beginning=True)

        # just for consume options daophot presents on the beginning
        opt_processor = DPOP_OPtion()
        if self.OPtion_result is None:
            self.OPtion_result = opt_processor
        self._insert_processing_step('', output_processor=opt_processor, on_beginning=True)

    def _on_exit(self):
        pass


    def _init_workdir_files(self, dir):
        super(Daophot, self)._init_workdir_files(dir)
        self.link_to_runner_dir(self.daophotopt)


    def _equeueATtach(self, image_file, on_beginning=False):
        # type: (str, bool) -> DPOP_ATtach
        image_file, _ = self._prepare_input_file(image_file)
        processor = DPOP_ATtach()
        self._insert_processing_step('ATTACH {}\n'.format(image_file),
                                     output_processor=processor,
                                     on_beginning = on_beginning)
        if self.ATtach_result is None or not on_beginning:
            self.ATtach_result = processor
        return processor

    # daophot commands
    def ATtach(self, image_file):
        # type: (str) -> DPOP_ATtach
        """
        Add daophot ATTACH command to execution queue. Available only in "batch" mode. 
        If image_file parameter is provided in constructor or by set_image method, 
        ATtach is enqueued automatically (preferred method
        until multiple ATTACH commands needed in "batch" mode).
        
        :param str image_file: image to attach file will be symlinked to work dir as i.fits,
                   if None 'i.fits' (file or symlink) is expected in working dir
        :return: DPOP_ATtach instance for getting results: ATtach_result property
        """
        if not self.batch_mode:
            raise Daophot.RunnerException('ATtach is intented for "batch" mode only. Use auto_attach property.')

        self._get_ready_for_commands()  # wait for completion before changes in working dir

        return self._equeueATtach(image_file)


    def EXit(self):
        self._insert_processing_step('EXIT\n', output_processor=DaophotCommandOutputProcessor())

    def _enqueueOPtions(self, options, value=None, on_beginning=False):
        # type: ([str, dict, list], [str], bool) -> DPOP_OPtion
        commands = 'OPT\n'
        if isinstance(options, str) and value is None:  # filename
            # daophot operates in his tmp dir and has limited buffer for file path
            # so symlink file to its working dir
            self._get_ready_for_commands()  # wait for completion before changes in working dir
            l_opt, a_opt = self._prepare_input_file(options)
            commands += l_opt+'\n\n'
        else:
            commands += '\n'  # answer for filename
            if value is not None:
                options = [(options,value)]  # options is str with option name and value is it's value
            elif isinstance(options, dict):
                options = options.items()   # options is dict
                                            # else options is list of pairs
            commands += ''.join('%s=%.2f\n' % (k,float(v)) for k,v in options)
            commands += '\n'
        processor = DPOP_OPtion()
        self._insert_processing_step(commands, output_processor=processor, on_beginning=on_beginning)
        if self.OPtion_result is None or not on_beginning:
            self.OPtion_result = processor
        return processor


    def OPtions(self, options, value=None):
        # type: ([str, dict, list], [str]) -> DPOP_OPtion
        """
        Adds daophot OPTION command to execution queue. Available only in "batch" mode. 
        :param options: can be either:
                dictionary:
                                        >>> dp = Daophot(mode = "batch")
                                        >>> dp.OPtions({'GAIN': 9, 'FI': '6.0'})
                iterable of tuples:
                                        >>> dp.OPtions([('GA', 9.0), ('FITTING RADIUS', '6.0')])
                option key, followed by value in 'value' parameter:
                                        >>> dp.OPtions('GA', 9.0)
                filename string of daophot.opt-formatted file:
                                        >>> dp.OPtions('config/pydaophot.opt')
        :param value: value if `options` is just single key
        :return: results object also accessible as `Daophot.OPtion_result` property
        :rtype: DPOP_OPtion
        """
        if not self.batch_mode:
            raise Daophot.RunnerException('OPtions is intented for "batch" mode only. Use auto_options property.')

        self._get_ready_for_commands()  # wait for completion before changes in working dir
        return self._enqueueOPtions(options, value)


    def FInd(self, frames_av = 1, frames_sum = 1, starlist_file='i.coo'):
        """
        Runs (or adds to execution queue in batch mode) daophot ATTACH command.
        :param int frames_av: averaged frames in image (default: 1)
        :param int frames_sum: summed frames in image (default: 1)
        :param str starlist_file: output coo file, in most cases do not change default i.coo,
            rather copy result using
            >> d.copy_from_work_dir(fname.COO_FILE, dest)
        :return: results object also accessible as `DPRunner.FInd_result` property
        :rtype: DpOp_FInd
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        local_starlist_file, abs_starlist_file = self._prepare_output_file(starlist_file)
        commands = 'FIND\n{},{}\n{}\nyes\n'.format(frames_av, frames_sum, local_starlist_file)
        processor = DpOp_FInd(starlist_file=abs_starlist_file)
        self._insert_processing_step(commands, output_processor=processor)
        self.FInd_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def PHotometry(self, photoopt=None, photo_is=0, photo_os=0, photo_ap=None, stars='i.coo', photometry_file='i.ap'):
        # type: ([str], float, float, [list], [str,sl.StarList], [str]) -> DpOp_PHotometry
        """
        Runs (or adds to execution queue in batch mode) daophot PHOTOMETRY command. 
        :param [str] photoopt: photo.opt file to be used, default: none 
                    (provide :param photo_is, :param photo_os and :param photo_ap)
        :param float photo_is: inner sky radius, overwrites :param photoopt file value IS
        :param float photo_os: outer sky radius, overwrites :param photoopt file value OS
        :param [list] photo_ap: apertures radius, up to 12, overwrites :param photoopt file values A1, A2, ...
        :param [str, sl.StarList] stars: input list of stars, default: i.coo 
        :param [str] photometry_file: output magnitudes file 
        :return: results object also accessible as `DPRunner.PHotometry_result` property
        :rtype: DpOp_PHotometry
        """
        # TODO: When PSF file is found, new daophot uses it and behaves differently,
        # TODO: this should be implemented as an optional parameter,
        # TODO: and not using same name for FITS and PSF by default (avoid finding PSF)
        # TODO: session:
        #           Found PSF file mik.psf
        #       Profile-fitting photometry (default mik.nst): mik.als
        #                     Star ID file (default mik.lst): mik.coo
        #                       Output file (default mik.ap): mik2.ap

        if photo_ap is None:
            photo_ap = []
        elif len(photo_ap) > 12:
            raise Daophot.RunnerValueError('photo_ap apertures list can contain maximum 12 elements')
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        l_popt, a_popt = self._prepare_input_file(photoopt)
        l_star, a_star = self._prepare_input_file(stars)
        l_phot, a_phot = self._prepare_output_file(photometry_file)

        commands = 'PHOT\n{}\n'.format(l_popt)
        if photo_is != 0:
            commands += 'IS={}\n'.format(photo_is)
        if photo_os != 0:
            commands += 'OS={}\n'.format(photo_os)
        for i, ap in enumerate(photo_ap):
            commands += 'A{:X}={}\n'.format(i+1, ap)
        commands += '\n{}\n{}\n'.format(l_star, l_phot)

        processor = DpOp_PHotometry(photometry_file=a_phot)
        self._insert_processing_step(commands, output_processor=processor)
        self.PHotometry_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def PIck(self, number_of_stars_to_pick=50, faintest_mag=20, photometry='i.ap', picked_stars_file='i.lst'):
        # type: (float, float, [str,sl.StarList], str) -> DpOp_PIck
        """
        Runs (or adds to execution queue in batch mode) daophot PICK command. 
        :param float number_of_stars_to_pick
        :param float faintest_mag: instrumental magnitude for the faintest star considered to be picked
        :param str photometry: input magnitudes file, usually from aperture photometry done by :func:`PHotometry`.
        :param str picked_stars_file: output list of picked stars, default: i.lst 
        :return: results object also accessible as :var:`DPRunner.PIck_result` property
        :rtype: DpOp_PIck
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        l_phot, a_phot = self._prepare_input_file(photometry)
        l_psfs, a_psfs = self._prepare_output_file(picked_stars_file)

        commands = 'PICK\n{}\n{:d},{:d}\n{}\n'.format(
            l_phot,
            number_of_stars_to_pick,
            faintest_mag,
            l_psfs
        )
        processor = DpOp_PIck(picked_stars_file=a_psfs)
        self._insert_processing_step(commands, output_processor=processor)
        self.PIck_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def PSf(self, photometry='i.ap', psf_stars='i.lst', psf_file='i.psf'):
        # type: ([str,sl.StarList],  [str,sl.StarList], str) -> DpOp_PSf
        """
        Runs (or adds to execution queue in batch mode) daophot PHOTOMETRY command. 
        :param str or sl.StarList photometry: input magnitudes file or Starlist, e.g. from aperture photometry by :func:`PHotometry`.
        :param str or sl.StarList psf_stars: input list of PSF stars, default: i.coo 
        :param str psf_file: output PSF file, default: i.psf
        :return: results object also accessible as `DPRunner.PSf_result` property
        :rtype: DpOp_PSf
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        l_phot, a_phot = self._prepare_input_file(photometry)
        l_psfs, a_psfs = self._prepare_input_file(psf_stars)
        l_psf , a_psf  = self._prepare_output_file(psf_file)
        l_nei , a_nei  = self._prepare_output_file(os.path.splitext(l_psf)[0]+'.nei')
        l_err , a_err  = self._prepare_output_file('i.err')

        commands = 'PSF\n{}\n{}\n{}\n'.format(
            l_phot,
            l_psfs,
            l_psf
        )
        processor = DpOp_PSf(psf_file=a_psf, nei_file=a_nei, err_file=a_err)
        self._insert_processing_step(commands, output_processor=processor)
        self.PSf_result = processor
        if not self.batch_mode:
            self.run()
        return processor


    def SOrt(self, file, by, decreasing=None):
        """
        Adds daophot SORT command to execution stack.
        :param str file: fname.COO_FILE etc... any fname.*_FILE to sort
        :param by:  1-based column number, negative for descending order - daophot standard, or
                    one of 'id', 'x', 'y', 'mag'
        :param bool decreasing:  in not None, forces sort order
        :return: results object, also accessible as `DPRunner.SOrt_result` property
        :rtype: DpOp_Sort
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        if isinstance(by, str):
            by = by.lower()
            if by == 'id': by = 1
            elif by == 'x': by = 2
            elif by == 'y': by = 3
            elif by == 'mag': by = 4
            else:
                raise Daophot.RunnerValueError('parameter by, if string must be either: "id", "x", "y" or "mag"')
        if decreasing is not None:
            by = -abs(by) if decreasing else abs(by)
        raise NotImplementedError("SORT command not implemented")

        if not self.batch_mode:
            self.run()

    def SUbstar(self, subtract, leave_in=None, subtracted_image='is.fits', psf_file='i.psf'):
        # type: (str, str, str, str) -> DpOp_SUbstar
        """
        Adds daophot SUBSTAR command to execution stack.
        :param subtract: relative to work dir pathname of stars to subtract file
        :param leave_in: relative to work dir pathname of stars to be kept file (default: None)
        :param psf_file: relative to work dir pathname of file with PSF (default i.psf)
        :param subtracted_image: relative to work dir pathname of output fits file (default is.fits)
        :return: results object, also accessible as `DPRunner.SUbstar_result` property
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        subtracted_image, _ = self._prepare_output_file(subtracted_image)
        subtract, _ = self._prepare_input_file(subtract)
        psf_file, _ = self._prepare_input_file(psf_file)
        if leave_in:
            leave_in, _ = self._prepare_input_file(leave_in)
            commands = 'SUB\n{}\n{}\ny\n{}\n{}\n'.format(
                psf_file,
                subtract,
                leave_in,
                subtracted_image
            )
        else:
            commands = 'SUB\n{}\n{}\nn\n{}\n'.format(
                psf_file,
                subtract,
                subtracted_image
            )
        processor = DpOp_SUbstar()
        self._insert_processing_step(commands, output_processor=processor)
        self.SUbstar_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def _process_starlist(self, s, **kwargs):
        if kwargs['add_psf_errors']:
            import pandas as pd
            err = self.PSf_result.errors
            idx = [i for i,_ in err]
            val = [v for _,v in err]
            col = pd.Series(val, index=idx)
            s['psf_err'] = col
        return s