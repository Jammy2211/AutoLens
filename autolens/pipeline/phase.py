from autolens.lensing import galaxy_prior as gp, lensing_image as mi
from autolens.lensing import galaxy as g
from autolens.lensing import ray_tracing
from autolens.imaging import mask as msk
from autolens.imaging import image as img
from autolens.lensing import fitting
from autolens.autofit import non_linear
from autolens.visualize import object_plotters
from autolens import exc
from autolens import conf
from astropy import cosmology as cosmo
import numpy as np
import logging
import matplotlib.pyplot as plt
import os

from autolens.pipeline.phase_property import PhasePropertyList

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


def default_mask_function(image):
    return msk.Mask.circular(image.shape, image.pixel_scale, 3.0)


class ResultsCollection(list):
    def __init__(self, results):
        super().__init__(results)

    @property
    def last(self):
        if len(self) > 0:
            return self[-1]
        return None

    @property
    def first(self):
        if len(self) > 0:
            return self[0]
        return None


class IntervalCounter(object):
    def __init__(self, interval):
        self.count = 0
        self.interval = interval

    def __call__(self):
        if self.interval == -1:
            return False
        self.count += 1
        return self.count % self.interval == 0


class HyperOnly(object):

    def hyper_run(self, image, previous_results=None):
        raise NotImplementedError()


class Phase(object):

    def __init__(self, optimizer_class=non_linear.MultiNest, phase_name=None):
        """
        A phase in an lensing pipeline. Uses the set non_linear optimizer to try to fit models and images passed to it.

        Parameters
        ----------
        optimizer_class: class
            The class of a non_linear optimizer
        phase_name: str
            The name of this phase
        """
        self.optimizer = optimizer_class(name=phase_name)
        self.phase_name = phase_name

    @property
    def constant(self):
        """
        Convenience method

        Returns
        -------
        ModelInstance
            A model instance comprising all the constant objects in this lensing
        """
        return self.optimizer.constant

    @property
    def variable(self):
        """
        Convenience method

        Returns
        -------
        ModelMapper
            A model mapper comprising all the variable (prior) objects in this lensing
        """
        return self.optimizer.variable

    @property
    def doc(self):
        if self.__doc__ is not None:
            return self.__doc__.replace("  ", "").replace("\n", " ")

    def pass_priors(self, previous_results):
        """
        Perform any prior or constant passing. This could involve setting model attributes equal to priors or constants
        from a previous phase.

        Parameters
        ----------
        previous_results: ResultsCollection
            The result of the previous phase
        """
        pass

    class Analysis(object):

        def __init__(self, phase_name, previous_results=None):
            """
            An lensing object

            Parameters
            ----------
            phase_name: str
                The name of the phase to which this analysis belongs
            previous_results: ResultsCollection
                The results of all previous phases
            """

            self.previous_results = previous_results
            self.phase_name = phase_name
            log_interval = conf.instance.general.get('output', 'log_interval', int)

            self.__should_log = IntervalCounter(log_interval)

            visualise_interval = conf.instance.general.get('output', 'visualise_interval', int)

            self.__should_visualise = IntervalCounter(visualise_interval)
            self.position_threshold = conf.instance.general.get('positions', 'position_threshold', float)
            self.plot_count = 0
            self.visualize_results = conf.instance.general.get('output', 'visualize_results', bool)
            self.as_fits_during_analysis = conf.instance.general.get('output', 'visualize_as_fits_during_analysis',
                                                                     bool)
            self.as_fits_at_end = conf.instance.general.get('output', 'visualize_as_fits_at_end', bool)
            self.output_image_path = "{}/".format(conf.instance.output_path) + '/' + self.phase_name + '/images/'
            make_path_if_does_not_exist(path=self.output_image_path)

        @property
        def should_log(self):
            return self.__should_log()

        @property
        def should_visualise(self):
            return self.__should_visualise()

        @property
        def last_results(self):
            if self.previous_results is not None:
                return self.previous_results.last

        def fit(self, instance):
            raise NotImplementedError()

        def try_visualize(self, instance):
            """
            Determine the fitness of a particular model

            Parameters
            ----------
            instance
                A model instance

            Returns
            -------
            fit: fitting.Fit
                How fit the model is and the model
            """
            if self.visualize_results:
                if self.should_log:
                    self.log(instance)
                if self.should_visualise:
                    self.plot_count += 1
                    logger.info("Saving visualisations {}".format(self.plot_count))
                    self.visualize(instance, suffix=None, during_analysis=True)
            return None

        def visualize(self, instance, suffix, during_analysis):

            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)

            return tracer, fitter

        @classmethod
        def log(cls, instance):
            raise NotImplementedError()

        def tracer_for_instance(self, instance):
            raise NotImplementedError()

        def fitter_for_tracer(self, tracer):
            raise NotImplementedError()

    class Result(non_linear.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(Phase.Result, self).__init__(constant, likelihood, variable)
            self.tracer = analysis.tracer_for_instance(constant)


class PhasePositions(Phase):
    lens_galaxies = PhasePropertyList("lens_galaxies")

    def __init__(self, lens_galaxies=None, optimizer_class=non_linear.MultiNest, phase_name=None):
        super().__init__(optimizer_class, phase_name)
        self.lens_galaxies = lens_galaxies

    def run(self, positions, pixel_scale, previous_results=None):
        """
        Run this phase.

        Parameters
        ----------
        previous_results: ResultsCollection
            An object describing the results of the last phase or None if no phase has been executed
        image: img.Image
            An lensing_image that has been masked

        Returns
        -------
        result: non_linear.Result
            A result object comprising the best fit model and other data.
        """
        analysis = self.make_analysis(positions=positions, pixel_scale=pixel_scale, previous_results=previous_results)
        result = self.optimizer.fit(analysis)
        return self.__class__.Result(result.constant, result.likelihood, result.variable, analysis)

    def make_analysis(self, positions, pixel_scale, previous_results=None):
        """
        Create an lensing object. Also calls the prior passing and lensing_image modifying functions to allow child
        classes to change the behaviour of the phase.

        Parameters
        ----------
        image: im.Image
            An lensing_image that has been masked
        previous_results: ResultsCollection
            The result from the previous phase

        Returns
        -------
        lensing: Analysis
            An lensing object that the non-linear optimizer calls to determine the fit of a set of values
        """
        self.pass_priors(previous_results)
        analysis = self.__class__.Analysis(positions=positions, pixel_scale=pixel_scale, phase_name=self.phase_name,
                                           previous_results=previous_results)
        return analysis

    class Analysis(Phase.Analysis):

        def __init__(self, positions, pixel_scale, phase_name, previous_results=None):
            super().__init__(phase_name, previous_results)

            self.positions = list(map(lambda position_set: np.asarray(position_set), positions))
            self.pixel_scale = pixel_scale

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.likelihood

        def tracer_for_instance(self, instance):
            return ray_tracing.TracerImageSourcePlanesPositions(lens_galaxies=instance.lens_galaxies,
                                                                positions=self.positions)

        def fitter_for_tracer(self, tracer):
            return fitting.PositionFitter(positions=tracer.source_plane.positions, noise=self.pixel_scale)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens lensing for... \n\nLens Galaxy::\n{}\n\n".format(instance.lens_galaxies))

    class Result(Phase.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PhasePositions.Result, self).__init__(constant, likelihood, variable, analysis)


class PhaseImaging(Phase):

    def __init__(self, optimizer_class=non_linear.MultiNest, sub_grid_size=1, image_psf_shape=None,
                 pixelization_psf_shape=None, positions=None, mask_function=default_mask_function, phase_name=None):
        """
        A phase in an lensing pipeline. Uses the set non_linear optimizer to try to fit models and images passed to it.

        Parameters
        ----------
        optimizer_class: class
            The class of a non_linear optimizer
        sub_grid_size: int
            The side length of the subgrid
        """

        super(PhaseImaging, self).__init__(optimizer_class, phase_name)
        self.sub_grid_size = sub_grid_size
        self.image_psf_shape = image_psf_shape
        self.pixelization_psf_shape = pixelization_psf_shape
        if positions is not None:
            self.positions = list(map(lambda position_set: np.asarray(position_set), positions))
        else:
            self.positions = None
        self.mask_function = mask_function

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def modify_image(self, image, previous_results):
        """
        Customize an lensing_image. e.g. removing lens light.

        Parameters
        ----------
        image: img.Image
            An lensing_image that has been masked
        previous_results: ResultsCollection
            The result of the previous lensing

        Returns
        -------
        lensing_image: img.Image
            The modified lensing_image (not changed by default)
        """
        return image

    def run(self, image, previous_results=None):
        """
        Run this phase.

        Parameters
        ----------
        previous_results: ResultsCollection
            An object describing the results of the last phase or None if no phase has been executed
        image: img.Image
            An lensing_image that has been masked

        Returns
        -------
        result: non_linear.Result
            A result object comprising the best fit model and other data.
        """
        analysis = self.make_analysis(image=image, previous_results=previous_results)
        result = self.optimizer.fit(analysis)
        if analysis.visualize_results:
            analysis.visualize(instance=result.constant, suffix=None, during_analysis=False)
        return self.__class__.Result(result.constant, result.likelihood, result.variable, analysis)

    def make_analysis(self, image, previous_results=None):
        """
        Create an lensing object. Also calls the prior passing and lensing_image modifying functions to allow child
        classes to change the behaviour of the phase.

        Parameters
        ----------
        image: im.Image
            An lensing_image that has been masked
        previous_results: ResultsCollection
            The result from the previous phase

        Returns
        -------
        lensing: Analysis
            An lensing object that the non-linear optimizer calls to determine the fit of a set of values
        """
        mask = self.mask_function(image)
        image = self.modify_image(image, previous_results)
        lensing_image = mi.LensingImage(image, mask, sub_grid_size=self.sub_grid_size,
                                        image_psf_shape=self.image_psf_shape, positions=self.positions)
        self.pass_priors(previous_results)
        analysis = self.__class__.Analysis(lensing_image=lensing_image, phase_name=self.phase_name,
                                           previous_results=previous_results)
        return analysis

    class Analysis(Phase.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):

            super(PhaseImaging.Analysis, self).__init__(phase_name, previous_results)

            self.lensing_image = lensing_image

            # self.output_array_as_png(self.lensing_image.image, 'observed_image', 'Observed Image',
            #                          self.lensing_image.grids.image.xticks, self.lensing_image.grids.image.yticks, True)

        def check_positions_trace_within_threshold(self, instance):

            if self.lensing_image.positions is not None:

                tracer = ray_tracing.TracerImageSourcePlanesPositions(lens_galaxies=instance.lens_galaxies,
                                                                      positions=self.lensing_image.positions)
                fitter = fitting.PositionFitter(positions=tracer.source_plane.positions,
                                                noise=self.lensing_image.image.pixel_scale)

                if not fitter.maximum_separation_within_threshold(self.position_threshold):
                    raise exc.RayTracingException

        def visualize(self, instance, suffix, during_analysis):

            tracer, fitter = super().visualize(instance, suffix, during_analysis)

            object_plotters.plot_image_data_from_image(image=self.lensing_image.image, units='arcsec',
                                                       output_path=self.output_image_path, output_format='png')

            object_plotters.plot_residuals_from_fitter(fitter=fitter, units='arcsec',
                                                       output_path=self.output_image_path, output_format='png')

            object_plotters.plot_chi_squareds_from_fitter(fitter=fitter, units='arcsec',
                                                          output_path=self.output_image_path, output_format='png')

            return tracer, fitter

        def map_to_1d(self, data):
            """Convinience method"""
            return self.lensing_image.mask.map_2d_array_to_masked_1d_array(data)

    class Result(Phase.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PhaseImaging.Result, self).__init__(constant, likelihood, variable, analysis)


class PositionsImagingPhase(PhaseImaging):
    lens_galaxies = PhasePropertyList("lens_galaxies")

    def __init__(self, positions, lens_galaxies=None, optimizer_class=non_linear.MultiNest,
                 phase_name="positions_phase"):
        super(PositionsImagingPhase, self).__init__(optimizer_class=optimizer_class, sub_grid_size=1,
                                                    mask_function=default_mask_function,
                                                    positions=positions, phase_name=phase_name)

        self.lens_galaxies = lens_galaxies

    class Analysis(PhaseImaging.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):
            super(PositionsImagingPhase.Analysis, self).__init__(lensing_image, phase_name, previous_results)

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.likelihood

        def visualize(self, instance, suffix, during_analysis):
            pass

        def tracer_for_instance(self, instance):
            return ray_tracing.TracerImageSourcePlanesPositions(lens_galaxies=instance.lens_galaxies,
                                                                positions=self.lensing_image.positions)

        def fitter_for_tracer(self, tracer):
            return fitting.PositionFitter(positions=tracer.source_plane.positions,
                                          noise=self.lensing_image.image.pixel_scale)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens lensing for... \n\nLens Galaxy::\n{}\n\n".format(instance.lens_galaxies))

    class Result(Phase.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PositionsImagingPhase.Result, self).__init__(constant, likelihood, variable, analysis)


class LensPlanePhase(PhaseImaging):
    """
    Fit only the lens galaxy light.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")

    def __init__(self, lens_galaxies=None, optimizer_class=non_linear.MultiNest, sub_grid_size=1, image_psf_shape=None,
                 mask_function=default_mask_function, phase_name="lens_only_phase"):
        super(LensPlanePhase, self).__init__(optimizer_class=optimizer_class, sub_grid_size=sub_grid_size,
                                             image_psf_shape=image_psf_shape,
                                             mask_function=mask_function, phase_name=phase_name)
        self.lens_galaxies = lens_galaxies


    class Analysis(PhaseImaging.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):
            super(LensPlanePhase.Analysis, self).__init__(lensing_image, phase_name, previous_results)

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            self.try_visualize(instance)
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.likelihood

        def visualize(self, instance, suffix, during_analysis):

            tracer, fitter = super().visualize(instance, suffix, during_analysis)

            object_plotters.plot_model_image_from_fitter(fitter=fitter, units='arcsec',
                                                         output_path=self.output_image_path, output_format='png')

            return tracer, fitter

        def tracer_for_instance(self, instance):
            return ray_tracing.TracerImagePlane(lens_galaxies=instance.lens_galaxies,
                                                image_grids=self.lensing_image.grids)

        def fitter_for_tracer(self, tracer):
            return fitting.ProfileFitter(lensing_image=self.lensing_image, tracer=tracer)

        def unmasked_model_image_for_instance(self, instance):
            unmasked_grids = self.lensing_image.unmasked_grids
            tracer = ray_tracing.TracerImagePlane(lens_galaxies=instance.lens_galaxies, image_grids=unmasked_grids)
            model_image_1d = unmasked_grids.image.convolve_array_1d_with_psf(tracer._image_plane_image,
                                                                           self.lensing_image.psf)
            return unmasked_grids.image.map_to_2d(model_image_1d)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens lensing for... \n\nLens Galaxy::\n{}\n\n".format(instance.lens_galaxies))


    class Result(PhaseImaging.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PhaseImaging.Result, self).__init__(constant, likelihood, variable, analysis)
            fitter = fitting.ProfileFitter(analysis.lensing_image, self.tracer)
            self.model_image = fitter.model_image
            self.lens_galaxy_model_images = fitter.model_images_of_galaxies
            self.lens_subtracted_image = analysis.lensing_image.image - fitter.model_images_of_planes[0]


class LensPlaneHyperPhase(LensPlanePhase):
    """
    Fit only the lens galaxy light.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")

    def __init__(self, lens_galaxies=None, optimizer_class=non_linear.MultiNest, sub_grid_size=1, image_psf_shape=None,
                 mask_function=default_mask_function, phase_name="lens_only_hyper_phase"):
        super(LensPlaneHyperPhase, self).__init__(lens_galaxies=lens_galaxies, optimizer_class=optimizer_class,
                                                  image_psf_shape=image_psf_shape,
                                                  sub_grid_size=sub_grid_size, mask_function=mask_function,
                                                  phase_name=phase_name)

    class Analysis(LensPlanePhase.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):
            super(LensPlanePhase.Analysis, self).__init__(lensing_image, phase_name, previous_results)
            self.hyper_model_image = self.map_to_1d(previous_results.last.model_image)
            self.hyper_galaxy_images = list(map(lambda galaxy_image: self.map_to_1d(galaxy_image),
                                                previous_results.last.lens_galaxy_model_images))
            self.hyper_minimum_values = len(self.hyper_galaxy_images) * [0.0]

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            self.try_visualize(instance)
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.likelihood

        def visualize(self, instance, suffix, during_analysis):

            tracer, fitter = super().visualize(instance, suffix, during_analysis)

            object_plotters.plot_scaled_noise_map_from_fitter(fitter=fitter, units='arcsec',
                                                              output_path=self.output_image_path, output_format='png')


            object_plotters.plot_scaled_chi_squareds_from_fitter(fitter=fitter, units='arcsec',
                                                          output_path=self.output_image_path, output_format='png')


        def fitter_for_tracer(self, tracer):
            return fitting.HyperProfileFitter(self.lensing_image, tracer, self.hyper_model_image,
                                              self.hyper_galaxy_images, self.hyper_minimum_values)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens lensing for... \n\nHyper Lens Galaxy::\n{}\n\n".format(instance.lens_galaxies))

    class Result(PhaseImaging.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PhaseImaging.Result, self).__init__(constant, likelihood, variable, analysis)


class LensLightHyperOnlyPhase(LensPlaneHyperPhase, HyperOnly):
    """
    Fit only the lens galaxy light.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")

    def __init__(self, optimizer_class=non_linear.MultiNest, sub_grid_size=1, image_psf_shape=None,
                 mask_function=default_mask_function, phase_name="lens_only_hyper_phase", hyper_index=None):
        super(LensLightHyperOnlyPhase, self).__init__(lens_galaxies=[], optimizer_class=optimizer_class,
                                                      image_psf_shape=image_psf_shape,
                                                      sub_grid_size=sub_grid_size, mask_function=mask_function,
                                                      phase_name=phase_name)

        self.hyper_index = hyper_index

    def hyper_run(self, image, previous_results=None):
        class LensGalaxyHyperPhase(LensLightHyperOnlyPhase):

            def pass_priors(self, previous_results):
                use_hyper_galaxy = len(previous_results[-1].constant.lens_galaxies) * [None]
                use_hyper_galaxy[self.hyper_index] = g.HyperGalaxy

                self.lens_galaxies = list(map(lambda lens_galaxy, use_hyper:
                                              gp.GalaxyPrior.from_galaxy(lens_galaxy, hyper_galaxy=use_hyper),
                                              previous_results.last.constant.lens_galaxies, use_hyper_galaxy))

        hyper_result = previous_results[-1]

        for i in range(len(previous_results[-1].constant.lens_galaxies)):
            phase = LensGalaxyHyperPhase(optimizer_class=non_linear.MultiNest, sub_grid_size=self.sub_grid_size,
                                         mask_function=self.mask_function,
                                         phase_name=self.phase_name + '/lens_gal_' + str(i), hyper_index=i)

            phase.optimizer.n_live_points = 20
            phase.optimizer.sampling_efficiency = 0.8
            result = phase.run(image, previous_results)
            hyper_result.constant.lens_galaxies[i].hyper_galaxy = result.constant.lens_galaxies[i].hyper_galaxy
        #    hyper_result.variable.lens_galaxies[i].hyper_galaxy = result.variable.lens_galaxies[0].hyper_galaxy

        return hyper_result

    def make_analysis(self, image, previous_results=None):
        """
        Create an lensing object. Also calls the prior passing and lensing_image modifying functions to allow child
        classes to change the behaviour of the phase.

        Parameters
        ----------
        image: im.Image
            An lensing_image that has been masked
        previous_results: ResultsCollection
            The result from the previous phase

        Returns
        -------
        lensing: Analysis
            An lensing object that the non-linear optimizer calls to determine the fit of a set of values
        """
        mask = self.mask_function(image)
        image = self.modify_image(image, previous_results)
        lensing_image = mi.LensingImage(image, mask, sub_grid_size=self.sub_grid_size)
        self.pass_priors(previous_results)
        analysis = self.__class__.Analysis(lensing_image=lensing_image, phase_name=self.phase_name,
                                           previous_results=previous_results, hyper_index=self.hyper_index)
        return analysis

    class Analysis(LensPlaneHyperPhase.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None, hyper_index=None):
            super(LensPlaneHyperPhase.Analysis, self).__init__(lensing_image, phase_name, previous_results)

            self.hyper_model_image = self.map_to_1d(previous_results.last.model_image)
            self.hyper_galaxy_images = list(map(lambda galaxy_image: self.map_to_1d(galaxy_image),
                                                previous_results.last.lens_galaxies_blurred_image_plane_images))
            self.hyper_galaxy_images = [self.hyper_galaxy_images[hyper_index]]
            self.hyper_minimum_values = len(self.hyper_galaxy_images) * [0.0]


class LensSourcePlanePhase(PhaseImaging):
    """
    Fit a simple source and lens system.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")
    source_galaxies = PhasePropertyList("source_galaxies")

    def __init__(self, lens_galaxies=None, source_galaxies=None, optimizer_class=non_linear.DownhillSimplex,
                 sub_grid_size=1, image_psf_shape=None, mask_function=default_mask_function,
                 positions=None, phase_name="source_lens_phase"):
        """
        A phase with a simple source/lens model

        Parameters
        ----------
        lens_galaxies : [g.Galaxy] | [gp.GalaxyPrior]
            A galaxy that acts as a gravitational lens
        source_galaxies: [g.Galaxy] | [gp.GalaxyPrior]
            A galaxy that is being lensed
        optimizer_class: class
            The class of a non-linear optimizer
        sub_grid_size: int
            The side length of the subgrid
        """

        super(LensSourcePlanePhase, self).__init__(optimizer_class=optimizer_class,
                                                   sub_grid_size=sub_grid_size,
                                                   image_psf_shape=image_psf_shape,
                                                   mask_function=mask_function,
                                                   positions=positions, phase_name=phase_name)
        self.lens_galaxies = lens_galaxies or []
        self.source_galaxies = source_galaxies or []

    class Analysis(PhaseImaging.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):
            self.lensing_image = lensing_image
            super(PhaseImaging.Analysis, self).__init__(phase_name, previous_results)

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            self.try_visualize(instance)
            self.check_positions_trace_within_threshold(instance)
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.likelihood

        def visualize(self, instance, suffix, during_analysis):

            tracer, fitter = super().visualize(instance, suffix, during_analysis)

            return tracer, fitter,

        def tracer_for_instance(self, instance):
            return ray_tracing.TracerImageSourcePlanes(lens_galaxies=instance.lens_galaxies,
                                                       source_galaxies=instance.source_galaxies,
                                                       image_grids=self.lensing_image.grids)

        def fitter_for_tracer(self, tracer):
            return fitting.ProfileFitter(lensing_image=self.lensing_image, tracer=tracer)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens/source lensing for... \n\nLens Galaxy:\n{}\n\nSource Galaxy:\n{}\n\n".format(
                    instance.lens_galaxies, instance.source_galaxies))

    class Result(PhaseImaging.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """

            super(PhaseImaging.Result, self).__init__(constant, likelihood, variable, analysis)

            fitter = fitting.ProfileFitter(analysis.lensing_image, self.tracer)
            self.blurred_image_plane_image = fitter.model_image
            self.source_galaxies_blurred_image_plane_images = fitter.model_images_of_galaxies


class LensSourcePlaneHyperPhase(LensSourcePlanePhase):
    """
    Fit a simple source and lens system.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")
    source_galaxies = PhasePropertyList("source_galaxies")

    def __init__(self, lens_galaxies=None, source_galaxies=None, optimizer_class=non_linear.DownhillSimplex,
                 sub_grid_size=1, positions=None, image_psf_shape=None, mask_function=default_mask_function,
                 phase_name="source_lens_phase"):
        """
        A phase with a simple source/lens model

        Parameters
        ----------
        lens_galaxies : [g.Galaxy] | [gp.GalaxyPrior]
            A galaxy that acts as a gravitational lens
        source_galaxies: [g.Galaxy] | [gp.GalaxyPrior]
            A galaxy that is being lensed
        optimizer_class: class
            The class of a non-linear optimizer
        sub_grid_size: int
            The side length of the subgrid
        """
        super(LensSourcePlaneHyperPhase, self).__init__(lens_galaxies=lens_galaxies,
                                                        source_galaxies=source_galaxies,
                                                        optimizer_class=optimizer_class, sub_grid_size=sub_grid_size,
                                                        positions=positions, image_psf_shape=image_psf_shape,
                                                        mask_function=mask_function,
                                                        phase_name=phase_name)
        self.lens_galaxies = lens_galaxies
        self.source_galaxies = source_galaxies

    class Analysis(LensSourcePlanePhase.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):
            super(LensSourcePlanePhase.Analysis, self).__init__(lensing_image, phase_name, previous_results)

            self.hyper_model_image = self.map_to_1d(previous_results.last.model_image)
            self.hyper_galaxy_images = list(map(lambda galaxy_image: self.map_to_1d(galaxy_image),
                                                previous_results.last.source_galaxies_blurred_image_plane_images))
            self.hyper_minimum_values = len(self.hyper_galaxy_images) * [0.0]

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.likelihood

        def visualize(self, instance, suffix, during_analysis):

            tracer, fitter = super().visualize(instance, suffix, during_analysis)

        def fitter_for_tracer(self, tracer):
            return fitting.HyperProfileFitter(self.lensing_image, tracer, self.hyper_model_image,
                                              self.hyper_galaxy_images, self.hyper_minimum_values)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens/source lensing for... \n\nLens Galaxy:\n{}\n\nSource Galaxy:\n{}\n\n".format(
                    instance.lens_galaxies, instance.source_galaxies))

    class Result(PhaseImaging.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PhaseImaging.Result, self).__init__(constant, likelihood, variable, analysis)


class LensMassAndSourceProfileHyperOnlyPhase(LensSourcePlaneHyperPhase, HyperOnly):
    """
    Fit only the lens galaxy light.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")
    source_galaxies = PhasePropertyList("source_galaxies")

    def __init__(self, optimizer_class=non_linear.MultiNest, sub_grid_size=1, image_psf_shape=None,
                 mask_function=default_mask_function, phase_name="source_and_len_hyper_phase", hyper_index=None):
        super(LensMassAndSourceProfileHyperOnlyPhase, self).__init__(lens_galaxies=[], source_galaxies=[],
                                                                     optimizer_class=optimizer_class,
                                                                     sub_grid_size=sub_grid_size,
                                                                     image_psf_shape=image_psf_shape,
                                                                     mask_function=mask_function,
                                                                     phase_name=phase_name)
        self.hyper_index = hyper_index

    def hyper_run(self, image, previous_results=None):
        class SourceGalaxyHyperPhase(LensMassAndSourceProfileHyperOnlyPhase):
            def pass_priors(self, previous_results):
                use_hyper_galaxy = len(previous_results[-1].constant.source_galaxies) * [None]
                use_hyper_galaxy[self.hyper_index] = g.HyperGalaxy

                self.lens_galaxies = previous_results[-1].variable.lens_galaxies
                self.lens_galaxies[0].sie = previous_results[0].constant.lens_galaxies[0].sie
                self.source_galaxies = list(map(lambda source_galaxy, use_hyper:
                                                gp.GalaxyPrior.from_galaxy(source_galaxy, hyper_galaxy=use_hyper),
                                                previous_results.last.constant.source_galaxies, use_hyper_galaxy))

        overall_result = previous_results[-1]

        for i in range(len(previous_results[-1].constant.source_galaxies)):
            phase = SourceGalaxyHyperPhase(optimizer_class=non_linear.MultiNest,
                                           sub_grid_size=self.sub_grid_size, mask_function=self.mask_function,
                                           phase_name=self.phase_name + '/src_gal_' + str(i), hyper_index=i)

            phase.optimizer.n_live_points = 20
            phase.optimizer.sampling_efficiency = 0.8
            result = phase.run(image, previous_results)
            overall_result.constant.source_galaxies[i].hyper_galaxy = result.constant.source_galaxies[i].hyper_galaxy

        return overall_result

    def make_analysis(self, image, previous_results=None):
        """
        Create an lensing object. Also calls the prior passing and lensing_image modifying functions to allow child
        classes to change the behaviour of the phase.

        Parameters
        ----------
        image: im.Image
            An lensing_image that has been masked
        previous_results: ResultsCollection
            The result from the previous phase

        Returns
        -------
        lensing: Analysis
            An lensing object that the non-linear optimizer calls to determine the fit of a set of values
        """
        mask = self.mask_function(image)
        image = self.modify_image(image, previous_results)
        lensing_image = mi.LensingImage(image, mask, sub_grid_size=self.sub_grid_size)
        self.pass_priors(previous_results)
        analysis = self.__class__.Analysis(lensing_image=lensing_image, phase_name=self.phase_name,
                                           previous_results=previous_results, hyper_index=self.hyper_index)
        return analysis

    class Analysis(LensSourcePlaneHyperPhase.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None, hyper_index=None):
            super(LensSourcePlaneHyperPhase.Analysis, self).__init__(lensing_image, phase_name, previous_results)

            self.hyper_model_image = self.map_to_1d(previous_results.last.model_image)
            self.hyper_galaxy_images = list(map(lambda galaxy_image: self.map_to_1d(galaxy_image),
                                                previous_results.last.source_galaxies_blurred_image_plane_images))
            self.hyper_galaxy_images = [self.hyper_galaxy_images[hyper_index]]
            self.hyper_minimum_values = len(self.hyper_galaxy_images) * [0.0]


class LensMassAndSourcePixelizationPhase(PhaseImaging):
    """
    Fit a simple source and lens system.
    """

    lens_galaxies = PhasePropertyList("lens_galaxies")
    source_galaxies = PhasePropertyList("source_galaxies")

    def __init__(self, lens_galaxies, source_galaxies, optimizer_class=non_linear.DownhillSimplex,
                 sub_grid_size=1, image_psf_shape=None, pixelization_psf_shape=None,
                 mask_function=default_mask_function, positions=None,
                 phase_name="source_lens_phase"):
        """
        A phase with a simple source/lens model

        Parameters
        ----------
        lens_galaxies : [g.Galaxy] | [gp.GalaxyPrior]
            A galaxy that acts as a gravitational lens
        source_galaxies: [g.Galaxy] | [gp.GalaxyPrior]
            A galaxy that is being lensed
        optimizer_class: class
            The class of a non-linear optimizer
        sub_grid_size: int
            The side length of the subgrid
        """

        super(LensMassAndSourcePixelizationPhase, self).__init__(optimizer_class=optimizer_class,
                                                                 sub_grid_size=sub_grid_size,
                                                                 image_psf_shape=image_psf_shape,
                                                                 pixelization_psf_shape=pixelization_psf_shape,
                                                                 mask_function=mask_function,
                                                                 positions=positions, phase_name=phase_name)
        self.lens_galaxies = lens_galaxies
        self.source_galaxies = source_galaxies

    class Analysis(PhaseImaging.Analysis):

        def __init__(self, lensing_image, phase_name, previous_results=None):
            super().__init__(lensing_image, phase_name, previous_results)

        def fit(self, instance):
            """
            Determine the fit of a lens galaxy and source galaxy to the lensing_image in this lensing.

            Parameters
            ----------
            instance
                A model instance with attributes

            Returns
            -------
            fit: Fit
                A fractional value indicating how well this model fit and the model lensing_image itself
            """
            self.check_positions_trace_within_threshold(instance)
            self.try_visualize(instance)
            tracer = self.tracer_for_instance(instance)
            fitter = self.fitter_for_tracer(tracer)
            return fitter.evidence

        def visualize(self, instance, suffix, during_analysis):
            tracer, fitter = super().visualize(instance, suffix, during_analysis)

        def tracer_for_instance(self, instance):
            return ray_tracing.TracerImageSourcePlanes(lens_galaxies=instance.lens_galaxies,
                                                       source_galaxies=instance.source_galaxies,
                                                       image_grids=self.lensing_image.grids)

        def fitter_for_tracer(self, tracer):
            return fitting.PixelizationFitter(lensing_image=self.lensing_image, tracer=tracer)

        @classmethod
        def log(cls, instance):
            logger.debug(
                "\nRunning lens/source lensing for... \n\nLens Galaxy:\n{}\n\nSource Galaxy:\n{}\n\n".format(
                    instance.lens_galaxies, instance.source_galaxies))

    class Result(PhaseImaging.Result):

        def __init__(self, constant, likelihood, variable, analysis):
            """
            The result of a phase
            """
            super(PhaseImaging.Result, self).__init__(constant, likelihood, variable, analysis)
            # tracer = lensing.tracer_for_instance(constant)
            # self.image_plane_source_galaxy_images = self.galaxy_images_from_plane(lensing, tracer.source_plane.galaxy_images,
            #                                                               tracer.source_plane.image_plane_galaxy_blurring_images)

        # @property
        # def source_plane_blurred_image_plane_image(self):
        #     return sum(self.image_plane_source_galaxy_images)


class MultiPlanePhase(PhaseImaging):

    def __init__(self, galaxies=None, optimizer_class=non_linear.DownhillSimplex,
                 sub_grid_size=1, image_psf_shape=None, mask_function=default_mask_function,
                 positions=None, phase_name="source_lens_phase", cosmology=cosmo.LambdaCDM):
        super(MultiPlanePhase, self).__init__()

        pass


def make_path_if_does_not_exist(path):
    if os.path.exists(path) == False:
        os.makedirs(path)
