from autogalaxy.pipeline.phase.abstract import analysis as ag_analysis
from autolens.fit import fit_positions
from autolens.pipeline import visualizer as vis
from autolens.lens import ray_tracing


class Analysis(ag_analysis.Analysis):
    def __init__(
        self, positions, noise_map, solver, imaging, settings, cosmology, results
    ):

        super().__init__(settings=settings, cosmology=cosmology)

        self.positions = positions
        self.noise_map = noise_map
        self.solver = solver
        self.imaging = imaging
        self.results = results

    def tracer_for_instance(self, instance):

        return ray_tracing.Tracer.from_galaxies(
            galaxies=instance.galaxies, cosmology=self.cosmology
        )

    def log_likelihood_function(self, instance):
        """
        Determine the fit of a lens galaxy and source galaxy to the masked_imaging in this lens.

        Parameters
        ----------
        instance
            A model instance with attributes

        Returns
        -------
        fit : Fit
            A fractional value indicating how well this model fit and the model masked_imaging itself
        """

        tracer = self.tracer_for_instance(instance=instance)
        fit = self.positions_fit_for_tracer(tracer=tracer)
        return fit.log_likelihood

    def positions_fit_for_tracer(self, tracer):

        return fit_positions.FitPositionsImagePlane(
            positions=self.positions,
            noise_map=self.noise_map,
            positions_solver=self.solver,
            tracer=tracer,
        )

    def visualize(self, paths, instance, during_analysis):

        tracer = self.tracer_for_instance(instance=instance)

        visualizer = vis.Visualizer(visualize_path=paths.image_path)


class Attributes:
    def __init__(self, cosmology):
        self.cosmology = cosmology
