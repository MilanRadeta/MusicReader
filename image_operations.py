import cv2
import numpy as np

HORIZONTAL_PROJECTION = 0
VERTICAL_PROJECTION = 1


def dilate(image, kernel, iterations=1):
    """Morphological dilatation of an image
    :param image:
    :param kernel:
    :param iterations:
    """
    return cv2.dilate(image, kernel, iterations)


def erode(image, kernel, iterations=1):
    """Morphological erosion of an image
    :param image:
    :param kernel:
    :param iterations:
    """
    return cv2.erode(image, kernel, iterations)


def open_image(image, kernel=None):
    """Morphological opening of an image
    :param image:
    :param kernel:
    """
    if kernel is None:
        kernel = np.ones((1, 100))
    return dilate(erode(image, kernel), kernel)


def project_image(image, projection=HORIZONTAL_PROJECTION):
    """Make horizontal or vertical projection of an image
    :param projection:
    :param image:
    """
    projected_image = []

    image_height, image_width = image.shape[:2]
    first_limit = image_height if projection == HORIZONTAL_PROJECTION else image_width
    second_limit = image_width if projection == HORIZONTAL_PROJECTION else image_height
    for i in range(first_limit):
        projection_sum = 0
        for j in range(second_limit):
            projection_sum += image[i if projection == HORIZONTAL_PROJECTION else j,
                                    j if projection == HORIZONTAL_PROJECTION else i] == 255
        projected_image.append([255] * projection_sum + [0] * (second_limit - projection_sum))
    return np.uint8(np.array(projected_image))


def crop_image(image, crop_start=None, crop_width=None):
    """Return a cropped image
    :param image:
    :param crop_start:
    :param crop_width:
    """
    if crop_width is None:
        crop_width = len(image[0]) // 10

    if crop_start is None:
        end = 0
        for row in image:
            s = sum(row) / 255
            if s > end:
                end = s

        crop_start = end - crop_width

    crop = image.copy()

    for i in range(len(crop)):
        crop[i] = crop[i][crop_start:(crop_start + crop_width)]

    cutoff = np.array(crop, dtype=np.uint8)
    return cutoff
