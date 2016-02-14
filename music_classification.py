import template_matching as tm
import image_region_recognition as irr
import image_operations as imo
import image_processing as imp


def open_image(image, kernel=None):
    return imo.open_image(image, kernel)


def merge_images(images):
    return imo.merge_images(images)


def find_regions(org_image, ref_image=None, pixel_span=2):
    return irr.find_regions(org_image, ref_image, pixel_span)


def search_for_templates(template_filepaths):
    return tm.search_for_templates(template_filepaths)


def template_match(obj,
                   template_filepaths=None,
                   template_images=None,
                   resize=False,
                   print_results=True):
    return tm.template_match(obj,
                             template_filepaths=template_filepaths,
                             template_images=template_images,
                             resize=resize,
                             print_results=print_results)


def get_region_image(image, region):
    return irr.get_region_image(image, region)


def get_bar_lines(regions, vertical_lines, staff):
    bar_lines = []
    for region in regions:
        if region in vertical_lines:
            min_row = min([r for r, c in region])
            max_row = max([r for r, c in region])
            height = max_row - min_row
            staff_height = staff[-1][-1] - staff[0][0]
            if height == staff_height:
                bar_lines += [region]
    return bar_lines


def remove_bar_lines(images, bar_lines, regions):
    remove_white_pixels(images, bar_lines, [regions])


def get_clefs(staff_image, regions, bar_lines, min_match=0.78):
    template_filepaths = None
    clefs = []
    for index in range(len(bar_lines) - 1):
        bar_line = bar_lines[index]
        closest_region, closest_col = find_closest_region(bar_line, regions)
        if closest_region is not None and check_region_location(bar_line, bar_lines[index + 1], closest_region):
            if template_filepaths is None:
                template_filepaths = search_for_templates("clefs")
            best_match = template_match(get_region_image(staff_image, closest_region),
                                        template_filepaths=template_filepaths,
                                        resize=True, print_results=True)
            if min_match <= best_match[1]:
                clefs += [(closest_region, best_match)]
    return clefs


def remove_clefs(images, clefs, regions):
    remove_white_pixels(images, [clef[0] for clef in clefs], [regions])


def remove_white_pixels(images=None, white_regions=None, regions_list=None):
    if regions_list is None:
        regions_list = []
    if images is None:
        images = []
    if white_regions is None:
        white_regions = []
    for white_region in white_regions:
        for regions in regions_list:
            regions.remove(white_region)
        for img in images:
            for r, c in white_region:
                img[r][c] = 0


def find_closest_region(ref_region, regions):
    max_ref_reg_col = max([c for r, c in ref_region])
    closest_region = None
    closest_col = -1
    for region in regions:
        reg_cols = [c for r, c in region if c > max_ref_reg_col]
        if len(reg_cols) > 0:
            min_clef_col = min(reg_cols)
            if min_clef_col < closest_col or closest_col == -1:
                closest_col = min_clef_col
                closest_region = region
    return closest_region, closest_col


def check_region_location(start_region, end_region, region):
    max_start_reg_col = max([c for r, c in start_region])
    min_end_reg_col = min([c for r, c in end_region])
    reg_width = min_end_reg_col - max_start_reg_col
    min_end_reg_col = min([c for r, c in region])
    distance = min_end_reg_col - max_start_reg_col
    return distance < (reg_width / 3.)


def get_time_signatures(staff_image, regions, bar_lines, clefs, min_match=0.75, tolerance=2):
    template_filepaths = None
    time_signatures = []
    for index in range(len(bar_lines) - 1):
        bar_line = bar_lines[index]
        bar_line_top = min([r for r, c in bar_line])
        bar_line_bot = max([r for r, c in bar_line])
        bar_line_height = bar_line_bot - bar_line_top + 1
        closest_clef, closest_clef_col = find_closest_region(bar_line, clefs)
        if closest_clef is not None and check_region_location(bar_line, bar_lines[index + 1], closest_clef):
            start_region = closest_clef
        else:
            start_region = bar_line
        closest_region, closest_col = find_closest_region(start_region, regions)
        if closest_region is not None and check_region_location(start_region, bar_lines[index + 1], closest_region):
            closest_region_top = min([r for r, c in closest_region])
            closest_region_bot = max([r for r, c in closest_region])
            closest_region_height = closest_region_bot - closest_region_top + 1
            if closest_region_top >= bar_line_top - tolerance and closest_region_bot <= bar_line_bot + tolerance:
                region_images = []
                if bar_line_height + tolerance > closest_region_height > bar_line_height / 2 + tolerance:
                    # Time signature's top and bottom numbers are recognized as one region, they need to be split
                    region_image = get_region_image(staff_image, closest_region)
                    region_images = [region_image[:bar_line_height / 2], region_image[bar_line_height / 2:]]
                else:
                    # Time signature's top and bottom numbers are separate regions, get another one
                    closest_region_copy = closest_region[:]
                    closest_region_top_copy = closest_region_top
                    img_copy = staff_image.copy()
                    regions_copy = regions[:]
                    remove_white_pixels([img_copy], [closest_region], [regions_copy])
                    closest_region, closest_col = find_closest_region(start_region, regions_copy)
                    if closest_region is not None and \
                            check_region_location(start_region, bar_lines[index + 1], closest_region):
                        closest_region_top = min([r for r, c in closest_region])
                        closest_region_bot = max([r for r, c in closest_region])
                        closest_region_height = closest_region_bot - closest_region_top + 1
                        if closest_region_top >= bar_line_top - tolerance and \
                                        closest_region_bot <= bar_line_bot + tolerance:
                            if bar_line_height + tolerance > closest_region_height > bar_line_height / 2 + tolerance:
                                raise Exception("Second time signature number is bigger than half staff height")
                            if closest_region_top_copy < closest_region_top:
                                region_images = [
                                    get_region_image(staff_image, closest_region_copy),
                                    get_region_image(staff_image, closest_region)
                                ]
                            else:
                                region_images = [
                                    get_region_image(staff_image, closest_region),
                                    get_region_image(staff_image, closest_region_copy)
                                ]
                            closest_region += closest_region_copy
                    else:
                        raise Exception("Time signature numbers are separate regions, but found only one of them")

                if len(region_images) == 2:
                    if template_filepaths is None:
                        template_filepaths = search_for_templates("time")
                    best_matches = []
                    for image in region_images:
                        best_matches += template_match(image,
                                                       template_filepaths=template_filepaths,
                                                       resize=True, print_results=True)
                    if min_match <= best_matches[0] and min_match <= best_matches[1]:
                        time_signatures += [(closest_region, best_matches)]
    return time_signatures


def remove_time_signatures(images, time_signatures, regions):
    remove_white_pixels(images, [time_signature[0] for time_signature in time_signatures], [regions])


def get_endings(staff_image, regions, top_staff_line_row, min_match=0.85):
    template_filepaths = None
    endings = []
    for region in regions:
        region_bot_row = max([r for r, c in region])
        if region_bot_row < top_staff_line_row:
            if template_filepaths is None:
                template_filepaths = search_for_templates("endings")
                best_match = template_match(get_region_image(staff_image, region),
                                            template_filepaths=template_filepaths,
                                            resize=True, print_results=True)
                if best_match >= min_match:
                    endings += [(region, best_match)]
    return endings


def remove_endings(images, endings, regions):
    remove_white_pixels(images, [ending[0] for ending in endings], [regions])


def find_notes(image, regions, staff, staff_spacing, tolerance=None, thickness_tolerance=2):
    for region in regions:
        region_image = irr.get_region_image(image, region)
        if len(region_image) > 2.5 * staff_spacing:
            img_vert_lines = imo.open_image_vertically(region_image, staff_spacing, 3)
            vertical_lines = find_regions(img_vert_lines)[1]
            remove_white_pixels([region_image], vertical_lines)

            first_line = None
            last_line = None
            avg_vert_line_thickness = 0
            for line in vertical_lines:
                if first_line is None or min([c for r, c in line]) < min([c for r, c in first_line]):
                    first_line = line
                if last_line is None or max([c for r, c in line]) > max([c for r, c in last_line]):
                    last_line = line
                avg_vert_line_thickness += max([c for r, c in line]) - min([c for r, c in line]) + 1
            avg_vert_line_thickness *= 1. / len(vertical_lines)
            if tolerance is None:
                tolerance = avg_vert_line_thickness

            # find beams by searching for regions between vertical lines
            full_beams = []
            connected_regions = []
            separate_regions = []
            sub_regions = find_regions(region_image)[1]
            for sub_region in sub_regions:
                start_vert_line = None
                end_vert_line = None
                lines = []
                min_col = min([c for r, c in sub_region])
                max_col = max([c for r, c in sub_region])
                for line in vertical_lines:
                    min_line_col = min([c for r, c in line])
                    max_line_col = max([c for r, c in line])
                    if -tolerance <= min_col - max_line_col <= tolerance:
                        start_vert_line = line
                        lines += [line]
                    elif -tolerance <= min_line_col - max_col <= tolerance:
                        end_vert_line = line
                        lines += [line]
                    elif min_col < min_line_col < max_col:
                        lines += [line]
                if start_vert_line is not None and end_vert_line is not None:
                    full_beams += [(sub_region, start_vert_line, end_vert_line, lines)]
                elif start_vert_line is not None or end_vert_line is not None:
                    connected_regions += [(sub_region,
                                           start_vert_line
                                           if start_vert_line is not None else end_vert_line)]
                else:
                    separate_regions += [sub_region]

            # Find half beams
            half_beams = []
            for sub_region in connected_regions:
                max_row = max([r for r, c in sub_region[0]])
                min_row = min([r for r, c in sub_region[0]])
                min_col = min([c for r, c in sub_region[0]])
                max_col = max([c for r, c in sub_region[0]])
                for beam in full_beams:
                    if sub_region[1] in beam[3]:
                        try:
                            min_beam_row = min([r for r, c in beam[0] if min_col <= c <= max_col])
                            max_beam_row = max([r for r, c in beam[0] if min_col <= c <= max_col])
                            distance = None
                            if min_row > max_beam_row:
                                distance = min_row - max_beam_row
                            elif max_row < min_beam_row:
                                distance = min_beam_row - max_row
                            if distance is not None and distance < staff_spacing:
                                half_beams += [sub_region]
                        except:
                            pass

            for half_beam in half_beams:
                connected_regions.remove(half_beam)

            # imp.display_image(region_image)
            # find flags

            # remove flags and beams from original image

            # find note heads by splitting the original image into each line
            #   and searching between min and max column of the region
