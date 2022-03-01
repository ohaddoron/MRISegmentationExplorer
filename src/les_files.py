import numpy as np
import typing as tp

from loguru import logger


def _parse_arr(arr: tp.Union[str, bytes]):
    """
    parses the provided input into array of data

    :param arr: provided input to parse
    :type arr: tp.Union[str, bytes]
    :return: array of bytes
    :rtype: bytes
    """

    if isinstance(arr, str):
        with open(arr, 'rb') as f:
            return f.read()
    else:
        return arr


def read_les_file_header(arr: tp.Union[str, bytes], offset=0):
    """
    Reads a "header" of a les file. The header is composed of 6 uint16 values (12 bytes) and defines a cuboid in
    which a lesion exists.
    The header is 6 uint16 values defining the x, y, z position of the the lesion ROI relative to the image origins.

    :param arr: array of data or a path to a les file containing data to be read
    :type arr: tp.Union[str, bytes]
    :param offset: offset value from the beginning of the file defining the current segment, defaults to 0
    :type offset: int, optional
    :return: list of start end pairs ordered as (y, x, z)
    :rtype: tp.List[tp.Tuple[int, int]]
    """
    arr = _parse_arr(arr)
    arr = np.array([int.from_bytes(arr[i: i + 2], 'little', signed=False)
                    for i in range(offset, offset + 12, 2)]).reshape(2, 3)
    assert min(arr[1] - arr[0]
               ), 'max values must be greater than min values in header'

    # returns ((ymin, ymax), (xmin, xmax), (zmin, zmax))
    return [tuple(arr[:, 0]), tuple(arr[:, 1]), tuple(arr[:, 2])]


def _get_data_length(header: tp.List[tp.Tuple[int, int]]):
    return np.prod([(item[1] - item[0] + 1) for item in header])


def _get_data_shape(header: tp.List[tp.Tuple[int, int]]):
    return (header[2][1] - header[2][0] + 1,
            header[1][1] - header[1][0] + 1,
            header[0][1] - header[0][0] + 1)


def read_les_file_data(arr: tp.Union[str, bytes], header: tp.List[tp.Tuple[int, int]], offset: tp.Optional[int] = 12):
    """
    Reads data associated with a single header and following a specific offset. The minimal offset is 12 bytes, corresponding to the length of the first header

    :param arr: raw bytes array of a les file
    :type arr: bytes
    :param header: header of the current segmentation map
    :type header: List[Tuple[int, int]]
    :param offset: offset value from which the reading should begin, defaults to 12
    :type offset: int, optional
    :return: 3D array corresponding to different slices of the segmentation map
    :rtype: np.array
    """
    arr = _parse_arr(arr)
    assert offset >= 12, 'offset must be greater than 12 bytes, the length of the first header in the file'
    assert len(arr[offset: offset + _get_data_length(header)]
               ) == _get_data_length(header), 'number of bytes to read must the length defined by the header'

    shape = _get_data_shape(header)

    output = np.array([item for item in arr[offset: offset + _get_data_length(header)]]).reshape(shape)

    output = np.transpose(output, (0, 2, 1))
    return output


def read_all_maps_from_les_file(arr: tp.Union[str, bytes]) -> tp.List[dict]:
    """
    Reads all segmentation maps from the provided file into a list of headers and segmentations

    :param arr: array of data or a path to a les file containing data to be read
    :type arr: tp.Union[str, bytes]
    :return: list of 3D segmentation maps
    :rtype: tp.List[dict]
    """
    arr = _parse_arr(arr)
    offset = 0

    segmentation_maps = []

    while True:
        if offset == len(arr):
            return segmentation_maps

        # read header of the current offset
        header = read_les_file_header(arr, offset=offset)
        # update offset according to the number of bytes in a header
        offset += 12

        data = read_les_file_data(arr, header, offset=offset)

        segmentation_maps.append({'header': header, 'data': data})

        offset += _get_data_length(header)
