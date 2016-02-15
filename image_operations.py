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
        kernel = np.ones((1, 20))
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
    return projected_image


def crop_image(image, crop_start=None, crop_width=None):
    """Return a cropped image
    :param image:
    :param crop_start:
    :param crop_width:
    """

    if crop_start is None:
        end = 0
        for row in image:
            s = sum(row) / 255
            if s > end:
                end = s

        if crop_width is None:
            crop_width = end // 3

        crop_start = end - crop_width

    if crop_width is None:
        crop_width = len(image[0]) // 10

    crop = image[:]

    for i in range(len(crop)):
        crop[i] = crop[i][crop_start:(crop_start + crop_width)]

    crop = np.array(crop, dtype=np.uint8)
    return crop


def open_image_vertically(image, staff_spacing, multiply_factor=1.5):
    """Morphological opening of image with vertical line kernel
    :param image:
    :param staff_spacing:
    :param multiply_factor:
    """
    return open_image(image, np.ones((int(round(multiply_factor * staff_spacing)), 1)))


def image_subtract(image1, image2):
    """Return image that contains only white pixels from
    the first image, but not from the second image
    :param image2:
    :param image1:
    """
    ret_image = image1.copy()
    image_height, image_width = ret_image.shape[:2]
    for row in range(image_height):
        for col in range(image_width):
            if image2[row, col] == 255:
                ret_image[row, col] = 0


def merge_images(images):
    """Merge the images and return them as one
    :param images:
    """
    ret_image = images[0].copy()
    for image in images:
        for row in range(len(image)):
            for col in range(len(image[0])):
                if image[row][col] == 255:
                    ret_image[row][col] = 255
    return ret_image
