import autoarray as aa
import autofit as af
import autolens as al
from test_autolens.simulate import simulate_util

import os


def simulate_image_from_galaxies_and_output_to_fits(
    data_resolution,
    data_type,
    sub_size,
    galaxies,
    psf_shape_2d=(51, 51),
    exposure_time=300.0,
    background_sky_level=1.0,
):

    pixel_scales = simulate_util.pixel_scale_from_data_resolution(
        data_resolution=data_resolution
    )
    shape_2d = simulate_util.shape_from_data_resolution(data_resolution=data_resolution)

    # Simulate a simple Gaussian PSF for the image.
    psf = aa.kernel.from_gaussian(
        shape_2d=psf_shape_2d, sigma=pixel_scales, pixel_scales=pixel_scales
    )

    # Setup the image-plane al.ogrid of the Imaging array which will be used for generating the image of the
    # simulated strong lens. A high-res sub-grid is necessary to ensure we fully resolve the central regions of the
    # lens and source galaxy light.
    image_plane_grid = aa.grid.uniform(
        shape_2d=shape_2d, pixel_scales=pixel_scales, sub_size=sub_size
    )

    # Use the input galaxies to setup a tracer, which will generate the image for the simulated Imaging data_type.
    tracer = al.Tracer.from_galaxies(galaxies=galaxies)

    # Simulate the Imaging data_type, remembering that we use a special image which ensures edge-effects don't
    # degrade our modeling of the telescope optics (e.al. the PSF convolution).

    imaging_simulator = al.ImagingSimulator(shape_2d=shape_2d, pixel_scales=pixel_scales,
                                            exposure_time=exposure_time, psf=psf, background_sky_level=background_sky_level)

    imaging = imaging_simulator.simulate_from_tracer_and_grid(
        tracer=tracer,
        add_noise=True,
        grid=image_plane_grid,
    )

    # Now, lets output this simulated imaging-simulate to the test_autoarray/simulate folder.
    test_path = "{}/../".format(os.path.dirname(os.path.realpath(__file__)))

    data_path = af.path_util.make_and_return_path_from_path_and_folder_names(
        path=test_path, folder_names=["simulate", data_type, data_resolution]
    )

    imaging.output_to_fits(
        image_path=data_path + "image.fits",
        psf_path=data_path + "psf.fits",
        noise_map_path=data_path + "noise_map.fits",
        overwrite=True,
    )

    aa.plot.imaging.subplot(
        imaging=imaging,
        output_filename="imaging",
        output_path=data_path,
        output_format="png",
    )

    aa.plot.imaging.individual(
        imaging=imaging,
        should_plot_image=True,
        should_plot_noise_map=True,
        should_plot_psf=True,
        should_plot_signal_to_noise_map=True,
        output_path=data_path,
        output_format="png",
    )

    al.plot.ray_tracing.subplot(
        tracer=tracer,
        output_filename="tracer",
        output_path=data_path,
        output_format="png",
        grid=image_plane_grid,
    )

    al.plot.ray_tracing.individual(
        tracer=tracer,
        should_plot_profile_image=True,
        should_plot_source_plane=True,
        should_plot_convergence=True,
        should_plot_potential=True,
        should_plot_deflections=True,
        output_path=data_path,
        output_format="png",
        grid=image_plane_grid,
    )


def make_lens_light_dev_vaucouleurs(data_resolutions, sub_size):

    data_type = "lens_light_dev_vaucouleurs"

    # This lens-only system has a Dev Vaucouleurs spheroid / bulge.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalDevVaucouleurs(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.1,
            effective_radius=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, al.Galaxy(redshift=1.0)],
        )


def make_lens_bulge_disk(data_resolutions, sub_size):

    data_type = "lens_bulge_disk"

    # This source-only system has a Dev Vaucouleurs spheroid / bulge and surrounding Exponential envelope

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalDevVaucouleurs(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.1,
            effective_radius=1.0,
        ),
        envelope=al.lp.EllipticalExponential(
            centre=(0.0, 0.0),
            axis_ratio=0.7,
            phi=60.0,
            intensity=1.0,
            effective_radius=2.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, al.Galaxy(redshift=1.0)],
        )


def make_lens_x2_light(data_resolutions, sub_size):

    data_type = "lens_x2_light"

    # This source-only system has two Sersic bulges separated by 2.0"

    lens_galaxy_0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalSersic(
            centre=(-1.0, -1.0),
            axis_ratio=0.8,
            phi=0.0,
            intensity=1.0,
            effective_radius=1.0,
            sersic_index=3.0,
        ),
    )

    lens_galaxy_1 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalSersic(
            centre=(1.0, 1.0),
            axis_ratio=0.8,
            phi=0.0,
            intensity=1.0,
            effective_radius=1.0,
            sersic_index=3.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy_0, lens_galaxy_1, al.Galaxy(redshift=1.0)],
        )


def make_lens_mass__source_smooth(data_resolutions, sub_size):

    data_type = "lens_mass__source_smooth"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, source_galaxy],
        )


def make_lens_mass__source_cuspy(data_resolutions, sub_size):

    data_type = "lens_mass__source_cuspy"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.1,
            effective_radius=0.5,
            sersic_index=3.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, source_galaxy],
        )


def make_lens_sis__source_smooth(data_resolutions, sub_size):

    data_type = "lens_sis__source_smooth"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.SphericalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, source_galaxy],
        )


def make_lens_sis__source_smooth__offset_centre(data_resolutions, sub_size):

    data_type = "lens_sis__source_smooth__offset_centre"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.SphericalIsothermal(
            centre=(4.0, 4.0), einstein_radius=1.6
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(4.0, 4.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, source_galaxy],
        )


def make_lens_light__source_smooth(data_resolutions, sub_size):

    data_type = "lens_light__source_smooth"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.5,
            effective_radius=0.8,
            sersic_index=4.0,
        ),
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, source_galaxy],
        )


def make_lens_light__source_cuspy(data_resolutions, sub_size):

    data_type = "lens_light__source_cuspy"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.5,
            effective_radius=0.8,
            sersic_index=4.0,
        ),
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.1,
            effective_radius=0.5,
            sersic_index=3.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_image_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            sub_size=sub_size,
            galaxies=[lens_galaxy, source_galaxy],
        )
