import template_matching as tm
import image_region_recognition as irr
import image_operations as imo


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


def get_clefs(staff_image, regions, bar_lines, min_match=0.75):
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


def remove_white_pixels(images, white_regions, regions_list):
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


def find_notes(image, regions, staff, staff_spacing):

    for region in regions:
        region_image = irr.get_region_image(image, region)
        # find vertical lines
        # find beams by searching for regions between vertical lines
        # find note heads by splitting the original image into each line
        #   and searching between min and max column of the region
