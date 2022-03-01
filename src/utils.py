import os
from pathlib import Path

import SimpleITK as sitk
import numpy as np
import toml

from PIL import Image
import typing as tp
import numpy as np
from loguru import logger
from functools import lru_cache


@lru_cache
def _get_config(config_path: tp.Optional[str] = None, name: tp.Optional[str] = None):
    """
    Reads a configuration section for the configurtation file provided in config_path. If no section name is provided, will read the entire configuration file

    :param config_path: pathway to configuration file, if not provided will default to the local configuration path, defaults to None
    :type config_path: str
    :param name: section name, defaults to None
    :type name: tp.Optional[str], optional
    :return: requested configurations
    :rtype: dict
    """
    config_path = config_path or os.path.join(
        Path(__file__).parent, '../config.toml')
    with open(config_path) as f:
        config = toml.load(f)
    if name:
        return config[name]
    else:
        return config


@lru_cache
def get_config(name: tp.Optional[str] = None):
    config_path = os.path.join(os.path.dirname(__file__), '../config.toml')
    logger.debug(f'Reading {name} from {config_path}')
    return _get_config(config_path, name)


def read_dicom_images(dicom_dir: str) -> np.ndarray:
    """
    Reads dicom images from a directories

    :param dicom_dir: pathway to a directory containing dicom files
    :type dicom_dir: str
    :return: array stack of dicom images
    :rtype: :class:`np.ndarray`
    """
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_dir)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    nda = sitk.GetArrayFromImage(image)
    return nda


def overlay_segmentation_on_image(segmentation_slice: np.array,
                                  image: np.array,
                                  header: tp.List[tp.Tuple[int, int]],
                                  alpha=0.6):
    """
    Overlays a segmentation mask ontop of a dicom image. Performs on a single slice

    :param segmentation_slice: mask image for a single slice
    :type segmentation_slice: np.array
    :param image: dicom image that serves as a base image
    :type image: np.array
    :param header: header for the segmentation map depicting the lesion ROI
    :type header: tp.List[tp.Tuple[int, int]]
    :param alpha: alpha value to use when blending, defaults to 0.4
    :type alpha: float, optional
    :return: overlay of the lesion ontop of the relevant slice
    :rtype: PIL.Image.Image
    """

    image = np.array(Image.fromarray(image).convert('RGB'))

    mask = np.zeros_like(image)

    mask[header[0][0]:header[0][1] + 1, header[1]
                                        [0]:header[1][1] + 1, 1] = segmentation_slice * 255
    image_2 = image.copy()

    image_2 = np.maximum(image_2, mask)

    result = (1 - alpha) * image + alpha * image_2
    return Image.fromarray(result.astype(np.uint8))
