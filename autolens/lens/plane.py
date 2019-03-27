import numpy as np
from astropy import constants
from astropy import cosmology as cosmo
from functools import wraps

from autolens import exc
from autolens.data.array import grids
from autolens.data.array import scaled_array
from autolens.lens.util import lens_util
from autolens.model.galaxy.util import galaxy_util


def check_plane_for_redshift(func):
    """If a plane's galaxies do not have redshifts, its cosmological quantities cannot be computed. This wrapper \
    makes these functions return *None* if the galaxies do not have redshifts

    Parameters
    ----------
    func : (self) -> Object
        A property function that requires galaxies to have redshifts.
    """

    @wraps(func)
    def wrapper(self):
        """

        Parameters
        ----------
        self

        Returns
        -------
            A value or coordinate in the same coordinate system as those passed in.
        """

        if self.redshift is not None:
            return func(self)
        else:
            return None

    return wrapper


class AbstractPlane(object):

    def __init__(self, redshift, galaxies, cosmology=cosmo.Planck15):
        """An abstract plane which represents a set of galaxies that are close to one another in redshift-space.

        From an abstract plane, cosmological quantities like angular diameter distances can be computed. If the  \
        redshift of the plane is input as *None*, quantities that depend on a redshift are returned as *None*.

        Parameters
        -----------
        redshift : float or None
            The redshift of the plane.
        galaxies : [Galaxy]
            The list of galaxies in this plane.
        cosmology : astropy.cosmology
            The cosmology associated with the plane, used to convert arc-second coordinates to physical values.
        """

        self.redshift = redshift
        self.galaxies = galaxies
        self.cosmology = cosmology

    @property
    def galaxy_redshifts(self):
        return [galaxy.redshift for galaxy in self.galaxies]

    @property
    def constant_kpc(self):
        # noinspection PyUnresolvedReferences
        return constants.c.to('kpc / s').value ** 2.0 / (4 * math.pi * constants.G.to('kpc3 / M_sun s2').value)

    @property
    @check_plane_for_redshift
    def arcsec_per_kpc_proper(self):
        return self.cosmology.arcsec_per_kpc_proper(z=self.redshift).value

    @property
    @check_plane_for_redshift
    def kpc_per_arcsec_proper(self):
        return 1.0 / self.arcsec_per_kpc_proper

    @property
    @check_plane_for_redshift
    def angular_diameter_distance_to_earth(self):
        return self.cosmology.angular_diameter_distance(self.redshift).to('kpc').value

    @property
    @check_plane_for_redshift
    def cosmic_average_mass_density_arcsec(self):
        return self.cosmology.critical_density(z=self.redshift).to('solMass / kpc^3').value / \
               self.arcsec_per_kpc_proper**3.0

    @property
    def has_light_profile(self):
        return any(list(map(lambda galaxy: galaxy.has_light_profile, self.galaxies)))

    @property
    def has_mass_profile(self):
        return any(list(map(lambda galaxy: galaxy.has_mass_profile, self.galaxies)))

    @property
    def has_pixelization(self):
        return any(list(map(lambda galaxy: galaxy.has_pixelization, self.galaxies)))

    @property
    def has_regularization(self):
        return any(list(map(lambda galaxy: galaxy.has_regularization, self.galaxies)))

    @property
    def regularization(self):

        galaxies_with_regularization = list(filter(lambda galaxy: galaxy.has_regularization, self.galaxies))

        if len(galaxies_with_regularization) == 0:
            return None
        if len(galaxies_with_regularization) == 1:
            return galaxies_with_regularization[0].regularization
        elif len(galaxies_with_regularization) > 1:
            raise exc.PixelizationException('The number of galaxies with regularizations in one plane is above 1')

    def luminosities_of_galaxies_within_circles(self, radius, conversion_factor=1.0):
        """Compute the total luminosity of all galaxies in this plane within a circle of specified radius.

        The value returned by this integral is dimensionless, and a conversion factor can be specified to convert it \
        to a physical value (e.g. the photometric zeropoint).

        See *galaxy.light_within_circle* and *light_profiles.light_within_circle* for details
        of how this is performed.

        Parameters
        ----------
        radius : float
            The radius of the circle to compute the dimensionless luminosity within.
        conversion_factor : float
            Factor the dimensionless luminosity is multiplied by to convert it to a physical luminosity \ 
            (e.g. a photometric zeropoint).                
        """
        return list(map(lambda galaxy: galaxy.luminosity_within_circle(radius, conversion_factor),
                        self.galaxies))

    def luminosities_of_galaxies_within_ellipses(self, major_axis, conversion_factor=1.0):
        """
        Compute the total luminosity of all galaxies in this plane within a ellipse of specified major-axis.

        The value returned by this integral is dimensionless, and a conversion factor can be specified to convert it \
        to a physical value (e.g. the photometric zeropoint).

        See *galaxy.light_within_ellipse* and *light_profiles.light_within_ellipse* for details
        of how this is performed.

        Parameters
        ----------
        major_axis : float
            The major-axis of the ellipse to compute the dimensionless luminosity within.
        conversion_factor : float
            Factor the dimensionless luminosity is multiplied by to convert it to a physical luminosity \ 
            (e.g. a photometric zeropoint).            
        """
        return list(map(lambda galaxy: galaxy.luminosity_within_ellipse(major_axis, conversion_factor),
                        self.galaxies))

    def masses_of_galaxies_within_circles_in_angular_units(self, radius):
        """
        Compute the total angular mass of all galaxies in this plane within a circle of specified radius.

        The value returned by this integral is in angular units, however a conversion factor can be specified to \
        convert it to a physical value (e.g. the critical surface mass density).

        See *galaxy.angular_mass_within_circle* and *mass_profiles.angular_mass_within_circle* for details
        of how this is performed.

        Parameters
        ----------
        radius : float
            The radius of the circle to compute the dimensionless mass within.
        conversion_factor : float
            Factor the dimensionless mass is multiplied by to convert it to a physical mass (e.g. the critical surface \
            mass density).            
        """
        return list(map(lambda galaxy: galaxy.mass_within_circle_in_angular_units(radius),
                        self.galaxies))

    def masses_of_galaxies_within_ellipses_in_angular_units(self, major_axis):
        """
        Compute the total angular mass of all galaxies in this plane within a ellipse of specified major-axis.

        The value returned by this integral is in angular units, however a conversion factor can be specified to \
        convert it to a physical value (e.g. the critical surface mass density).

        See *galaxy.angular_mass_within_ellipse* and *mass_profiles.angular_mass_within_ellipse* for details
        of how this is performed.

        Parameters
        ----------
        major_axis : float
            The major-axis of the ellipse to compute the dimensionless mass within.
        conversion_factor : float
            Factor the dimensionless mass is multiplied by to convert it to a physical mass (e.g. the critical surface \
            mass density).
        """
        return list(map(lambda galaxy: galaxy.mass_within_ellipse_in_angular_units(major_axis),
                        self.galaxies))

    def masses_of_galaxies_within_circles_in_mass_units(self, radius, critical_surface_mass_density):
        """
        Compute the total angular mass of all galaxies in this plane within a circle of specified radius.

        The value returned by this integral is in angular units, however a conversion factor can be specified to \
        convert it to a physical value (e.g. the critical surface mass density).

        See *galaxy.angular_mass_within_circle* and *mass_profiles.angular_mass_within_circle* for details
        of how this is performed.

        Parameters
        ----------
        radius : float
            The radius of the circle to compute the dimensionless mass within.
        critical_surface_mass_density : float
            Factor the dimensionless mass is multiplied by to convert it to a physical mass (e.g. the critical surface \
            mass density).            
        """
        return list(map(lambda galaxy: galaxy.mass_within_circle_in_mass_units(radius, critical_surface_mass_density),
                        self.galaxies))

    def masses_of_galaxies_within_ellipses_in_mass_units(self, major_axis, critical_surface_mass_density):
        """
        Compute the total angular mass of all galaxies in this plane within a ellipse of specified major-axis.

        The value returned by this integral is in angular units, however a conversion factor can be specified to \
        convert it to a physical value (e.g. the critical surface mass density).

        See *galaxy.angular_mass_within_ellipse* and *mass_profiles.angular_mass_within_ellipse* for details
        of how this is performed.

        Parameters
        ----------
        major_axis : float
            The major-axis of the ellipse to compute the dimensionless mass within.
        critical_surface_mass_density : float
            Factor the dimensionless mass is multiplied by to convert it to a physical mass (e.g. the critical surface \
            mass density).            
        """
        return list(map(lambda galaxy: galaxy.mass_within_ellipse_in_mass_units(major_axis, critical_surface_mass_density),
                        self.galaxies))

    @property
    def einstein_radius_arcsec(self):
        if self.has_mass_profile:
            return sum(filter(None, list(map(lambda galaxy: galaxy.einstein_radius, self.galaxies))))

    @property
    @check_plane_for_redshift
    def einstein_radius_kpc(self):
        if self.has_mass_profile:
            return self.kpc_per_arcsec_proper * self.einstein_radius_arcsec

    def einstein_mass_in_mass_units(self, critical_surface_mass_density_arcsec):
        if self.has_mass_profile:
            return sum(filter(None, list(map(lambda galaxy:
                                             galaxy.mass_within_circle_in_mass_units(
                                                 radius=galaxy.einstein_radius,
                                                 critical_surface_mass_density=critical_surface_mass_density_arcsec),
                                             self.galaxies))))


class AbstractGriddedPlane(AbstractPlane):

    def __init__(self, redshift, galaxies, grid_stack, border, compute_deflections, cosmology=cosmo.Planck15):
        """An abstract plane which represents a set of galaxies that are close to one another in redshift-space and \
        have an associated grid on which lensing calcuations are performed.

        From an abstract plane grid, the surface-density, potential and deflection angles of the galaxies can be \
        computed.

        Parameters
        -----------
        redshift : float or None
            The redshift of the plane.
        galaxies : [Galaxy]
            The list of lens galaxies in this plane.
        grid_stack : masks.GridStack
            The stack of grid_stacks of (y,x) arc-second coordinates of this plane.
        border : masks.RegularGridBorder
            The borders of the regular-grid, which is used to relocate demagnified traced regular-pixel to the \
            source-plane borders.
        compute_deflections : bool
            If true, the deflection-angles of this plane's coordinates are calculated use its galaxy's mass-profiles.
        cosmology : astropy.cosmology
            The cosmology associated with the plane, used to convert arc-second coordinates to physical values.
        """

        super(AbstractGriddedPlane, self).__init__(redshift=redshift, galaxies=galaxies, cosmology=cosmology)

        self.grid_stack = grid_stack
        self.border = border

        if compute_deflections:

            def calculate_deflections(grid):

                if galaxies:
                    return sum(map(lambda galaxy: galaxy.deflections_from_grid(grid), galaxies))
                else:
                    return np.full((grid.shape[0], 2), 0.0)

            self.deflection_stack = self.grid_stack.apply_function(calculate_deflections)

        else:

            self.deflection_stack = None

    def trace_grid_stack_to_next_plane(self):
        """Trace this plane's grid_stacks to the next plane, using its deflection angles."""

        def minus(grid, deflections):
            return grid - deflections

        return self.grid_stack.map_function(minus, self.deflection_stack)

    @property
    def image_plane_image(self):
        return self.grid_stack.scaled_array_2d_from_array_1d(self.image_plane_image_1d)

    @property
    def image_plane_image_for_simulation(self):
        if not self.has_padded_grid_stack:
            raise exc.RayTracingException(
                'To retrieve an image plane image for the simulation, the grid_stacks in the tracer_normal'
                'must be padded grid_stacks')
        return self.grid_stack.regular.map_to_2d_keep_padded(padded_array_1d=self.image_plane_image_1d)

    @property
    def image_plane_image_1d(self):
        return galaxy_util.intensities_of_galaxies_from_grid(grid=self.grid_stack.sub, galaxies=self.galaxies)

    @property
    def image_plane_image_1d_of_galaxies(self):
        return list(map(self.image_plane_image_1d_of_galaxy, self.galaxies))

    def image_plane_image_1d_of_galaxy(self, galaxy):
        return galaxy_util.intensities_of_galaxies_from_grid(grid=self.grid_stack.sub, galaxies=[galaxy])

    @property
    def image_plane_blurring_image_1d(self):
        return galaxy_util.intensities_of_galaxies_from_grid(grid=self.grid_stack.blurring, galaxies=self.galaxies)

    @property
    def convergence(self):
        convergence_1d = galaxy_util.convergence_of_galaxies_from_grid(
            grid=self.grid_stack.sub.unlensed_grid, galaxies=self.galaxies)
        return self.grid_stack.scaled_array_2d_from_array_1d(array_1d=convergence_1d)

    @property
    def potential(self):
        potential_1d = galaxy_util.potential_of_galaxies_from_grid(grid=self.grid_stack.sub.unlensed_grid,
                                                                   galaxies=self.galaxies)
        return self.grid_stack.scaled_array_2d_from_array_1d(array_1d=potential_1d)

    @property
    def deflections_y(self):
        return self.grid_stack.scaled_array_2d_from_array_1d(self.deflections_1d[:, 0])

    @property
    def deflections_x(self):
        return self.grid_stack.scaled_array_2d_from_array_1d(self.deflections_1d[:, 1])

    @property
    def deflections_1d(self):
        return galaxy_util.deflections_of_galaxies_from_grid(grid=self.grid_stack.sub.unlensed_grid,
                                                             galaxies=self.galaxies)

    @property
    def has_padded_grid_stack(self):
        return isinstance(self.grid_stack.regular, grids.PaddedRegularGrid)

    @property
    def plane_image(self):
        return lens_util.plane_image_of_galaxies_from_grid(shape=self.grid_stack.regular.mask.shape,
                                                           grid=self.grid_stack.regular,
                                                           galaxies=self.galaxies)

    @property
    def mapper(self):

        galaxies_with_pixelization = list(filter(lambda galaxy: galaxy.has_pixelization, self.galaxies))

        if len(galaxies_with_pixelization) == 0:
            return None
        if len(galaxies_with_pixelization) == 1:
            pixelization = galaxies_with_pixelization[0].pixelization
            return pixelization.mapper_from_grid_stack_and_border(grid_stack=self.grid_stack, border=self.border)
        elif len(galaxies_with_pixelization) > 1:
            raise exc.PixelizationException('The number of galaxies with pixelizations in one plane is above 1')

    @property
    def yticks(self):
        """Compute the yticks labels of this grid_stack, used for plotting the y-axis ticks when visualizing an image \
        """
        return np.linspace(np.amin(self.grid_stack.regular[:, 0]), np.amax(self.grid_stack.regular[:, 0]), 4)

    @property
    def xticks(self):
        """Compute the xticks labels of this grid_stack, used for plotting the x-axis ticks when visualizing an \
        image"""
        return np.linspace(np.amin(self.grid_stack.regular[:, 1]), np.amax(self.grid_stack.regular[:, 1]), 4)


class Plane(AbstractGriddedPlane):

    def __init__(self, galaxies, grid_stack, border=None, compute_deflections=True, cosmology=cosmo.Planck15):
        """A plane of galaxies where all galaxies are at the same redshift.

        Parameters
        -----------
        galaxies : [Galaxy]
            The list of lens galaxies in this plane.
        grid_stack : masks.GridStack
            The stack of grid_stacks of (y,x) arc-second coordinates of this plane.
        border : masks.RegularGridBorder
            The borders of the regular-grid, which is used to relocate demagnified traced regular-pixel to the \
            source-plane borders.
        compute_deflections : bool
            If true, the deflection-angles of this plane's coordinates are calculated use its galaxy's mass-profiles.
        cosmology : astropy.cosmology
            The cosmology associated with the plane, used to convert arc-second coordinates to physical values.
        """

        if not galaxies:
            raise exc.RayTracingException('An empty list of galaxies was supplied to Plane')

        galaxy_redshifts = [galaxy.redshift for galaxy in galaxies]

        if any([redshift is not None for redshift in galaxy_redshifts]):
            if not all([galaxies[0].redshift == galaxy.redshift for galaxy in galaxies]):
                raise exc.RayTracingException('The galaxies supplied to A Plane have different redshifts or one galaxy '
                                              'does not have a redshift.')

        super(Plane, self).__init__(redshift=galaxies[0].redshift, galaxies=galaxies, grid_stack=grid_stack,
                                    border=border, compute_deflections=compute_deflections, cosmology=cosmology)

    def unmasked_blurred_image_of_galaxies_from_psf(self, padded_grid_stack, psf):
        """This is a utility function for the function above, which performs the iteration over each plane's galaxies \
        and computes each galaxy's unmasked blurred image.

        Parameters
        ----------
        padded_grid_stack
        psf : ccd.PSF
            The PSF of the image used for convolution.
        """
        return [padded_grid_stack.unmasked_blurred_image_from_psf_and_unmasked_image(
            psf, image) if not galaxy.has_pixelization else None for galaxy, image in
                zip(self.galaxies, self.image_plane_image_1d_of_galaxies)]

    def unmasked_blurred_image_of_galaxy_with_grid_stack_psf(self, galaxy, padded_grid_stack, psf):
        return padded_grid_stack.unmasked_blurred_image_from_psf_and_unmasked_image(
            psf,
            self.image_plane_image_1d_of_galaxy(
                galaxy))


class PlaneSlice(AbstractGriddedPlane):

    def __init__(self, galaxies, grid_stack, redshift, border=None, compute_deflections=True, cosmology=cosmo.Planck15):
        """A plane of galaxies where the galaxies may be at different redshifts to the plane itself.

        Parameters
        -----------
        galaxies : [Galaxy]
            The list of lens galaxies in this plane.
        grid_stack : masks.GridStack
            The stack of grid_stacks of (y,x) arc-second coordinates of this plane.
        border : masks.RegularGridBorder
            The borders of the regular-grid, which is used to relocate demagnified traced regular-pixel to the \
            source-plane borders.
        compute_deflections : bool
            If true, the deflection-angles of this plane's coordinates are calculated use its galaxy's mass-profiles.
        cosmology : astropy.cosmology
            The cosmology associated with the plane, used to convert arc-second coordinates to physical values.
        """

        super(PlaneSlice, self).__init__(redshift=redshift, galaxies=galaxies, grid_stack=grid_stack, border=border,
                                         compute_deflections=compute_deflections, cosmology=cosmology)


class PlanePositions(object):

    def __init__(self, redshift, galaxies, positions, compute_deflections=True, cosmology=None):
        """A plane represents a set of galaxies at a given redshift in a ray-tracer_normal and the positions of image-plane \
        coordinates which mappers close to one another in the source-plane.

        Parameters
        -----------
        galaxies : [Galaxy]
            The list of lens galaxies in this plane.
        positions : [[[]]]
            The (y,x) arc-second coordinates of image-plane pixels which (are expected to) mappers to the same
            location(s) in the final source-plane.
        compute_deflections : bool
            If true, the deflection-angles of this plane's coordinates are calculated use its galaxy's mass-profiles.
        """

        self.redshift = redshift
        self.galaxies = galaxies
        self.positions = positions

        if compute_deflections:
            def calculate_deflections(pos):
                return sum(map(lambda galaxy: galaxy.deflections_from_grid(pos), galaxies))

            self.deflections = list(map(lambda pos: calculate_deflections(pos), self.positions))

        self.cosmology = cosmology

    def trace_to_next_plane(self):
        """Trace the positions to the next plane."""
        return list(map(lambda positions, deflections: np.subtract(positions, deflections),
                        self.positions, self.deflections))


class PlaneImage(scaled_array.ScaledRectangularPixelArray):

    def __init__(self, array, pixel_scales, grid, origin=(0.0, 0.0)):
        self.grid = grid
        super(PlaneImage, self).__init__(array=array, pixel_scales=pixel_scales, origin=origin)
