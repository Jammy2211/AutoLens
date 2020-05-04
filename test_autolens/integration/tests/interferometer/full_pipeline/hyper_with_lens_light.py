import autofit as af
import autolens as al
from test_autolens.integration.tests.interferometer import runner

test_type = "full_pipeline"
test_name = "hyper_with_lens_light"
data_type = "lens_sie__source_smooth"
data_resolution = "sma"


def make_pipeline(
    name,
    phase_folders,
    pipeline_pixelization=al.pix.VoronoiBrightnessImage,
    pipeline_regularization=al.reg.AdaptiveBrightness,
    non_linear_class=af.MultiNest,
):

    phase1 = al.PhaseInterferometer(
        phase_name="phase_1__lens_sersic",
        phase_folders=phase_folders,
        galaxies=dict(lens=al.GalaxyModel(redshift=0.5, light=al.lp.EllipticalSersic)),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 30
    phase1.optimizer.sampling_efficiency = 0.3

    phase1 = phase1.extend_with_multiple_hyper_phases(hyper_galaxy=True)

    class LensSubtractedPhase(al.PhaseInterferometer):
        def customize_priors(self, results):

            ## Lens Light Sersic -> Sersic ##

            self.galaxies.lens.light = results.from_phase(
                "phase_1__lens_sersic"
            ).instance.galaxies.lens.light

            ## Lens Mass, Move centre priors to centre of lens light ###

            self.galaxies.lens.mass.centre = (
                results.from_phase("phase_1__lens_sersic")
                .model_absolute(a=0.1)
                .galaxies.lens.light.centre
            )

            ## Set all hyper-galaxies if feature is turned on ##

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.lens.hyper_galaxy
            )

    phase2 = LensSubtractedPhase(
        phase_name="phase_2__lens_sie__source_sersic",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.EllipticalSersic,
                mass=al.mp.EllipticalIsothermal,
                shear=al.mp.ExternalShear,
            ),
            source=al.GalaxyModel(redshift=1.0, light=al.lp.EllipticalSersic),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase2.optimizer.const_efficiency_mode = False
    phase2.optimizer.n_live_points = 50
    phase2.optimizer.sampling_efficiency = 0.3

    phase2 = phase2.extend_with_multiple_hyper_phases(
        hyper_galaxy=True, include_background_sky=True, include_background_noise=True
    )

    class LensSourcePhase(al.PhaseInterferometer):
        def customize_priors(self, results):

            ## Lens Light, Sersic -> Sersic ###

            self.galaxies.lens.light = results.from_phase(
                "phase_1__lens_sersic"
            ).model.galaxies.lens.light

            ## Lens Mass, SIE -> SIE, Shear -> Shear ###

            self.galaxies.lens.mass = results.from_phase(
                "phase_2__lens_sie__source_sersic"
            ).model.galaxies.lens.mass

            self.galaxies.lens.shear = results.from_phase(
                "phase_2__lens_sie__source_sersic"
            ).model.galaxies.lens.shear

            ### Source Light, Sersic -> Sersic ###

            self.galaxies.source = results.from_phase(
                "phase_2__lens_sie__source_sersic"
            ).model.galaxies.source

            ## Set all hyper-galaxies if feature is turned on ##

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.lens.hyper_galaxy
            )

    phase3 = LensSourcePhase(
        phase_name="phase_3__lens_sersic_sie__source_sersic",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.EllipticalSersic,
                mass=al.mp.EllipticalIsothermal,
                shear=al.mp.ExternalShear,
            ),
            source=al.GalaxyModel(redshift=1.0, light=al.lp.EllipticalSersic),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase3.optimizer.const_efficiency_mode = True
    phase3.optimizer.n_live_points = 75
    phase3.optimizer.sampling_efficiency = 0.3

    phase3 = phase3.extend_with_multiple_hyper_phases(hyper_galaxy=True)

    class InversionPhase(al.PhaseInterferometer):
        def customize_priors(self, results):

            ## Lens Light & Mass, Sersic -> Sersic, SIE -> SIE, Shear -> Shear ###

            self.galaxies.lens.light = results.from_phase(
                "phase_3__lens_sersic_sie__source_sersic"
            ).instance.galaxies.lens.light

            self.galaxies.lens.mass = results.from_phase(
                "phase_3__lens_sersic_sie__source_sersic"
            ).instance.galaxies.lens.mass

            self.galaxies.lens.shear = results.from_phase(
                "phase_3__lens_sersic_sie__source_sersic"
            ).instance.galaxies.lens.shear

            ## Set all hyper-galaxies if feature is turned on ##

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.lens.hyper_galaxy
            )

    phase4 = InversionPhase(
        phase_name="phase_4__initialize_magnification_inversion",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.EllipticalSersic,
                mass=al.mp.EllipticalIsothermal,
                shear=al.mp.ExternalShear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=al.pix.VoronoiMagnification,
                regularization=al.reg.Constant,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase4.optimizer.const_efficiency_mode = True
    phase4.optimizer.n_live_points = 20
    phase4.optimizer.sampling_efficiency = 0.8

    phase4 = phase4.extend_with_multiple_hyper_phases(
        hyper_galaxy=True, inversion=False
    )

    class InversionPhase(al.PhaseInterferometer):
        def customize_priors(self, results):

            ## Lens Light & Mass, Sersic -> Sersic, SIE -> SIE, Shear -> Shear ###

            self.galaxies.lens = results.from_phase(
                "phase_3__lens_sersic_sie__source_sersic"
            ).model.galaxies.lens

            ### Source Inversion, Inv -> Inv ###

            self.galaxies.source.pixelization = results.from_phase(
                "phase_4__initialize_magnification_inversion"
            ).instance.galaxies.source.pixelization

            self.galaxies.source.regularization = results.from_phase(
                "phase_4__initialize_magnification_inversion"
            ).instance.galaxies.source.regularization

            ## Set all hyper-galaxies if feature is turned on ##

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.lens.hyper_galaxy
            )

    phase5 = InversionPhase(
        phase_name="phase_5__lens_sersic_sie__source_magnification_inversion",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.EllipticalSersic,
                mass=al.mp.EllipticalIsothermal,
                shear=al.mp.ExternalShear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=pipeline_pixelization,
                regularization=pipeline_regularization,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase5.optimizer.const_efficiency_mode = True
    phase5.optimizer.n_live_points = 75
    phase5.optimizer.sampling_efficiency = 0.2

    phase5 = phase5.extend_with_multiple_hyper_phases(
        hyper_galaxy=True,
        include_background_sky=True,
        include_background_noise=True,
        inversion=False,
    )

    class InversionPhase(al.PhaseInterferometer):
        def customize_priors(self, results):

            ## Lens Light & Mass, Sersic -> Sersic, SIE -> SIE, Shear -> Shear ###

            self.galaxies.lens.light = results.from_phase(
                "phase_5__lens_sersic_sie__source_magnification_inversion"
            ).instance.galaxies.lens.light

            self.galaxies.lens.mass = results.from_phase(
                "phase_5__lens_sersic_sie__source_magnification_inversion"
            ).instance.galaxies.lens.mass

            self.galaxies.lens.shear = results.from_phase(
                "phase_5__lens_sersic_sie__source_magnification_inversion"
            ).instance.galaxies.lens.shear

            ## Set all hyper-galaxies if feature is turned on ##

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.lens.hyper_galaxy
            )

    phase6 = InversionPhase(
        phase_name="phase_6_initialize_inversion",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.EllipticalSersic,
                mass=al.mp.EllipticalIsothermal,
                shear=al.mp.ExternalShear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=pipeline_pixelization,
                regularization=pipeline_regularization,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase6.optimizer.const_efficiency_mode = True
    phase6.optimizer.n_live_points = 20
    phase6.optimizer.sampling_efficiency = 0.8

    phase6 = phase6.extend_with_multiple_hyper_phases(
        hyper_galaxy=True,
        include_background_sky=True,
        include_background_noise=True,
        inversion=True,
    )

    class InversionPhase(al.PhaseInterferometer):
        def customize_priors(self, results):

            ## Lens Light & Mass, Sersic -> Sersic, SIE -> SIE, Shear -> Shear ###

            self.galaxies.lens = results.from_phase(
                "phase_5__lens_sersic_sie__source_magnification_inversion"
            ).model.galaxies.lens

            ### Source Inversion, Inv -> Inv ###

            self.galaxies.source.pixelization = results.from_phase(
                "phase_6_initialize_inversion"
            ).hyper_combined.instance.galaxies.source.pixelization

            self.galaxies.source.regularization = results.from_phase(
                "phase_6_initialize_inversion"
            ).hyper_combined.instance.galaxies.source.regularization

            ## Set all hyper-galaxies if feature is turned on ##

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.lens.hyper_galaxy
            )

            self.galaxies.source.hyper_galaxy = (
                results.last.hyper_combined.instance.galaxies.source.hyper_galaxy
            )

    phase7 = InversionPhase(
        phase_name="phase_7__lens_sersic_sie__source_inversion",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.EllipticalSersic,
                mass=al.mp.EllipticalIsothermal,
                shear=al.mp.ExternalShear,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=pipeline_pixelization,
                regularization=pipeline_regularization,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        non_linear_class=non_linear_class,
    )

    phase7.optimizer.const_efficiency_mode = True
    phase7.optimizer.n_live_points = 75
    phase7.optimizer.sampling_efficiency = 0.2

    phase7 = phase7.extend_with_multiple_hyper_phases(
        hyper_galaxy=True,
        include_background_sky=True,
        include_background_noise=True,
        inversion=True,
    )

    return al.PipelineDataset(
        name, phase1, phase2, phase3, phase4, phase5, phase6, phase7
    )


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])
