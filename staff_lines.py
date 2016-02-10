from image_operations import project_image, crop_image, open_image


def find_lines(image):
    """Recognize staff lines on image and return them
    as a list of lists of lists of row numbers,
    distances between them and average staff spacing.
    :param image: """
    first = get_white_rows(crop_image(project_image(image)))
    second = get_white_rows(open_image(image))

    lines, line_distances, staff_distances =\
        group_rows(intersect_lists(first, second))
    avg_staff_spacing = []
    for staff_line_distances in line_distances:
        avg_staff_spacing += staff_line_distances
    avg_staff_spacing = sum(avg_staff_spacing) * 1. / len(avg_staff_spacing)
    avg_staff_distance = sum(staff_distances) * 1. / len(staff_distances)
    return lines, line_distances, avg_staff_spacing, staff_distances, avg_staff_distance


def get_white_rows(image):
    """Find row numbers of white pixels in an image
    :param image:
    """
    rows = []
    height, width = image.shape[:2]
    for row in range(height):
        for col in range(width):
            if (image[row][col] == 255) and (row not in rows):
                rows.append(row)
    return sorted(rows)


def intersect_lists(first, second):
    """Intersect two lists
    :param first:
    :param second:
    """
    ret_val = []
    for val in first:
        if val in second:
            ret_val += [val]
    return ret_val


def group_rows(rows):
    """Group white rows by staves and staff lines
    :param rows:
    """

    # Contains list of staves,
    # that contain list of lines,
    # that contains list of white rows' numbers
    labels = [[[]]]

    line_distances = [[]]
    staff_distances = []
    prev_row = None
    for row in rows:
        if prev_row is not None:
            if row - prev_row > 1:
                if len(labels[-1]) < 5:
                    # Add another line to the last staff
                    # and add the distance between new line
                    # and previous line
                    labels[-1].append([])
                    line_distances[-1] += [row - prev_row]
                else:
                    # Add another staff and add list
                    # of line distances for that staff
                    labels.append([])
                    line_distances.append([])
                    staff_distances += [row - prev_row]

        labels[-1][-1] += [row]
        prev_row = row
    return labels, line_distances, staff_distances


def remove_lines(org_image,
                 lines=None,
                 top_bot_pixel_removal=True,
                 top_bot_pixel_diff=2,
                 thickness_based_removal=True,
                 thickness_tolerance=0):
    """Return an image that represents a copy of the original without the
    staff lines
    :param org_image:
    :param lines:
    :param top_bot_pixel_removal:
    :param top_bot_pixel_diff:
    :param thickness_based_removal:
    :param thickness_tolerance: """

    image = org_image.copy()

    if lines is None:
        lines = find_lines(org_image)[0]

    image_height, image_width = image.shape[:2]

    if top_bot_pixel_removal:
        for staff in lines:
            for line in staff:
                top = line[0]
                bot = line[-1]
                for j in range(image_width):
                    remove = True
                    is_line = False
                    for row in image[top:bot + 1]:
                        if row[j] == 255:
                            is_line = True
                            break
                    if not is_line:
                        continue
                    # check top_bot_pixel_diff pixels above and below
                    for row in image[top - top_bot_pixel_diff: top]:
                        if row[j] == 255:
                            remove = False
                            break
                    if remove:
                        for row in image[bot + 1: bot + top_bot_pixel_diff + 1]:
                            if row[j] == 255:
                                remove = False
                                break
                        if remove:
                            for row in image[top:bot + 1]:
                                row[j] = 0

    if thickness_based_removal:

        avg_thickness = []
        for staff in lines:
            for line in staff:
                avg_thickness += [len(line)]
        avg_thickness = sum(avg_thickness) * 1. / len(avg_thickness)

        for j in range(image_width):
            checking_line = False
            for i in range(len(image)):
                if image[i][j] == 255:
                    if not checking_line:
                        start = i
                    checking_line = True
                else:
                    if checking_line:
                        thickness = i - start
                        if thickness <= (avg_thickness + thickness_tolerance):
                            for row in image[start: i]:
                                row[j] = 0
                    checking_line = False
    return image
