import numpy as np
from os import listdir

# Intersect two lists
def intersect_lists(first, second):
    ret_val = []
    for val in first:
        if val in second:
            ret_val += [val]
    return ret_val


# Line finding, labeling and removing functions

# Find Y coordinates of white pixels
def find_y(image):
    y = []
    for i in range(len(image)):
        for j in range(len(image[i])):
            if (image[i][j] == 255) and (i not in y):
                y.append(i)
    return sorted(y)


# Group points and get distances
def label_y(y_list):
    labels = [[]]
    line_distances = []
    prev_y = None
    for y in y_list:
        if prev_y is not None:
            if y - prev_y > 1:
                labels.append([])
                line_distances += [y - prev_y]
        labels[-1] += [y]
        prev_y = y
    return labels, line_distances


# Find lines
def find_lines(image):
    first = find_y(crop_image(horizontal_projection(image)))
    second = find_y(open_image(image))

    lines, distances = label_y(intersect_lists(first, second))
    staff_spacings = [distances[i] for i in range(len(distances)) if (i + 1) % 5 != 0]
    staff_spacing = sum(staff_spacings) * 1. / len(staff_spacings)
    return lines, distances, staff_spacing


# Remove lines
def remove_lines(org_image, tolerance=0, lines=None, topBotPixelRemoval=True, widthBasedRemoval=True):
    image = org_image.copy()

    if lines == None:
        lines, distances, staff_spacing = find_lines(org_image)

    if topBotPixelRemoval:
        for line in lines:
            top = line[0]
            bot = line[-1]
            for j in range(len(image[top])):
                remove = True
                is_line = False
                for row in image[top:bot + 1]:
                    if row[j] == 255:
                        is_line = True
                        break
                if not is_line:
                    continue
                # check 2 pixels above and below
                diff = 2
                for row in image[top - diff: top]:
                    if row[j] == 255:
                        remove = False
                        break
                if remove:
                    for row in image[bot + 1: bot + diff + 1]:
                        if row[j] == 255:
                            remove = False
                            break
                if remove:
                    for row in image[top:bot + 1]:
                        row[j] = 0

    if widthBasedRemoval:
        avg_thickness = lines[:]
        for i, line in enumerate(avg_thickness):
            avg_thickness[i] = len(line)
        avg_thickness = sum(avg_thickness) * 1. / len(avg_thickness)

        for j in range(len(image[0])):
            white = False
            for i in range(len(image)):
                if image[i][j] == 255:
                    if not white:
                        start = i
                    white = True
                else:
                    if white:
                        thickness = i - start
                        if thickness <= (avg_thickness + tolerance):
                            for row in image[start: i]:
                                row[j] = 0
                    white = False
    return image


# Region functions

# Search image for region containing pixel at row and col
# if it's a white pixel and add it to found regions
def add_region(image, row, col, regions, diff=1):
    append = True
    coords = [(row, col)]
    idx = 0
    while (idx < len(coords)):
        row, col = coords[idx]
        for dr in range(-diff, diff + 1):
            for dc in range(-diff, diff + 1):
                r = row + dr
                c = col + dc
                if r >= 0 and c >= 0 and r < len(image) and c < len(image[r]):
                    if image[r][c] == 255 and ((r, c) not in coords):
                        skip = False
                        for region in regions:
                            if (r, c) in region:
                                skip = True
                                append = False
                                for coord in coords:
                                    region.append((r, c))
                        if not skip:
                            coords += [(r, c)]
        idx += 1
    if append:
        regions.append(coords)


# Morphological opening of image with vertical line kernel
def find_vertical_lines(image, staff_spacing=None):
    if staff_spacing is None:
        # Find lines, distances
        lines, distances, staff_spacing = find_lines(image)

    # Find vertical objects
    img_open = open_image(remove_lines(image), np.ones((1.5 * staff_spacing, 1)))
    return img_open


# Find and return regions from org_image, according to ref_image
def find_regions(org_image, ref_image=None, diff=1):
    if ref_image is None:
        ref_image = org_image
    # Label regions of interest
    regions = []
    for row in range(len(ref_image)):
        for col in range(len(ref_image[row])):
            if ref_image[row][col] == 255:
                isFound = False
                for region in regions:
                    if (row, col) in region:
                        isFound = True
                        break
                if not isFound:
                    add_region(org_image, row, col, regions, diff)

    img_regions = org_image.copy()
    for row in range(len(img_regions)):
        for col in range(len(img_regions[row])):
            img_regions[row][col] = 0

    for region in regions:
        for row, col in region:
            img_regions[row, col] = 255

    return img_regions, regions


def find_vertical_objects(image, image_vert_lines=None, staff_spacing=None, diff=1):
    if image_vert_lines is None:
        image_vert_lines = find_vertical_lines(image, staff_spacing)
    return find_regions(image, image_vert_lines, diff=diff)


# Additional image manipulation functions

# Split image to sub images that contain only the regions
def split_image(image, regions):
    split_images = []
    for region in regions:
        minr = min([r for r, c in region])
        maxr = max([r for r, c in region])
        minc = min([c for r, c in region])
        maxc = max([c for r, c in region])
        sub_image = []
        for row in range(minr, maxr + 1):
            sub_image.append([])
            for col in range(minc, maxc + 1):
                sub_image[-1] += [image[row][col]]
        sub_image = np.array(sub_image)
        sub_image = np.uint8(sub_image)
        split_images.append(sub_image)
    return split_images


# Remove white pixels from image1 if image2 contains them
def image_subtract(image1, image2):
    ret_image = image1.copy()
    for row in range(len(ret_image)):
        for col in range(len(ret_image[row])):
            if image2[row, col] == 255:
                ret_image[row, col] = 0


# Template matching functions

def search_for_templates(vertFile):
    templates = []
    split = vertFile.split('/')
    for listedFile in listdir("templates"):
        if listedFile == split[0]:
            for innerFile in listdir("templates/%s" % listedFile):
                if len(split) == 1 or innerFile.startswith(split[1]):
                    templates += ["templates/%s/%s" % (listedFile, innerFile)]
    return templates


# Return best match from templates for image containing the object
def match_object_with_size(obj, templates):
    obj_height, obj_width = obj.shape[:2]
    best_match = (None, 0)
    for template in templates:
        template_name = template
        # Template Image Processing
        template = load_image(template)
        template = resize_image(template, obj_width, obj_height)
        template = image_gray(template)
        template = image_bin_otsu(template)
        template = invert(template)
        match = 0
        for row in range(len(template)):
            for col in range(len(template[row])):
                match += 1 if obj[row][col] == template[row][col] else 0

        # Normalize
        match *= 1. / (obj_width * obj_height)
        if match > best_match[1]:
            best_match = (template_name, match)
    print("Best match: %d%%" % (best_match[1] * 100))
    print("Template name: %s" % best_match[0])
    return best_match


# General template matching
def match_object(obj, templates):
    object_height, object_width = obj.shape[:2]
    best_match = (None, (0, 0), 0)
    for templateName, template in templates.items():
        match_matrix = []
        for row in range(object_height - len(template) + 1):
            match_matrix.append([])
            for col in range(object_width - len(template[0]) + 1):
                match = 0
                for r in range(len(template)):
                    for c in range(len(template[r])):
                        match += 1 if obj[row + r][col + c] == template[r][c] else 0
                match *= 1. / (len(template) * len(template[0]))

                match_matrix[-1] += [match]
                if match > best_match[2]:
                    best_match = (templateName, (row, col), match)

    if best_match[0] is None:
        print("NO MATCH!")
    else:
        print("best match: %d%%" % (best_match[2] * 100))
        print("templateName: %s" % best_match[0])
        print("rows: %s - %s" % (best_match[1][0], best_match[1][0] + len(templates[best_match[0]])))
        print("cols: %s - %s" % (best_match[1][1], best_match[1][1] + len(templates[best_match[0]][0])))
    return best_match
