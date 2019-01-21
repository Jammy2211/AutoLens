import os
import shutil

from autofit import conf
from autofit.optimize import non_linear as nl
from autolens.data import ccd
from autolens.model.galaxy import galaxy, galaxy_model as gm
from autolens.pipeline import phase as ph
from autolens.pipeline import pipeline as pl
from autolens.model.profiles import light_profiles as lp, mass_profiles as mp
from test.integration import tools

test_type = 'lens_and_source'
test_name = "lens_mass_x1_source_x1_positions"

path = '{}/../../'.format(os.path.dirname(os.path.realpath(__file__)))
output_path = path+'output/'+test_type
config_path = path+'config'
conf.instance = conf.Config(config_path=config_path, output_path=output_path)


def pipeline():

    lens_mass = mp.SphericalIsothermal(centre=(0.01, 0.01), einstein_radius=1.0)
    source_light = lp.EllipticalSersic(centre=(-0.01, -0.01), axis_ratio=0.6, phi=90.0, intensity=1.0,
                                       effective_radius=0.5, sersic_index=1.0)

    lens_galaxy = galaxy.Galaxy(sie=lens_mass)
    source_galaxy = galaxy.Galaxy(sersic=source_light)

    tools.reset_paths(test_name=test_name, output_path=output_path)
    tools.simulate_integration_image(test_name=test_name, pixel_scale=0.1, lens_galaxies=[lens_galaxy],
                                     source_galaxies=[source_galaxy], target_signal_to_noise=30.0)

    ccd_data = ccd.load_ccd_data_from_fits(image_path=path + '/data/' + test_name + '/image.fits',
                                        psf_path=path + '/data/' + test_name + '/psf.fits',
                                        noise_map_path=path + '/data/' + test_name + '/noise_map.fits',
                                        pixel_scale=0.1)

    pipeline = make_pipeline(test_name=test_name)
    pipeline.run(data=ccd_data)


def make_pipeline(test_name):

    phase1 = ph.LensSourcePlanePhase(lens_galaxies=[gm.GalaxyModel(sie=mp.EllipticalIsothermal)],
                                     source_galaxies=[gm.GalaxyModel(sersic=lp.EllipticalSersic)],
                                     optimizer_class=nl.MultiNest,
                                     positions=[[[1.0, 1.0], [1.0, -1.0], [-1.0, 1.0], [-1.0, -1.0]]],
                                     phase_name="{}/phase1".format(test_name))

    phase1.optimizer.n_live_points = 30
    phase1.optimizer.sampling_efficiency = 0.8

    return pl.PipelineImaging(test_name, phase1)


if __name__ == "__main__":
    pipeline()
