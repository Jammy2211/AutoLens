import pytest

from autolens import exc
from autofit.tools.dimension_type import map_types
from autolens.model import dimensions as dim


class TestLength(object):

    def test__conversions_from_arcsec_to_kpc_and_back__errors_raised_if_no_kpc_per_arcsec(self):
        unit_arcsec = dim.Length(value=2.0)

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit_length == 'arcsec'

        unit_arcsec = unit_arcsec.convert(unit_length='arcsec')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'arcsec'

        unit_kpc = unit_arcsec.convert(unit_length='kpc', kpc_per_arcsec=2.0)

        assert unit_kpc == 4.0
        assert unit_kpc.unit == 'kpc'

        unit_kpc = unit_kpc.convert(unit_length='kpc')

        assert unit_kpc == 4.0
        assert unit_kpc.unit == 'kpc'

        unit_arcsec = unit_kpc.convert(unit_length='arcsec', kpc_per_arcsec=2.0)

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'arcsec'

        with pytest.raises(exc.UnitsException):
            unit_arcsec.convert(unit_length='kpc')
            unit_kpc.convert(unit_length='arcsec')
            unit_arcsec.convert(unit_length='lol')


class TestLuminosity(object):

    def test__conversions_from_eps_and_counts_and_back__errors_raised_if_no_exposure_time(self):

        unit_eps = dim.Luminosity(value=2.0)

        assert unit_eps == 2.0
        assert unit_eps.unit_luminosity == 'eps'

        unit_eps = unit_eps.convert(unit_luminosity='eps')

        assert unit_eps == 2.0
        assert unit_eps.unit == 'eps'

        unit_counts = unit_eps.convert(unit_luminosity='counts', exposure_time=2.0)

        assert unit_counts == 4.0
        assert unit_counts.unit == 'counts'

        unit_counts = unit_counts.convert(unit_luminosity='counts')

        assert unit_counts == 4.0
        assert unit_counts.unit == 'counts'

        unit_eps = unit_counts.convert(unit_luminosity='eps', exposure_time=2.0)

        assert unit_eps == 2.0
        assert unit_eps.unit == 'eps'

        with pytest.raises(exc.UnitsException):
            unit_eps.convert(unit_luminosity='counts')
            unit_counts.convert(unit_luminosity='eps')
            unit_eps.convert(unit_luminosity='lol')


class TestMass(object):

    def test__conversions_from_angular_and_sol_mass_and_back__errors_raised_if_no_exposure_time(self):

        unit_angular = dim.Mass(value=2.0)

        assert unit_angular == 2.0
        assert unit_angular.unit_mass == 'angular'

        unit_angular = unit_angular.convert(unit_mass='angular')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular'

        unit_sol_mass = unit_angular.convert(unit_mass='solMass', critical_surface_density=2.0)

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass'

        unit_sol_mass = unit_sol_mass.convert(unit_mass='solMass')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass'

        unit_angular = unit_sol_mass.convert(unit_mass='angular', critical_surface_density=2.0)

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular'

        with pytest.raises(exc.UnitsException):
            unit_angular.convert(unit_mass='solMass')
            unit_sol_mass.convert(unit_mass='angular')
            unit_angular.convert(unit_mass='lol')


class TestMassOverLuminosity(object):

    def test__conversions_from_angular_and_sol_mass_and_back__errors_raised_if_critical_mass_density(self):

        unit_angular = dim.MassOverLuminosity(value=2.0)

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / eps'

        unit_angular = unit_angular.convert(unit_mass='angular', unit_luminosity='eps')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / eps'

        unit_sol_mass = unit_angular.convert(unit_mass='solMass', critical_surface_density=2.0,
                                             unit_luminosity='eps')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass / eps'

        unit_sol_mass = unit_sol_mass.convert(unit_mass='solMass', unit_luminosity='eps')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass / eps'

        unit_angular = unit_sol_mass.convert(unit_mass='angular', critical_surface_density=2.0,
                                             unit_luminosity='eps')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / eps'

        with pytest.raises(exc.UnitsException):
            unit_angular.convert(unit_mass='solMass', unit_luminosity='eps')
            unit_sol_mass.convert(unit_mass='angular', unit_luminosity='eps')
            unit_angular.convert(unit_mass='lol', unit_luminosity='eps')
            
    def test__conversions_from_eps_and_counts_and_back__errors_raised_if_no_exposure_time(self):

        unit_eps = dim.MassOverLuminosity(value=2.0)

        assert unit_eps == 2.0
        assert unit_eps.unit == 'angular / eps'

        unit_eps = unit_eps.convert(unit_mass='angular', unit_luminosity='eps')

        assert unit_eps == 2.0
        assert unit_eps.unit == 'angular / eps'

        unit_counts = unit_eps.convert(unit_mass='angular', exposure_time=2.0, unit_luminosity='counts')

        assert unit_counts == 1.0
        assert unit_counts.unit == 'angular / counts'

        unit_counts = unit_counts.convert(unit_mass='angular', unit_luminosity='counts')

        assert unit_counts == 1.0
        assert unit_counts.unit == 'angular / counts'

        unit_eps = unit_counts.convert(unit_mass='angular', exposure_time=2.0, unit_luminosity='eps')

        assert unit_eps == 2.0
        assert unit_eps.unit == 'angular / eps'

        with pytest.raises(exc.UnitsException):
            unit_eps.convert(unit_mass='angular', unit_luminosity='eps')
            unit_counts.convert(unit_mass='angular', unit_luminosity='eps')
            unit_eps.convert(unit_mass='lol', unit_luminosity='eps')


class TestMassOverLength2(object):

    def test__conversions_from_angular_and_sol_mass_and_back__errors_raised_if_critical_mass_density(self):

        unit_angular = dim.MassOverLength2(value=2.0)

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / arcsec^2'

        unit_angular = unit_angular.convert(unit_mass='angular', unit_length='arcsec')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / arcsec^2'

        unit_sol_mass = unit_angular.convert(unit_mass='solMass', critical_surface_density=2.0,
                                             unit_length='arcsec')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass / arcsec^2'

        unit_sol_mass = unit_sol_mass.convert(unit_mass='solMass', unit_length='arcsec')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass / arcsec^2'

        unit_angular = unit_sol_mass.convert(unit_mass='angular', critical_surface_density=2.0,
                                             unit_length='arcsec')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / arcsec^2'

        with pytest.raises(exc.UnitsException):
            unit_angular.convert(unit_mass='solMass', unit_length='eps')
            unit_sol_mass.convert(unit_mass='angular', unit_length='eps')
            unit_angular.convert(unit_mass='lol', unit_length='eps')

    def test__conversions_from_arcsec_to_kpc_and_back__errors_raised_if_no_kpc_per_arcsec(self):

        unit_arcsec = dim.MassOverLength2(value=2.0, unit_mass='solMass')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'solMass / arcsec^2'

        unit_arcsec = unit_arcsec.convert(unit_length='arcsec', unit_mass='solMass')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'solMass / arcsec^2'

        unit_kpc = unit_arcsec.convert(unit_length='kpc', kpc_per_arcsec=2.0, unit_mass='solMass')

        assert unit_kpc == 2.0 / 2.0**2.0
        assert unit_kpc.unit == 'solMass / kpc^2'

        unit_kpc = unit_kpc.convert(unit_length='kpc', unit_mass='solMass')

        assert unit_kpc == 2.0 / 2.0**2.0
        assert unit_kpc.unit == 'solMass / kpc^2'

        unit_arcsec = unit_kpc.convert(unit_length='arcsec', kpc_per_arcsec=2.0, unit_mass='solMass')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'solMass / arcsec^2'

        with pytest.raises(exc.UnitsException):
            unit_arcsec.convert(unit_length='kpc', unit_mass='solMass')
            unit_kpc.convert(unit_length='arcsec', unit_mass='solMass')
            unit_arcsec.convert(unit_length='lol', unit_mass='solMass')


class TestMassOverLength3(object):

    def test__conversions_from_angular_and_sol_mass_and_back__errors_raised_if_critical_mass_density(self):

        unit_angular = dim.MassOverLength3(value=2.0)

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / arcsec^3'

        unit_angular = unit_angular.convert(unit_mass='angular', unit_length='arcsec')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / arcsec^3'

        unit_sol_mass = unit_angular.convert(unit_mass='solMass', critical_surface_density=2.0,
                                             unit_length='arcsec')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass / arcsec^3'

        unit_sol_mass = unit_sol_mass.convert(unit_mass='solMass', unit_length='arcsec')

        assert unit_sol_mass == 4.0
        assert unit_sol_mass.unit == 'solMass / arcsec^3'

        unit_angular = unit_sol_mass.convert(unit_mass='angular', critical_surface_density=2.0,
                                             unit_length='arcsec')

        assert unit_angular == 2.0
        assert unit_angular.unit == 'angular / arcsec^3'

        with pytest.raises(exc.UnitsException):
            unit_angular.convert(unit_mass='solMass', unit_length='eps')
            unit_sol_mass.convert(unit_mass='angular', unit_length='eps')
            unit_angular.convert(unit_mass='lol', unit_length='eps')

    def test__conversions_from_arcsec_to_kpc_and_back__errors_raised_if_no_kpc_per_arcsec(self):

        unit_arcsec = dim.MassOverLength3(value=2.0, unit_mass='solMass')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'solMass / arcsec^3'

        unit_arcsec = unit_arcsec.convert(unit_length='arcsec', unit_mass='solMass')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'solMass / arcsec^3'

        unit_kpc = unit_arcsec.convert(unit_length='kpc', kpc_per_arcsec=2.0, unit_mass='solMass')

        assert unit_kpc == 2.0 / 2.0**3.0
        assert unit_kpc.unit == 'solMass / kpc^3'

        unit_kpc = unit_kpc.convert(unit_length='kpc', unit_mass='solMass')

        assert unit_kpc == 2.0 / 2.0**3.0
        assert unit_kpc.unit == 'solMass / kpc^3'

        unit_arcsec = unit_kpc.convert(unit_length='arcsec', kpc_per_arcsec=2.0, unit_mass='solMass')

        assert unit_arcsec == 2.0
        assert unit_arcsec.unit == 'solMass / arcsec^3'

        with pytest.raises(exc.UnitsException):
            unit_arcsec.convert(unit_length='kpc', unit_mass='solMass')
            unit_kpc.convert(unit_length='arcsec', unit_mass='solMass')
            unit_arcsec.convert(unit_length='lol', unit_mass='solMass')


class MockDimensionsProfile(dim.DimensionsProfile):

    def __init__(self,
                 position: dim.Position = None,
                 param_float: float = None,
                 length: dim.Length = None,
                 luminosity : dim.Luminosity = None,
                 mass : dim.Mass = None,
                 mass_over_luminosity: dim.MassOverLuminosity = None):

        super(MockDimensionsProfile, self).__init__()

        self.position = position
        self.param_float = param_float
        self.luminosity = luminosity
        self.length = length
        self.mass = mass
        self.mass_over_luminosity = mass_over_luminosity

    @dim.convert_profile_to_input_units
    def unit_length_calc(self,
                    length_0 : dim.Length = None, length_1 : dim.Length = None,
                    kpc_per_arcsec : float = None):

        return dim.Length(self.length + length_0, self.length.unit_length)

    @dim.convert_profile_to_input_units
    def unit_luminosity_calc(self,
                    luminosity_0 : dim.Luminosity = None, luminosity_1 : dim.Luminosity = None,
                    exposure_time : float = None):

        return dim.Luminosity(self.luminosity + luminosity_0, self.luminosity.unit_luminosity)

    @dim.convert_profile_to_input_units
    def unit_mass_calc(self,
                    mass_0 : dim.Mass = None, mass_1 : dim.Mass = None,
                    critical_surface_density : dim.MassOverLength2 = None):

        return dim.Mass(self.mass + mass_0, self.mass.unit_mass)


class TestDimensionsProfile(object):

    def test__arcsec_to_kpc_conversions_of_length__float_and_tuple_length__conversion_converts_values(self):

        profile_arcsec = MockDimensionsProfile(
            position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),
            param_float=2.0,
            length=dim.Length(value=3.0, unit_length='arcsec'),
            luminosity=dim.Luminosity(value=4.0, unit_luminosity='eps'),
            mass=dim.Mass(value=5.0, unit_mass='angular'),
            mass_over_luminosity=dim.MassOverLuminosity(value=6.0, unit_luminosity='eps', unit_mass='angular'))

        assert profile_arcsec.position == (1.0, 2.0)
        assert profile_arcsec.position[0].unit_length == 'arcsec'
        assert profile_arcsec.position[1].unit_length == 'arcsec'
        assert profile_arcsec.param_float == 2.0
        assert profile_arcsec.length == 3.0
        assert profile_arcsec.length.unit_length == 'arcsec'
        assert profile_arcsec.luminosity == 4.0
        assert profile_arcsec.luminosity.unit_luminosity == 'eps'
        assert profile_arcsec.mass == 5.0
        assert profile_arcsec.mass.unit_mass == 'angular'
        assert profile_arcsec.mass_over_luminosity == 6.0
        assert profile_arcsec.mass_over_luminosity.unit == 'angular / eps'

        profile_arcsec = profile_arcsec.new_profile_with_units_converted(unit_length='arcsec')

        assert profile_arcsec.position == (1.0, 2.0)
        assert profile_arcsec.position[0].unit == 'arcsec'
        assert profile_arcsec.position[1].unit == 'arcsec'
        assert profile_arcsec.param_float == 2.0
        assert profile_arcsec.length == 3.0
        assert profile_arcsec.length.unit == 'arcsec'
        assert profile_arcsec.luminosity == 4.0
        assert profile_arcsec.luminosity.unit == 'eps'
        assert profile_arcsec.mass == 5.0
        assert profile_arcsec.mass.unit_mass == 'angular'
        assert profile_arcsec.mass_over_luminosity == 6.0
        assert profile_arcsec.mass_over_luminosity.unit == 'angular / eps'

        profile_kpc = profile_arcsec.new_profile_with_units_converted(unit_length='kpc', kpc_per_arcsec=2.0)

        assert profile_kpc.position == (2.0, 4.0)
        assert profile_kpc.position[0].unit == 'kpc'
        assert profile_kpc.position[1].unit == 'kpc'
        assert profile_kpc.param_float == 2.0
        assert profile_kpc.length == 6.0
        assert profile_kpc.length.unit == 'kpc'
        assert profile_kpc.luminosity == 4.0
        assert profile_kpc.luminosity.unit == 'eps'
        assert profile_arcsec.mass == 5.0
        assert profile_arcsec.mass.unit_mass == 'angular'
        assert profile_kpc.mass_over_luminosity == 6.0
        assert profile_kpc.mass_over_luminosity.unit == 'angular / eps'

        profile_kpc = profile_kpc.new_profile_with_units_converted(unit_length='kpc')

        assert profile_kpc.position == (2.0, 4.0)
        assert profile_kpc.position[0].unit == 'kpc'
        assert profile_kpc.position[1].unit == 'kpc'
        assert profile_kpc.param_float == 2.0
        assert profile_kpc.length == 6.0
        assert profile_kpc.length.unit == 'kpc'
        assert profile_kpc.luminosity == 4.0
        assert profile_kpc.luminosity.unit == 'eps'
        assert profile_arcsec.mass == 5.0
        assert profile_arcsec.mass.unit_mass == 'angular'
        assert profile_kpc.mass_over_luminosity == 6.0
        assert profile_kpc.mass_over_luminosity.unit == 'angular / eps'

        profile_arcsec = profile_kpc.new_profile_with_units_converted(unit_length='arcsec', kpc_per_arcsec=2.0)

        assert profile_arcsec.position == (1.0, 2.0)
        assert profile_arcsec.position[0].unit == 'arcsec'
        assert profile_arcsec.position[1].unit == 'arcsec'
        assert profile_arcsec.param_float == 2.0
        assert profile_arcsec.length == 3.0
        assert profile_arcsec.length.unit == 'arcsec'
        assert profile_arcsec.luminosity == 4.0
        assert profile_arcsec.luminosity.unit == 'eps'
        assert profile_arcsec.mass == 5.0
        assert profile_arcsec.mass.unit_mass == 'angular'
        assert profile_arcsec.mass_over_luminosity == 6.0
        assert profile_arcsec.mass_over_luminosity.unit == 'angular / eps'

    def test__conversion_requires_kpc_per_arcsec_but_does_not_supply_it_raises_error(self):

        profile_arcsec = MockDimensionsProfile(position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),)

        with pytest.raises(exc.UnitsException):
            profile_arcsec.new_profile_with_units_converted(unit_length='kpc')

        profile_kpc = profile_arcsec.new_profile_with_units_converted(unit_length='kpc', kpc_per_arcsec=2.0)

        with pytest.raises(exc.UnitsException):
            profile_kpc.new_profile_with_units_converted(unit_length='arcsec')

    def test__eps_to_counts_conversions_of_luminosity__conversions_convert_values(self):

        profile_eps = MockDimensionsProfile(
            position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),
            param_float=2.0,
            length=dim.Length(value=3.0, unit_length='arcsec'),
            luminosity=dim.Luminosity(value=4.0, unit_luminosity='eps'),
            mass=dim.Mass(value=5.0, unit_mass='angular'),
            mass_over_luminosity=dim.MassOverLuminosity(value=6.0, unit_luminosity='eps', unit_mass='angular'))

        assert profile_eps.position == (1.0, 2.0)
        assert profile_eps.position[0].unit_length == 'arcsec'
        assert profile_eps.position[1].unit_length == 'arcsec'
        assert profile_eps.param_float == 2.0
        assert profile_eps.length == 3.0
        assert profile_eps.length.unit_length == 'arcsec'
        assert profile_eps.luminosity == 4.0
        assert profile_eps.luminosity.unit_luminosity == 'eps'
        assert profile_eps.mass == 5.0
        assert profile_eps.mass.unit_mass == 'angular'
        assert profile_eps.mass_over_luminosity == 6.0
        assert profile_eps.mass_over_luminosity.unit == 'angular / eps'

        profile_eps = profile_eps.new_profile_with_units_converted(unit_luminosity='eps')

        assert profile_eps.position == (1.0, 2.0)
        assert profile_eps.position[0].unit_length == 'arcsec'
        assert profile_eps.position[1].unit_length == 'arcsec'
        assert profile_eps.param_float == 2.0
        assert profile_eps.length == 3.0
        assert profile_eps.length.unit_length == 'arcsec'
        assert profile_eps.luminosity == 4.0
        assert profile_eps.luminosity.unit_luminosity == 'eps'
        assert profile_eps.mass == 5.0
        assert profile_eps.mass.unit_mass == 'angular'
        assert profile_eps.mass_over_luminosity == 6.0
        assert profile_eps.mass_over_luminosity.unit == 'angular / eps'
        
        profile_counts = profile_eps.new_profile_with_units_converted(unit_luminosity='counts',
                                                                      exposure_time=10.0)

        assert profile_counts.position == (1.0, 2.0)
        assert profile_counts.position[0].unit_length == 'arcsec'
        assert profile_counts.position[1].unit_length == 'arcsec'
        assert profile_counts.param_float == 2.0
        assert profile_counts.length == 3.0
        assert profile_counts.length.unit_length == 'arcsec'
        assert profile_counts.luminosity == 40.0
        assert profile_counts.luminosity.unit_luminosity == 'counts'
        assert profile_counts.mass == 5.0
        assert profile_counts.mass.unit_mass == 'angular'
        assert profile_counts.mass_over_luminosity == pytest.approx(0.6, 1.0e-4)
        assert profile_counts.mass_over_luminosity.unit == 'angular / counts'

        profile_counts = profile_counts.new_profile_with_units_converted(unit_luminosity='counts')


        assert profile_counts.position == (1.0, 2.0)
        assert profile_counts.position[0].unit_length == 'arcsec'
        assert profile_counts.position[1].unit_length == 'arcsec'
        assert profile_counts.param_float == 2.0
        assert profile_counts.length == 3.0
        assert profile_counts.length.unit_length == 'arcsec'
        assert profile_counts.luminosity == 40.0
        assert profile_counts.luminosity.unit_luminosity == 'counts'
        assert profile_counts.mass == 5.0
        assert profile_counts.mass.unit_mass == 'angular'
        assert profile_counts.mass_over_luminosity == pytest.approx(0.6, 1.0e-4)
        assert profile_counts.mass_over_luminosity.unit == 'angular / counts'

        profile_eps = profile_counts.new_profile_with_units_converted(unit_luminosity='eps',
                                                                      exposure_time=10.0)

        assert profile_eps.position == (1.0, 2.0)
        assert profile_eps.position[0].unit_length == 'arcsec'
        assert profile_eps.position[1].unit_length == 'arcsec'
        assert profile_eps.param_float == 2.0
        assert profile_eps.length == 3.0
        assert profile_eps.length.unit_length == 'arcsec'
        assert profile_eps.luminosity == 4.0
        assert profile_eps.luminosity.unit_luminosity == 'eps'
        assert profile_eps.mass == 5.0
        assert profile_eps.mass.unit_mass == 'angular'
        assert profile_eps.mass_over_luminosity == pytest.approx(6.0, 1.0e-4)
        assert profile_eps.mass_over_luminosity.unit == 'angular / eps'

    def test__luminosity_conversion_requires_exposure_time_but_does_not_supply_it_raises_error(self):

        profile_eps = MockDimensionsProfile(
            position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),
            param_float=2.0,
            length=dim.Length(value=3.0, unit_length='arcsec'),
            luminosity=dim.Luminosity(value=4.0, unit_luminosity='eps'),
            mass=dim.Mass(value=5.0, unit_mass='angular'),
            mass_over_luminosity=dim.MassOverLuminosity(value=6.0, unit_luminosity='eps', unit_mass='angular'))

        with pytest.raises(exc.UnitsException):
            profile_eps.new_profile_with_units_converted(unit_luminosity='counts')

        profile_counts = profile_eps.new_profile_with_units_converted(unit_luminosity='counts', exposure_time=10.0)

        with pytest.raises(exc.UnitsException):
            profile_counts.new_profile_with_units_converted(unit_luminosity='eps')

    def test__angular_to_solMass_conversions_of_mass__conversions_convert_values(self):
        
        profile_angular = MockDimensionsProfile(
            position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),
            param_float=2.0,
            length=dim.Length(value=3.0, unit_length='arcsec'),
            luminosity=dim.Luminosity(value=4.0, unit_luminosity='eps'),
            mass=dim.Mass(value=5.0, unit_mass='angular'),
            mass_over_luminosity=dim.MassOverLuminosity(value=6.0, unit_luminosity='eps', unit_mass='angular'))

        assert profile_angular.position == (1.0, 2.0)
        assert profile_angular.position[0].unit_length == 'arcsec'
        assert profile_angular.position[1].unit_length == 'arcsec'
        assert profile_angular.param_float == 2.0
        assert profile_angular.length == 3.0
        assert profile_angular.length.unit_length == 'arcsec'
        assert profile_angular.luminosity == 4.0
        assert profile_angular.luminosity.unit_luminosity == 'eps'
        assert profile_angular.mass == 5.0
        assert profile_angular.mass.unit_mass == 'angular'
        assert profile_angular.mass_over_luminosity == 6.0
        assert profile_angular.mass_over_luminosity.unit == 'angular / eps'

        profile_angular = profile_angular.new_profile_with_units_converted(unit_mass='angular')

        assert profile_angular.position == (1.0, 2.0)
        assert profile_angular.position[0].unit_length == 'arcsec'
        assert profile_angular.position[1].unit_length == 'arcsec'
        assert profile_angular.param_float == 2.0
        assert profile_angular.length == 3.0
        assert profile_angular.length.unit_length == 'arcsec'
        assert profile_angular.luminosity == 4.0
        assert profile_angular.luminosity.unit_luminosity == 'eps'
        assert profile_angular.mass == 5.0
        assert profile_angular.mass.unit_mass == 'angular'
        assert profile_angular.mass_over_luminosity == 6.0
        assert profile_angular.mass_over_luminosity.unit == 'angular / eps'

        profile_solMass = profile_angular.new_profile_with_units_converted(unit_mass='solMass',
                                                                      critical_surface_density=10.0)

        assert profile_solMass.position == (1.0, 2.0)
        assert profile_solMass.position[0].unit_length == 'arcsec'
        assert profile_solMass.position[1].unit_length == 'arcsec'
        assert profile_solMass.param_float == 2.0
        assert profile_solMass.length == 3.0
        assert profile_solMass.length.unit_length == 'arcsec'
        assert profile_solMass.luminosity == 4.0
        assert profile_solMass.luminosity.unit_luminosity == 'eps'
        assert profile_solMass.mass == 50.0
        assert profile_solMass.mass.unit_mass == 'solMass'
        assert profile_solMass.mass_over_luminosity == pytest.approx(60.0, 1.0e-4)
        assert profile_solMass.mass_over_luminosity.unit == 'solMass / eps'

        profile_solMass = profile_solMass.new_profile_with_units_converted(unit_mass='solMass')

        assert profile_solMass.position == (1.0, 2.0)
        assert profile_solMass.position[0].unit_length == 'arcsec'
        assert profile_solMass.position[1].unit_length == 'arcsec'
        assert profile_solMass.param_float == 2.0
        assert profile_solMass.length == 3.0
        assert profile_solMass.length.unit_length == 'arcsec'
        assert profile_solMass.luminosity == 4.0
        assert profile_solMass.luminosity.unit_luminosity == 'eps'
        assert profile_solMass.mass == 50.0
        assert profile_solMass.mass.unit_mass == 'solMass'
        assert profile_solMass.mass_over_luminosity == pytest.approx(60.0, 1.0e-4)
        assert profile_solMass.mass_over_luminosity.unit == 'solMass / eps'

        profile_angular = profile_solMass.new_profile_with_units_converted(unit_mass='angular',
                                                                      critical_surface_density=10.0)

        assert profile_angular.position == (1.0, 2.0)
        assert profile_angular.position[0].unit_length == 'arcsec'
        assert profile_angular.position[1].unit_length == 'arcsec'
        assert profile_angular.param_float == 2.0
        assert profile_angular.length == 3.0
        assert profile_angular.length.unit_length == 'arcsec'
        assert profile_angular.luminosity == 4.0
        assert profile_angular.luminosity.unit_luminosity == 'eps'
        assert profile_angular.mass == 5.0
        assert profile_angular.mass.unit_mass == 'angular'
        assert profile_angular.mass_over_luminosity == pytest.approx(6.0, 1.0e-4)
        assert profile_angular.mass_over_luminosity.unit == 'angular / eps'

    def test__mass_conversion_requires_critical_surface_density_but_does_not_supply_it_raises_error(self):
        
        profile_angular = MockDimensionsProfile(
            position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),
            param_float=2.0,
            length=dim.Length(value=3.0, unit_length='arcsec'),
            luminosity=dim.Luminosity(value=4.0, unit_luminosity='eps'),
            mass=dim.Mass(value=5.0, unit_mass='angular'),
            mass_over_luminosity=dim.MassOverLuminosity(value=6.0, unit_luminosity='eps', unit_mass='angular'))

        with pytest.raises(exc.UnitsException):
            profile_angular.new_profile_with_units_converted(unit_mass='solMass')

        profile_solMass = profile_angular.new_profile_with_units_converted(unit_mass='solMass', critical_surface_density=10.0)

        with pytest.raises(exc.UnitsException):
            profile_solMass.new_profile_with_units_converted(unit_mass='angular')

class TestUnitCheckConversionWwrapper(object):

    def test__if_units_of_input_are_not_same_raises_error(self):

        profile = MockDimensionsProfile(
            position=(dim.Length(1.0, 'arcsec'), dim.Length(2.0, 'arcsec')),
            param_float=2.0,
            length=dim.Length(value=3.0, unit_length='arcsec'),
            luminosity=dim.Luminosity(value=4.0, unit_luminosity='eps'),
            mass=dim.Mass(value=5.0, unit_mass='angular'),
            mass_over_luminosity=dim.MassOverLuminosity(value=6.0, unit_luminosity='eps', unit_mass='angular'))

        profile.unit_length_calc(length_0=dim.Length(1.0, 'arcsec'), length_1=dim.Length(1.0, 'arcsec'))
        profile.unit_length_calc(length_0=dim.Length(1.0, 'kpc'), length_1=dim.Length(1.0, 'kpc'), kpc_per_arcsec=1.0)

        profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'eps'), luminosity_1=dim.Luminosity(1.0, 'eps'))
        profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'counts'), luminosity_1=dim.Luminosity(1.0, 'counts'),
                                     exposure_time=1.0)

        profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'angular'), mass_1=dim.Mass(1.0, 'angular'))
        profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'solMass'), mass_1=dim.Mass(1.0, 'solMass'),
                               critical_surface_density=1.0)

        with pytest.raises(exc.UnitsException):

            profile.unit_length_calc(length_0=dim.Length(1.0, 'arcsec'), length_1=dim.Length(1.0, 'kpc'), kpc_per_arcsec=1.0)
            profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'counts'), luminosity_1=dim.Luminosity(1.0, 'eps'),
                                         exposure_time=1.0)
            profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'solMass'), mass_1=dim.Mass(1.0, 'angular'),
                                   critical_surface_density=1.0)

    def test__profile_length_units_calculations__profile_is_converted_for_calculation_if_different_to_input_units(self):

        profile = MockDimensionsProfile(length=dim.Length(3.0, 'arcsec'))

        length = profile.unit_length_calc(length_0=dim.Length(1.0, 'arcsec'))
        assert length.unit_length == 'arcsec'
        assert length == 4.0

        length = profile.unit_length_calc(length_0=dim.Length(1.0, 'kpc'), kpc_per_arcsec=1.0)
        assert length.unit_length == 'kpc'
        assert length == 4.0

        length = profile.unit_length_calc(length_0=dim.Length(1.0, 'kpc'), kpc_per_arcsec=2.0)
        assert length.unit_length == 'kpc'
        assert length == 7.0
        
        profile = MockDimensionsProfile(length=dim.Length(3.0, 'kpc'))

        length = profile.unit_length_calc(length_0=dim.Length(1.0, 'kpc'))
        assert length.unit_length == 'kpc'
        assert length == 4.0

        length = profile.unit_length_calc(length_0=dim.Length(1.0, 'arcsec'), kpc_per_arcsec=1.0)
        assert length.unit_length == 'arcsec'
        assert length == 4.0

        length = profile.unit_length_calc(length_0=dim.Length(1.0, 'arcsec'), kpc_per_arcsec=2.0)
        assert length.unit_length == 'arcsec'
        assert length == 2.5

    def test__profile_luminosity_units_calculations__profile_is_converted_for_calculation_if_different_to_input_units(self):
        
        profile = MockDimensionsProfile(luminosity=dim.Luminosity(3.0, 'eps'))

        luminosity = profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'eps'))
        assert luminosity.unit_luminosity == 'eps'
        assert luminosity == 4.0

        luminosity = profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'counts'), exposure_time=1.0)
        assert luminosity.unit_luminosity == 'counts'
        assert luminosity == 4.0

        luminosity = profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'counts'), exposure_time=2.0)
        assert luminosity.unit_luminosity == 'counts'
        assert luminosity == 7.0

        profile = MockDimensionsProfile(luminosity=dim.Luminosity(3.0, 'counts'))

        luminosity = profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'counts'))
        assert luminosity.unit_luminosity == 'counts'
        assert luminosity == 4.0

        luminosity = profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'eps'), exposure_time=1.0)
        assert luminosity.unit_luminosity == 'eps'
        assert luminosity == 4.0

        luminosity = profile.unit_luminosity_calc(luminosity_0=dim.Luminosity(1.0, 'eps'), exposure_time=2.0)
        assert luminosity.unit_luminosity == 'eps'
        assert luminosity == 2.5

    def test__profile_mass_units_calculations__profile_is_converted_for_calculation_if_different_to_input_units(self):

        profile = MockDimensionsProfile(mass=dim.Mass(3.0, 'angular'))

        mass = profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'angular'))
        assert mass.unit_mass == 'angular'
        assert mass == 4.0

        critical_surface_density = dim.MassOverLength2(1.0, unit_length='arcsec', unit_mass='solMass')
        mass = profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'solMass'), critical_surface_density=critical_surface_density)
        assert mass.unit_mass == 'solMass'
        assert mass == 4.0

        critical_surface_density = dim.MassOverLength2(2.0, unit_length='arcsec', unit_mass='solMass')
        mass = profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'solMass'), critical_surface_density=critical_surface_density)
        assert mass.unit_mass == 'solMass'
        assert mass == 7.0

        profile = MockDimensionsProfile(mass=dim.Mass(3.0, 'solMass'))

        mass = profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'solMass'))
        assert mass.unit_mass == 'solMass'
        assert mass == 4.0

        critical_surface_density = dim.MassOverLength2(1.0, unit_length='arcsec', unit_mass='angular')
        mass = profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'angular'), critical_surface_density=critical_surface_density)
        assert mass.unit_mass == 'angular'
        assert mass == 4.0

        critical_surface_density = dim.MassOverLength2(2.0, unit_length='arcsec', unit_mass='angular')
        mass = profile.unit_mass_calc(mass_0=dim.Mass(1.0, 'angular'), critical_surface_density=critical_surface_density)
        assert mass.unit_mass == 'angular'
        assert mass == 2.5