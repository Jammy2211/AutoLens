import autofit as af
import autolens as al
from test_autolens.integration.tests.imaging import runner

test_type = "reult_passing"
test_name = "mass_customize_model_via_phase_works"
dataset_name = "lens_sie__source_smooth"
instrument = "vro"


def make_pipeline(name, path_prefix, search=af.DynestyStatic()):

    # For this mass model, we fix the centre, making N = 10.

    mass = af.PriorModel(al.mp.EllipticalIsothermal)
    mass.centre.centre_0 = 0.0
    mass.centre.centre_1 = 0.0

    phase1 = al.PhaseImaging(
        name="phase[1]",
        path_prefix=path_prefix,
        galaxies=dict(
            lens=al.GalaxyModel(redshift=0.5, mass=mass),
            source=al.GalaxyModel(redshift=1.0, light=al.lp.EllipticalSersic),
        ),
        sub_size=1,
        search=search,
    )

    phase1.search.const_efficiency_mode = True
    phase1.search.n_live_points = 60
    phase1.search.facc = 0.8

    # We now want to create a lens galaxy whose mass model centres are free parameters, increaisng N to 12.

    # This works, giving N = 12

    mass = af.PriorModel(al.mp.EllipticalIsothermal)

    mass.centre.centre_0 = af.GaussianPrior(mean=0.0, sigma=0.05)
    mass.centre.centre_1 = af.GaussianPrior(mean=0.0, sigma=0.05)

    phase2 = al.PhaseImaging(
        name="phase[2]",
        path_prefix=path_prefix,
        galaxies=dict(
            lens=al.GalaxyModel(redshift=0.5, mass=mass),
            source=phase1.result.model.galaxies.source,
        ),
        sub_size=1,
        search=search,
    )

    return al.PipelineDataset(name, path_prefix, phase1, phase2)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])
