import numpy as np

from autofit.mapper import model_mapper as mm
from autofit.optimize import non_linear
from autolens.model.galaxy import galaxy as g


class MockAnalysis(object):

    def __init__(self, number_galaxies, value):
        self.number_galaxies = number_galaxies
        self.value = value

    # noinspection PyUnusedLocal
    def galaxy_images_for_model(self, model):
        return self.number_galaxies * [np.array([self.value])]

    def fit(self, instance):
        return 1


class MockResults(object):

    def __init__(self, model_image=None, galaxy_images=(), constant=None, analysis=None,
                 optimizer=None):
        self.model_image = model_image
        self.unmasked_model_image = model_image
        self.galaxy_images = galaxy_images
        self.constant = constant or mm.ModelInstance()
        self.variable = mm.ModelMapper()
        self.analysis = analysis
        self.optimizer = optimizer

    @property
    def path_galaxy_tuples(self) -> [(str, g.Galaxy)]:
        """
        Tuples associating the names of galaxies with instances from the best fit
        """
        return [(('g0',), g.Galaxy(redshift=0.5)), (('g1',), g.Galaxy(redshift=1.0))]

    @property
    def path_galaxy_tuples_with_index(self) -> [(str, g.Galaxy)]:
        """
        Tuples associating the names of galaxies with instances from the best fit
        """
        return [(0, ('g0',), g.Galaxy(redshift=0.5)),
                (1, ('g1',), g.Galaxy(redshift=1.0))]

    @property
    def image_2d_dict(self) -> {str: g.Galaxy}:
        """
        A dictionary associating galaxy names with model images of those galaxies
        """
        return {galaxy_path: self.galaxy_images[i]
                for i, galaxy_path, galaxy
                in self.path_galaxy_tuples_with_index}


class MockResult:
    def __init__(self, constant, figure_of_merit, variable=None):
        self.constant = constant
        self.figure_of_merit = figure_of_merit
        self.variable = variable
        self.previous_variable = variable
        self.gaussian_tuples = None


class MockNLO(non_linear.NonLinearOptimizer):

    def fit(self, analysis):
        class Fitness(object):

            def __init__(self, instance_from_physical_vector):
                self.result = None
                self.instance_from_physical_vector = instance_from_physical_vector

            def __call__(self, vector):
                instance = self.instance_from_physical_vector(vector)

                likelihood = analysis.fit(instance)
                self.result = MockResult(instance, likelihood)

                # Return Chi squared
                return -2 * likelihood

        fitness_function = Fitness(self.variable.instance_from_physical_vector)
        fitness_function(self.variable.prior_count * [0.8])

        return fitness_function.result