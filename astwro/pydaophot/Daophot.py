# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
from .DAORunner import DAORunner
from .OutputProviders import *
from .config import find_opt_file
import astwro.starlist as sl

class Daophot(DAORunner):
    """ **daophot** runner

    Object of this class maintains single process of **daophot** and it's working directory.

    Methods of this class corresponds to **daophot**'s commands, each of those methods
    returns result object providing access to daophot screen output as well as easy access
    to files generated by **daophot** command.
    
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
    :var str image:  image which will be automatically ATTACHed before every run
    :var  options: options which will be automatically added as OPTION command before every run,
                    can be either:
                                dictionary:
                                                        >>> dp = Daophot()
                                                        >>> dp.options = {'GAIN': 9, 'FI': '6.0'}
                                iterable of tuples:
                                                        >>> dp.options = [('GA', 9.0), ('FITTING RADIUS', '6.0')]
                                filename string of daophot.opt-formatted file:
                                                        >>> dp.options = 'config/pydaophot.opt'
    """

    def __init__(self, dir=None, image=None, daophotopt=None, options=None, batch=False):
        # type: ([str,object], [str], [str], [list,dict], bool) -> Daophot
        """
        :param str dir:          pathname or TmpDir object - working directory for daophot,
                                   if None temp dir will be used and deleted on `Daophot.close()`
        :param str image:        if provided this file will be automatically attached (AT) as first daophot command
                                   setting image property has same effect
        :param str daophotopt:   daophot.opt file, if None build in default file will be used, can be added later
                                   by `Runner.copy_to_runner_dir(file, 'daophot.opt')`
        :type options: list or str
        :param options: if provided OPTION command will be automatically attached
                                   setting options property has same effect; list of tuples or dict.
                                   Do not set WATCH PROGRESS to sth else than -2
        :param bool batch:         whether Daophot have to work in batch mode. 
        """
        self.OPtion_result = None  #: Results of command OPtion  or initial options reported by `daophot`
        if daophotopt is not None:
            self.daophotopt = daophotopt  #:str: daophotopt.opt file to be copied to *runner dir*
        else:
            self.daophotopt = find_opt_file('daophot.opt')

        self.image = image
        self.options = {'WA': -2}
        if options:
            self.options.update(dict(options))

        super(Daophot, self).__init__(dir=dir, batch=batch)
        # base implementation of __init__ calls `_reset` also
        self._update_executable('daophot')

    def _reset(self):
        super(Daophot, self)._reset()

        self.OPtion_result = None  #: Results of command OPtion  or initial options reported by `daophot`
        self.ATtach_result = None
        self.FInd_result = None
        self.PHotometry_result = None
        self.PIck_result = None
        self.PSf_result = None
        self.SOrt_result = None
        self.SUbstar_result = None
        self.GRoup_result = None
        self.NEda_result = None


    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = super(Daophot, self).__deepcopy__(memo)

        new.daophotopt = deepcopy(self.daophotopt, memo)

        new.image = deepcopy(self.image, memo)
        new.options = deepcopy(self.options, memo)
        return new

    def _pre_run(self, wait):
        super(Daophot, self)._pre_run(wait)
        if self.options:
            self._enqueueOPtions(self.options, on_beginning=True)
        if self.image:
            self._equeueATtach(self.image, on_beginning=True)

        # just for consume options daophot presents on the beginning
        opt_processor = DPOP_OPtion()
        if self.OPtion_result is None:
            self.OPtion_result = opt_processor
        self._insert_processing_step('', output_processor=opt_processor, on_beginning=True)

    def _on_exit(self):
        pass


    def _init_workdir_files(self, dir):
        super(Daophot, self)._init_workdir_files(dir)
        self.link_to_runner_dir(self.daophotopt, 'daophot.opt')


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

    def set_options(self, options, value=None):
        # type: ([str,dict,list], [str,float]) -> None
        """ Set option(s) before run. 
        
            Options can be either:
        
                dictionary:             
                                        ``dp.set_options({'GAIN': 9, 'FI': '6.0'})``
                iterable of tuples:     
                                        ``dp.set_options([('GA', 9.0), ('FITTING RADIUS', '6.0')])``
                
                option key, followed by value in 'value' parameter:
                                        ``dp.set_options('GA', 9.0)``
                                        
                filename string of allstar.opt-formatted file (file will be symlinked as `allstar.opt`):
                                        ``dp.set_options('opts/newallstar.opt')``
                                        
            .. warning:: Do not set `WATCH PROGRESS` to something else than -2
        """
        if isinstance(options, str) and value is None:  # filename
            # allstar operates in his tmp dir and has limited buffer for file path
            # so symlink file to its working dir
            self.link_to_runner_dir(options, 'daophot.opt')
        else:
            if self.options is None:
                self.options = {}
            if value is not None:  # single value
                options = {options:value}
            elif isinstance(options, list):
                options = dict(options)
            self.options.update(options)

    # daophot commands
    def ATtach(self, image_file):
        # type: (str) -> DPOP_ATtach
        """
        Add daophot ATTACH command to execution queue. Available only in "batch" mode. 
        
        If image_file parameter is provided in constructor or by set_image method, 
        ATtach is enqueued automatically (preferred method
        until multiple ATTACH commands needed in "batch" mode).
        
        :param str image_file: image to attach file will be symlinked to work dir as `i.fits`,
                   if None `i.fits` (file or symlink) is expected in working dir
        :return: DPOP_ATtach instance for getting results: ATtach_result property
        :rtype: DPOP_ATtach
        """
        if not self.batch_mode:
            raise Daophot.RunnerException('ATtach is intented for "batch" mode only. Use image property.')

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
            commands += ''.join('%s=%.2f\n' % (k,float(v)) for k,v in options if v is not None)
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
        
        Use :meth `set_options()` for options which are set after daophot process start
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
            raise Daophot.RunnerException('OPtions is intented for "batch" mode only. Use set_options().')

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
        :return: results object also accessible as `Daophot.FInd_result` property
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

    def PHotometry(self, photoopt=None, IS=0, OS=0, apertures=None, stars='i.coo', photometry_file='i.ap'):
        # type: ([str], float, float, [list], [str,sl.StarList], [str]) -> DpOp_PHotometry
        """
        Runs (or adds to execution queue in batch mode) daophot PHOTOMETRY command. 
        
        Either :param photoopt or :param photo_is, :param OS and :param photo_ap have to be set.
        :param [str] photoopt: photo.opt file to be used, default: none 
                    (provide :param photo_is, :param OS and :param photo_ap)
        :param float IS: inner sky radius, overwrites :param photoopt file value IS
        :param float OS: outer sky radius, overwrites :param photoopt file value OS
        :param [list] apertures: apertures radius, up to 12, overwrites :param photoopt file values A1, A2, ...
        :param [str, sl.StarList] stars: input list of stars, default: i.coo 
        :param [str] photometry_file: output magnitudes file 
        :return: results object also accessible as `Daophot.PHotometry_result` property
        :rtype: DpOp_PHotometry
        
        .. seealso::  :py:method:`astwro.daophot.Daophot.NAda`
        """
        # TODO: When PSF file is found, new daophot uses it and behaves differently,
        # TODO: this should be implemented as an optional parameter,
        # TODO: and not using same name for FITS and PSF by default (avoid finding PSF)
        # TODO: session:
        #           Found PSF file mik.psf
        #       Profile-fitting photometry (default mik.nst): mik.als
        #                     Star ID file (default mik.lst): mik.coo
        #                       Output file (default mik.ap): mik2.ap
        if photoopt is None and (apertures is None or IS==0 or OS==0):
            raise Daophot.RunnerValueError('Apertures and IS and OS must be provided, explicitly or as photoopt file')
        if apertures is None:
            apertures = []
        elif len(apertures) > 12:
            raise Daophot.RunnerValueError('apertures apertures list can contain maximum 12 elements')
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        l_popt, a_popt = self._prepare_input_file(photoopt)
        l_star, a_star = self._prepare_input_file(stars)
        l_phot, a_phot = self._prepare_output_file(photometry_file)

        commands = 'PHOT\n{}\n'.format(l_popt)
        if IS != 0:
            commands += 'IS={}\n'.format(IS)
        if OS != 0:
            commands += 'OS={}\n'.format(OS)
        for i, ap in enumerate(apertures):
            commands += 'A{:X}={}\n'.format(i+1, ap)
        commands += '\n{}\n{}\n'.format(l_star, l_phot)

        processor = DpOp_PHotometry(photometry_file=a_phot)
        self._insert_processing_step(commands, output_processor=processor)
        self.PHotometry_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def PIck(self, number_of_stars_to_pick=50, faintest_mag=20.0, photometry='i.ap', picked_stars_file='i.lst'):
        # type: (float, float, [str,sl.StarList], str) -> DpOp_PIck
        """
        Runs (or adds to execution queue in batch mode) daophot PICK command. 
        
        :param int: number_of_stars_to_pick
        :param float faintest_mag: instrumental magnitude for the faintest star considered to be picked
        :param str photometry: input magnitudes file, usually from aperture photometry done by :func:`PHotometry`.
        :param str picked_stars_file: output list of picked stars, default: i.lst 
        :return: results object also accessible as :var:`Daophot.PIck_result` property
        :rtype: DpOp_PIck
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        l_phot, a_phot = self._prepare_input_file(photometry)
        l_psfs, a_psfs = self._prepare_output_file(picked_stars_file)

        commands = 'PICK\n{}\n{:d},{:f}\n{}\n'.format(
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
        :return: results object also accessible as `Daophot.PSf_result` property
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
        Adds daophot SORT command to execution stack. NOT IMPLEMENTED sorry
        
        Use sorting capabilities of `StarList` and `StarList.renumber()`
        :param str file: fname.COO_FILE etc... any fname.*_FILE to sort
        :param by:  1-based column number, negative for descending order - daophot standard, or
                    one of 'id', 'x', 'y', 'mag'
        :param bool decreasing:  in not None, forces sort order
        :return: results object, also accessible as `Daophot.SOrt_result` property
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
        :return: results object, also accessible as `Daophot.SUbstar_result` property
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        l_out, a_out = self._prepare_output_file(subtracted_image)
        l_sub, a_sub = self._prepare_input_file(subtract)
        l_psf, a_psf = self._prepare_input_file(psf_file)
        if leave_in is not None:
            l_lve, a_lve = self._prepare_input_file(leave_in)
            commands = 'SUB\n{}\n{}\ny\n{}\n{}\n'.format(
                l_psf,
                l_sub,
                l_lve,
                l_out
            )
        else:
            commands = 'SUB\n{}\n{}\nn\n{}\n'.format(
                l_psf,
                l_sub,
                l_out
            )
        processor = DpOp_SUbstar(subtracted_image_file=a_out)
        self._insert_processing_step(commands, output_processor=processor)
        self.SUbstar_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def GRoup(self, photometry='i.ap', psf_file='i.psf', critical_overlap=0.1, groups_file='i.grp'):
        # type: ([str,sl.StarList], str, float, str) -> DpOp_GRoup
        """
        Runs (or adds to execution queue in batch mode) daophot GROUP command to execution stack.
        
        :param str,StarList photometry: stars to be grouped
        :param str psf_file: file with PSF
        :param float critical_overlap: relative to work dir pathname of file with PSF 
        :param str groups_file: output gouped stars file
        :return: results object, also accessible as `GRoup_result` property
        """
        self._get_ready_for_commands()  # wait for completion before changes in working dir
        l_pho, a_pho = self._prepare_input_file(photometry)
        l_psf, a_psf = self._prepare_input_file(psf_file)
        l_grp, a_grp = self._prepare_output_file(groups_file)
        commands = 'GROUP\n{}\n{}\n{}\n{}\n'.format(
            l_pho,
            l_psf,
            critical_overlap,
            l_grp
        )
        processor = DpOp_GRoup(groups_file=a_grp)
        self._insert_processing_step(commands, output_processor=processor)
        self.GRoup_result = processor
        if not self.batch_mode:
            self.run()
        return processor

    def NEda(self, photoopt=None, IS=0, OS=0, apertures=None,
             psf_file='i.psf', psf_photometry='i.als', stars_id='i.als', neda_photometry_file='i.nap'):
        # type: ([str], float, float, [list], [str], [str,sl.StarList], [str,sl.StarList], [str]) -> DpOp_NEda
        """
        Runs (or adds to execution queue in batch mode) daophot NEDA command. 
        
        Either :param photoopt or :param photo_is, :param OS and :param photo_ap have to be set.
        :param [str] photoopt: photo.opt file to be used, default: none 
                    (provide :param photo_is, :param OS and :param photo_ap)
        :param float IS: inner sky radius, overwrites :param photoopt file value IS
        :param float OS: outer sky radius, overwrites :param photoopt file value OS
        :param [list] apertures: apertures radius, up to 12, overwrites `photoopt` file values A1, A2, ...            
        :param str psf_file: file with PSF
        :param [str, sl.StarList] psf_photometry: stars with PSF photometry, default: i.als 
        :param [str, sl.StarList] stars_id: input list of stars, default: i.als
        :param str neda_photometry_file: output neda photometry file 
        :return: results object, also accessible as `NEda_result` property
        :rtype: DpOp_NEda
        """
        if photoopt is None and (apertures is None or IS==0 or OS==0):
            raise Daophot.RunnerValueError('Apertures and IS and OS must be provided, explicitly or as photoopt file')
        if apertures is None:
            apertures = []
        elif len(apertures) > 12:
            raise Daophot.RunnerValueError('apertures apertures list can contain maximum 12 elements')
        self._get_ready_for_commands()  # wait for completion before changes in working dir

        l_popt, a_popt = self._prepare_input_file(photoopt)
        l_psf,  a_psf  = self._prepare_input_file(psf_file)
        l_phot, a_phot = self._prepare_input_file(psf_photometry)
        l_star, a_star = self._prepare_input_file(stars_id)
        l_neda, a_neda = self._prepare_output_file(neda_photometry_file)

        commands = 'NEDA\n{}\n'.format(l_popt)
        if IS != 0:
            commands += 'IS={}\n'.format(IS)
        if OS != 0:
            commands += 'OS={}\n'.format(OS)
        for i, ap in enumerate(apertures):
            commands += 'A{:X}={}\n'.format(i+1, ap)
        commands += '\n{}\n{}\n{}\n{}\n'.format(
            l_psf,
            l_phot,
            l_star,
            l_neda
        )

        processor = DpOp_NEda(neda_file=a_neda)
        self._insert_processing_step(commands, output_processor=processor)
        self.NEda_result = processor
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
