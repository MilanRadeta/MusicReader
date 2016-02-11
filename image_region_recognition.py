import numpy as np
import image_operations as imo


def add_region(image, row, col, regions, pixel_span=2):
    """Search image for region containing white pixels
    at designated row and col and add it to found regions.
    If during the search white pixels that are already
    in one of previously recognized regions are found,
    all the newly found pixels will be added to that region.
    :param image:
    :param row:
    :param col:
    :param regions:
    :param pixel_span:
    """
    image_height, image_width = image.shape[:2]
    found_region = None
    if image[row, col] == 0:
        raise Exception("Image has a black pixel"
                        "at row %s and col %s!" % (row, col))

    coordinates = [(row, col)]
    idx = 0
    while idx < len(coordinates):
        row, col = coordinates[idx]
        for dr in range(-pixel_span, pixel_span + 1):
            for dc in range(-pixel_span, pixel_span + 1):
                r = row + dr
                c = col + dc
                if 0 <= r < image_height and 0 <= c < image_width:
                    if image[r][c] == 255 and ((r, c) not in coordinates):
                        if found_region is None:
                            # If a region that contains one of the coordinates
                            # hasn't been found, check all the regions now
                            # for current coordinate
                            found_region =\
                                find_region_with_coordinate(regions, (r, c))

                            if found_region is not None:
                                # Found coordinate in one of other regions
                                # Add all coordinates to the region if it
                                # doesn't contain them
                                for coordinate in coordinates:
                                    if coordinate not in found_region:
                                        found_region += [coordinate]
                            if found_region is None:
                                coordinates += [(r, c)]
                        else:
                            if (r, c) not in found_region:
                                found_region += [(r, c)]
                                coordinates += [(r, c)]
        idx += 1
    if found_region is None:
        regions.append(coordinates)


def find_regions(org_image, ref_image=None, pixel_span=2):
    """Find and return regions from org_image,
    according to ref_image. If there's no ref_image, org_image
    will be it.
    :param org_image:
    :param ref_image:
    :param pixel_span:
    """
    if ref_image is None:
        ref_image = org_image
    else:
        ref_image = np.uint8(np.array(ref_image))

    image_height, image_width = ref_image.shape[:2]
    # Label regions of interest
    regions = []
    for row in range(image_height):
        for col in range(image_width):
            if ref_image[row][col] == 255:
                if find_region_with_coordinate(regions, (row, col)) is None:
                    add_region(org_image, row, col, regions, pixel_span)

    img_regions = org_image.copy()
    for row in range(len(img_regions)):
        for col in range(len(img_regions[row])):
            img_regions[row][col] = 0

    for region in regions:
        for row, col in region:
            img_regions[row, col] = 255

    return img_regions, regions


def find_region_with_coordinate(regions, coordinate):
    """In found regions find the region that contains the given
    coordinate.
    :param regions:
    :param coordinate:
    """
    for region in regions:
        if coordinate in region:
            return region
    return None


def find_vertical_regions(image, image_vertical_lines=None,
                          staff_spacing=None, pixel_span=2):
    """Return regions from image that contain vertical lines
    :param image:
    :param image_vertical_lines:
    :param staff_spacing:
    :param pixel_span:
    """
    if image_vertical_lines is None:
        image_vertical_lines = imo.open_image_vertically(
            image, staff_spacing)
    return find_regions(image, image_vertical_lines, pixel_span=pixel_span)


def split_image_by_regions(image, regions):
    """Split image to sub images that contain only the regions.
    :param image:
    :param regions:
    """
    split_images = []
    for region in regions:
        split_images.append(get_region_image(image, region))
    return split_images


def get_region_image(image, region):
    """Get image containing only the specified region
    :param image:
    :param region:
    """
    min_row = min([r for r, c in region])
    max_row = max([r for r, c in region])
    min_col = min([c for r, c in region])
    max_col = max([c for r, c in region])
    sub_image = []
    for row in range(min_row, max_row + 1):
        sub_image.append([])
        for col in range(min_col, max_col + 1):
            sub_image[-1] += [image[row][col]]
    sub_image = np.array(sub_image)
    sub_image = np.uint8(sub_image)
    return sub_image
