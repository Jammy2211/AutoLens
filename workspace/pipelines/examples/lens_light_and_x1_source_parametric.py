from autofit import conf
from autofit.optimize import non_linear as nl
from autofit.mapper import model_mapper as mm
from autolens.data import ccd
from autolens.data.array import mask as msk
from autolens.model.galaxy import galaxy_model as gm
from autolens.pipeline import phase as ph
from autolens.pipeline import pipeline
from autolens.model.profiles import light_profiles as lp
from autolens.model.profiles import mass_profiles as mp
from autolens.data.plotters import ccd_plotters

import os

# In this pipeline, we'll perform a basic analysis which fits a source galaxy using a parametric light profile and a
# lens galaxy where its light is included and fitted, using three phases:

# Phase 1) Fit the lens galaxy's light using an elliptical Sersic light profile.

# Phase 2) Use this lens subtracted image to fit the lens galaxy's mass (SIE+Shear) and source galaxy's light (Sersic).

# Phase 3) Fit the lens's light, mass and source's light simultaneously using priors initialized from the above 2 phases.

# Get the relative path to the config files and output folder in our workspace.
path = '{}/../../'.format(os.path.dirname(os.path.realpath(__file__)))

# There is a x2 '/../../' because we are in the 'workspace/pipelines/examples' folder. If you write your own pipeline \
# in the 'workspace/pipelines' folder you should remove one '../', as shown below.
# path = '{}/../'.format(os.path.dirname(os.path.realpath(__file__)))

# Use this path to explicitly set the config path and output papth
conf.instance = conf.Config(config_path=path+'config', output_path=path+'output')

# It is convenient to specify the lens name as a string, so that if the pipeline is applied to multiple images we \
# don't have to change all of the path entries in the load_ccd_data_from_fits function below.
lens_name = 'lens_light_and_x1_source'

ccd_data = ccd.load_ccd_data_from_fits(image_path=path + '/data/example/' + lens_name + '/image.fits', pixel_scale=0.1,
                                       psf_path=path+'/data/example/'+lens_name+'/psf.fits',
                                       noise_map_path=path+'/data/example/'+lens_name+'/noise_map.fits')

# It is generally a good idea to plot the image before you run a pipeline, and make sure your mask is appropriately \
# sized. The default mask used by PyAutoLens is a 3.0" circle, so that's the mask I'm plotting below.
# (checkout the 'mask_and_positions.py' example pipeline to see how to setup a custom mask for an image)

mask = msk.Mask.circular(shape=ccd_data.shape, pixel_scale=ccd_data.pixel_scale, radius_arcsec=3.0)

ccd_plotters.plot_ccd_subplot(ccd_data=ccd_data, mask=mask)

def make_lens_light_and_x1_source_parametric_pipeline(pipeline_name):

    ### PHASE 1 ###

    # In phase 1, we will fit only the lens galaxy's light, where we:

    # 1) Set our priors on the lens galaxy (y,x) centre such that we assume the image is centred around the lens galaxy.
    # 2) Use a circular mask which therefore also includes the source's light.

    # Whereas in the howtolens tutorial I used an anti-annular mask in this phase to remove the source galaxy, here I
    # use the default 3.0"  circular mask. In general, I haven't found the choice of mask to make a big difference,
    # albeit this does depend on how much off the lens galaxy's light the lensed source galaxy's light obstructs.

    class LensPhase(ph.LensPlanePhase):

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.light.centre_0 = mm.GaussianPrior(mean=0.0, sigma=0.1)
            self.lens_galaxies.lens.light.centre_1 = mm.GaussianPrior(mean=0.0, sigma=0.1)

    phase1 = LensPhase(lens_galaxies=dict(lens=gm.GalaxyModel(light=lp.EllipticalSersic)),
                       optimizer_class=nl.MultiNest, phase_name=pipeline_name + '/phase_1_lens_light_only')

    # You'll see these lines throughout all of the example pipelines. They are used to make MultiNest sample the \
    # non-linear parameter space faster (if you haven't already, checkout 'tutorial_7_multinest_black_magic' in
    # 'howtolens/chapter_2_lens_modeling'.

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 30
    phase1.optimizer.sampling_efficiency = 0.3

    ### PHASE 2 ###

    # In phase 2, we will fit the lens galaxy's mass and source galaxy's light, where we:

    # 1) Use a lens-subtracted image generated by subtracting model lens galaxy image from phase 1.
    # 2) Use a circular annular mask to only include the source-galaxy.
    # 3) Initialize the priors on the centre of the lens galaxy's mass-profile by linking them to those inferred for \
    #    its light profile in phase 1.

    def mask_function(image):
        return msk.Mask.circular_annular(shape=image.shape, pixel_scale=image.pixel_scale,
                                         inner_radius_arcsec=0.3, outer_radius_arcsec=3.0)

    class LensSubtractedPhase(ph.LensSourcePlanePhase):

        def modify_image(self, image, previous_results):
            return image - previous_results[-1].unmasked_model_image

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.mass.centre_0 = previous_results[0].variable.lens.light.centre_0
            self.lens_galaxies.lens.mass.centre_1 = previous_results[0].variable.lens.light.centre_1

    phase2 = LensSubtractedPhase(lens_galaxies=dict(lens=gm.GalaxyModel(mass=mp.EllipticalIsothermal,
                                                                        shear=mp.ExternalShear)),
                                 source_galaxies=dict(source=gm.GalaxyModel(light=lp.EllipticalSersic)),
                                 optimizer_class=nl.MultiNest, mask_function=mask_function,
                                 phase_name=pipeline_name + '/phase_2_source_only')

    phase2.optimizer.const_efficiency_mode = True
    phase2.optimizer.n_live_points = 60
    phase2.optimizer.sampling_efficiency = 0.2

    ### PHASE 3 ###

    # In phase 3, we will fit simultaneously the lens and source galaxies, where we:

    # 1) Initialize the lens's light, mass, shear and source's light using the results of phases 1 and 2.

    class LensSourcePhase(ph.LensSourcePlanePhase):

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.light = previous_results[0].variable.lens.light
            self.lens_galaxies.lens.mass = previous_results[1].variable.lens.mass
            self.lens_galaxies.lens.shear = previous_results[1].variable.lens.shear
            self.source_galaxies.source = previous_results[1].variable.source

    phase3 = LensSourcePhase(lens_galaxies=dict(lens=gm.GalaxyModel(light=lp.EllipticalSersic,
                                                                    mass=mp.EllipticalIsothermal,
                                                                    shear=mp.ExternalShear)),
                             source_galaxies=dict(source=gm.GalaxyModel(light=lp.EllipticalSersic)),
                             optimizer_class=nl.MultiNest, phase_name=pipeline_name + '/phase_3_both')

    phase3.optimizer.const_efficiency_mode = True
    phase3.optimizer.n_live_points = 75
    phase3.optimizer.sampling_efficiency = 0.3

    return pipeline.PipelineImaging(pipeline_name, phase1, phase2, phase3)


pipeline_lens_light_and_x1_source_parametric = \
    make_lens_light_and_x1_source_parametric_pipeline(pipeline_name='example/lens_light_and_x1_source_parametric')

pipeline_lens_light_and_x1_source_parametric.run(data=ccd_data)