from autoarray.structures.arrays import values
from autoarray.structures.grids.two_d import grid_2d_irregular
from autoarray.fit.fit import FitData

from functools import partial

from autolens import exc

class AbstractFitPositionsSourcePlane:
    def __init__(self, positions, noise_map, tracer):
        """
        Given a positions dataset, which is a list of positions with names that associated them to model source
        galaxies, use a `Tracer` to determine the traced coordinate positions in the source-plane.

        Different children of this abstract class are available which use the traced coordinates to define a chi-squared
        value in different ways.

        Parameters
        -----------
        positions : grid_2d_irregular.Grid2DIrregular
            The (y,x) arc-second coordinates of named positions which the log_likelihood is computed using. Positions
            are paired to galaxies in the `Tracer` using their names.
        tracer : ray_tracing.Tracer
            The object that defines the ray-tracing of the strong lens system of galaxies.
        noise_value : float
            The noise-value assumed when computing the log likelihood.
        """
        self.positions = positions
        self.noise_map = noise_map
        self.source_plane_positions = tracer.traced_grids_of_planes_from_grid(
            grid=positions
        )[-1]

    @property
    def furthest_separations_of_source_plane_positions(self) -> values.ValuesIrregular:
        """
        Returns the furthest distance of every source-plane (y,x) coordinate to the other source-plane (y,x)
        coordinates.

        For example, for the following source-plane positions:

        source_plane_positions = [[(0.0, 0.0), (0.0, 1.0), (0.0, 3.0)]

        The returned furthest distances are:

        source_plane_positions = [3.0, 2.0, 3.0]

        Returns
        -------
        values.ValuesIrregular
            The further distances of every set of grouped source-plane coordinates the other source-plane coordinates
            that it is grouped with.
        """
        return self.source_plane_positions.furthest_distances_from_other_coordinates

    @property
    def max_separation_of_source_plane_positions(self) -> float:
        return max(self.furthest_separations_of_source_plane_positions)

    def max_separation_within_threshold(self, threshold) -> bool:
        return self.max_separation_of_source_plane_positions <= threshold


class FitPositionsSourceMaxSeparation(AbstractFitPositionsSourcePlane):
    def __init__(self, positions, noise_map, tracer):
        """A lens position fitter, which takes a set of positions (e.g. from a plane in the tracer) and computes \
        their maximum separation, such that points which tracer closer to one another have a higher log_likelihood.

        Parameters
        -----------
        positions : grid_2d_irregular.Grid2DIrregular
            The (y,x) arc-second coordinates of positions which the maximum distance and log_likelihood is computed using.
        noise_value : float
            The noise-value assumed when computing the log likelihood.
        """
        super().__init__(positions=positions, noise_map=noise_map, tracer=tracer)

    # @property
    # def chi_squared_map(self):
    #     return np.square(np.divide(self.max_separation_of_source_plane_positions, self.noise_map))
    #
    # @property
    # def figure_of_merit(self):
    #     return -0.5 * sum(self.chi_squared_map)


class FitPositionsImage(FitData):
    def __init__(self, name, positions, noise_map, tracer, positions_solver):
        """
        A lens position fitter, which takes a set of positions (e.g. from a plane in the tracer) and computes \
        their maximum separation, such that points which tracer closer to one another have a higher log_likelihood.

        Parameters
        -----------
        positions : grid_2d_irregular.Grid2DIrregular
            The (y,x) arc-second coordinates of positions which the maximum distance and log_likelihood is computed using.
        noise_value : float
            The noise-value assumed when computing the log likelihood.
        """

        self.name = name
        self.positions_solver = positions_solver
        self.point_source_profile = tracer.extract_profile(profile_name=name)

        if self.point_source_profile is None:
            raise exc.PointSourceExtractionException(
                f"For the point-source named {name} there was no matching point source profile "
                f"in the tracer (make sure your tracer's point source name is the same the dataset name.")

        self.source_plane_coordinate = self.point_source_profile.centre

        if len(tracer.planes) > 2:
            upper_plane_index = tracer.extract_plane_index_of_profile(profile_name=name)
        else:
            upper_plane_index = None

        model_positions = positions_solver.solve(
            lensing_obj=tracer,
            source_plane_coordinate=self.source_plane_coordinate,
            upper_plane_index=upper_plane_index,
        )

        model_positions = model_positions.grid_of_closest_from_grid_pair(
            grid_pair=positions
        )

        super().__init__(
            data=positions,
            noise_map=noise_map,
            model_data=model_positions,
            mask=None,
            inversion=None,
        )

    @property
    def positions(self):
        return self.data

    @property
    def model_positions(self):
        return self.model_data

    @property
    def residual_map(self) -> values.ValuesIrregular:

        residual_positions = self.positions - self.model_positions

        return residual_positions.distances_from_coordinate(coordinate=(0.0, 0.0))


class FitFluxes(FitData):
    def __init__(self, name, fluxes, noise_map, positions, tracer):

        self.name = name
        self.positions = positions

        self.point_source_profile = tracer.extract_profile(profile_name=name)

        if self.point_source_profile is None:
            raise exc.PointSourceExtractionException(
                f"For the point-source named {name} there was no matching point source profile "
                f"in the tracer (make sure your tracer's point source name is the same the dataset name.")

        elif not hasattr(self.point_source_profile, "flux"):
            raise exc.PointSourceExtractionException(
                f"For the point-source named {name} the extracted point source was the "
                f"class {self.point_source_profile.__class__.__name__} and therefore does "
                f"not contain a flux component.")

        if len(tracer.planes) > 2:
            upper_plane_index = tracer.extract_plane_index_of_profile(profile_name=name)
            deflections_func = partial(
                tracer.deflections_between_planes_from_grid,
                plane_i=0,
                plane_j=upper_plane_index,
            )
        else:
            deflections_func = tracer.deflections_from_grid

        self.magnifications = abs(
            tracer.magnification_via_hessian_from_grid(
                grid=positions, deflections_func=deflections_func
            )
        )

        model_fluxes = values.ValuesIrregular(
            values=[
                magnification * self.point_source_profile.flux
                for magnification in self.magnifications
            ]
        )

        super().__init__(
            data=fluxes,
            noise_map=noise_map,
            model_data=model_fluxes,
            mask=None,
            inversion=None,
        )

    @property
    def fluxes(self):
        return self.data

    @property
    def model_fluxes(self):
        return self.model_data
