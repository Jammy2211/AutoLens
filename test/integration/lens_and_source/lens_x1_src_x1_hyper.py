from autolens.pipeline import pipeline as pl
from autolens.pipeline import phase as ph
from autolens.profiles import light_profiles as lp
from autolens.profiles import mass_profiles as mp
from autolens.lensing import galaxy_model as gm
from autolens.autofit import non_linear as nl
from autolens.autofit import model_mapper as mm
from autolens.lensing import galaxy
from autolens import conf
from test.integration import tools

import numpy as np
import shutil
import os

dirpath = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(dirpath)
output_path = '/gpfs/data/pdtw24/Lens/int/lens_mass_source/'

def test_lens_x1_src_x1_profile_hyper_pipeline():

    pipeline_name = "l1_s1_hyp"
    data_name = '/l1_s1_hyp'

    try:
        shutil.rmtree(dirpath+'/data'+data_name)
    except FileNotFoundError:
        pass

    lens_mass = mp.EllipticalIsothermal(centre=(0.01, 0.01), axis_ratio=0.8, phi=80.0, einstein_radius=1.6)
    
    source_bulge_0 = lp.EllipticalSersic(centre=(0.01, 0.01), axis_ratio=0.9, phi=90.0, intensity=1.0,
                                         effective_radius=1.0, sersic_index=4.0)

    source_bulge_1 = lp.EllipticalSersic(centre=(0.1, 0.1), axis_ratio=0.9, phi=90.0, intensity=1.0,
                                         effective_radius=1.0, sersic_index=4.0)

    lens_galaxy = galaxy.Galaxy(sie=lens_mass)
    source_galaxy = galaxy.Galaxy(bulge_0=source_bulge_0, bulge_1=source_bulge_1)

    tools.simulate_integration_image(data_name=data_name, pixel_scale=0.2, lens_galaxies=[lens_galaxy],
                                     source_galaxies=[source_galaxy], target_signal_to_noise=30.0)

    conf.instance.output_path = output_path

    try:
        shutil.rmtree(output_path + pipeline_name)
    except FileNotFoundError:
        pass

    pipeline = make_lens_x1_src_x1_profile_hyper_pipeline(pipeline_name=pipeline_name)
    image = tools.load_image(data_name=data_name, pixel_scale=0.2)

    results = pipeline.run(image=image)
    for result in results:
        print(result)

def make_lens_x1_src_x1_profile_hyper_pipeline(pipeline_name):

    phase1 = ph.LensSourcePlanePhase(lens_galaxies=[gm.GalaxyModel(sie=mp.EllipticalIsothermal)],
                                     source_galaxies=[gm.GalaxyModel(sersic=lp.EllipticalSersic)],
                                     optimizer_class=nl.MultiNest, phase_name="{}/phase1".format(pipeline_name))

    phase1.optimizer.n_live_points = 60
    phase1.optimizer.sampling_efficiency = 0.8

    phase1h = ph.LensMassAndSourceProfileHyperOnlyPhase(optimizer_class=nl.MultiNest, 
                                                        phase_name="{}/phase1h".format(pipeline_name))

    class SourceHyperPhase(ph.LensSourcePlaneHyperPhase):
        def pass_priors(self, previous_results):
            phase1_results = previous_results[-1]
            phase1h_results = previous_results[-1].hyper
    #        self.lens_galaxies[0] = previous_results[-1].variable.lens_galaxies[0]
            self.source_galaxies = phase1_results.variable.source_galaxies
            self.source_galaxies[0].hyper_galaxy = phase1h_results.constant.source_galaxies[0].hyper_galaxy

    phase2 = SourceHyperPhase(lens_galaxies=[gm.GalaxyModel(sie=mp.EllipticalIsothermal)],
                              source_galaxies=[gm.GalaxyModel(sersic=lp.EllipticalSersic)],
                              optimizer_class=nl.MultiNest, phase_name="{}/phase2".format(pipeline_name))

    phase2.optimizer.n_live_points = 40
    phase2.optimizer.sampling_efficiency = 0.8

    return pl.PipelineImaging(pipeline_name, phase1, phase1h, phase2)


if __name__ == "__main__":
    test_lens_x1_src_x1_profile_hyper_pipeline()
