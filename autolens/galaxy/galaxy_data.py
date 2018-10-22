import numpy as np

from autolens.imaging import scaled_array
from autolens.imaging import mask as msk


class GalaxyData(scaled_array.ScaledSquarePixelArray):

    def __new__(cls, data, noise_map, mask, sub_grid_size=2):
        return np.array(mask.map_2d_array_to_masked_1d_array(data)).view(cls)

    def __init__(self, data, noise_map, mask, sub_grid_size=2):
        """
        The lensing _image is the collection of data (images, noise-maps, PSF), a mask, grids, convolvers and other \
        utilities that are used for modeling and fitting an _image of a strong lens.

        Whilst the _image data is initially loaded in 2D, for the lensing _image the masked-_image (and noise-maps) \
        are reduced to 1D arrays for faster calculations.

        Parameters
        ----------
        data : scaled_array.ScaledSquarePixelArray
            The original _image data in 2D.
        mask: msk.Mask
            The 2D mask that is applied to the _image.
        sub_grid_size : int
            The size of the sub-grid used for each lensing SubGrid. E.g. a value of 2 grids each _image-pixel on a 2x2 \
            sub-grid.
        image_psf_shape : (int, int)
            The shape of the PSF used for convolving model images generated using analytic light profiles. A smaller \
            shape will trim the PSF relative to the input _image PSF, giving a faster analysis run-time.
        """
        super().__init__(array=data, pixel_scale=data.pixel_scale)

        self.data = data
        self.noise_map = mask.map_2d_array_to_masked_1d_array(array_2d=noise_map)
        self.mask = mask
        self.sub_grid_size = sub_grid_size

        self.grids = msk.ImagingGrids.grids_from_mask_sub_grid_size_and_psf_shape(mask=mask,
                     sub_grid_size=sub_grid_size, psf_shape=(1,1))

        self.unmasked_grids = msk.ImagingGrids.padded_grids_from_mask_sub_grid_size_and_psf_shape(mask=mask,
                              sub_grid_size=sub_grid_size, psf_shape=(1,1))

    def __array_finalize__(self, obj):
        super(GalaxyData, self).__array_finalize__(obj)
        if isinstance(obj, GalaxyData):
            self.data = obj.data
            self.mask = obj.mask
            self.sub_grid_size = obj.sub_grid_size
            self.grids = obj.grids
            self.unmasked_grids = obj.unmasked_grids