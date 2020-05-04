import autofit as af
import autolens as al
from test_autolens.integration.tests.interferometer import runner

test_type = "lens__source_inversion"
test_name = "lens_mass__source_adaptive_brightness"
data_type = "lens_sie__source_smooth"
data_resolution = "sma"


def make_pipeline(
    name,
    phase_folders,
    real_space_shape_2d=(100, 100),
    real_space_pixel_scales=(0.1, 0.1),
    non_linear_class=af.MultiNest,
):

    phase1 = al.PhaseInterferometer(
        phase_name="phase_1",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(redshift=0.5, mass=al.mp.EllipticalIsothermal),
            source=al.GalaxyModel(redshift=1.0, light=al.lp.EllipticalSersic),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase2 = al.PhaseInterferometer(
        phase_name="phase_2_weighted_regularization",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                mass=phase1.result.instance.galaxies.lens.mass,
                shear=phase1.result.instance.galaxies.lens.shear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=al.pix.VoronoiBrightnessImage,
                regularization=al.reg.AdaptiveBrightness,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase2.optimizer.const_efficiency_mode = True
    phase2.optimizer.n_live_points = 40
    phase2.optimizer.sampling_efficiency = 0.8

    phase3 = al.PhaseInterferometer(
        phase_name="phase_3",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                mass=phase1.model.galaxies.lens.mass,
                shear=phase1.model.galaxies.lens.shear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=phase2.result.instance.galaxies.source.pixelization,
                regularization=phase2.result.instance.galaxies.source.regularization,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase3.optimizer.const_efficiency_mode = True
    phase3.optimizer.n_live_points = 40
    phase3.optimizer.sampling_efficiency = 0.8

    phase4 = al.PhaseInterferometer(
        phase_name="phase_4_weighted_regularization",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                mass=phase3.result.instance.galaxies.lens.mass,
                shear=phase3.result.instance.galaxies.lens.shear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=phase2.model.galaxies.source.pixelization,
                regularization=phase2.model.galaxies.source.pixelization,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase4.optimizer.const_efficiency_mode = True
    phase4.optimizer.n_live_points = 40
    phase4.optimizer.sampling_efficiency = 0.8

    return al.PipelineDataset(name, phase1, phase2, phase3, phase4)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])
