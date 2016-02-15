import template_matching as tm
import image_region_recognition as irr
import image_operations as imo
import image_processing as imp


def open_image(image, kernel=None):
    return imo.open_image(image, kernel)


def merge_images(images):
    return imo.merge_images(images)


def find_regions(org_image, ref_image=None, pixel_span=2, eight_way=True):
    return irr.find_regions(org_image, ref_image, pixel_span, eight_way=eight_way)


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
                                        resize=True, print_results=False)
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


def find_closest_region(ref_region, regions, exceptions=None):
    if exceptions is None:
        exceptions = []
    max_ref_reg_col = max([c for r, c in ref_region])
    closest_region = None
    closest_col = -1
    for region in regions:
        if region not in exceptions:
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
                full_region_image = None
                if bar_line_height + tolerance > closest_region_height > bar_line_height / 2 + tolerance \
                        or (closest_region_top < bar_line_top + bar_line_height // 2 < closest_region_bot):
                    # Time signature's top and bottom numbers are recognized as one region, they need to be split
                    region_image = get_region_image(staff_image, closest_region)
                    full_region_image = region_image
                    region_images = [region_image[:bar_line_height / 2], region_image[bar_line_height / 2:]]
                else:
                    # Time signature's top and bottom numbers are separate regions, get another one
                    closest_region_copy = closest_region[:]
                    closest_region_top_copy = closest_region_top
                    closest_region, closest_col = find_closest_region(start_region, regions, [closest_region])
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
                                                       resize=True, print_results=False)
                    if min_match <= best_matches[0] and min_match <= best_matches[1]:
                        time_signatures += [(closest_region, best_matches)]
                    elif full_region_image is not None:
                        best_match = template_match(full_region_image,
                                                    template_filepaths=template_filepaths,
                                                    resize=True, print_results=False)
                        if min_match <= best_match:
                            time_signatures += [(closest_region, best_match)]
    return time_signatures


def remove_time_signatures(images, time_signatures, regions):
    remove_white_pixels(images, [time_signature[0] for time_signature in time_signatures], [regions])


def get_endings(staff_image, regions, top_staff_line_row, min_match=0.9):
    template_filepaths = None
    endings = []
    for region in regions:
        region_bot_row = max([r for r, c in region])
        if region_bot_row < top_staff_line_row:
            if template_filepaths is None:
                template_filepaths = search_for_templates("endings")
                best_match = template_match(get_region_image(staff_image, region),
                                            template_filepaths=template_filepaths,
                                            resize=True, print_results=False)
                if best_match >= min_match:
                    endings += [(region, best_match)]
    return endings


def remove_endings(images, endings, regions):
    remove_white_pixels(images, [ending[0] for ending in endings], [regions])


def find_avg_thickness(vertical_lines):
    avg_vert_line_thickness = 0
    if len(vertical_lines) > 0:
        for line in vertical_lines:
            avg_vert_line_thickness += max([c for r, c in line]) - min([c for r, c in line]) + 1
        avg_vert_line_thickness *= 1. / len(vertical_lines)
    return avg_vert_line_thickness


def find_vertical_notes(org_image, regions, staff, staff_spacing, staff_distance,
                        tolerance=None, flag_min_match=0.8, note_head_min_match=0.8):
    image = org_image.copy()

    rel_staff = []
    for line in staff:
        rel_line = []
        for row in line:
            rel_line += [row - (staff[0][0] - staff_distance // 2)]
        rel_staff += [rel_line]

    recognized_notes = []
    unrecognized_regions = []
    small_regions = []

    note_heads_templates = {}
    for templateName in search_for_templates(["note_heads/filled"]):
        template = imp.load_image(templateName)
        template = imp.resize_image(template, (int(round(staff_spacing)), int(round(staff_spacing))))
        template = imp.image_gray(template)
        template = imp.image_bin_otsu(template)
        template = imp.invert(template)
        note_heads_templates[templateName] = template

    for index, region in enumerate(regions):
        org_reg_c = min([c for r, c in region])
        org_reg_r = min([r for r, c in region])
        region_image = irr.get_region_image(image, region)
        if len(region_image) > 3 * staff_spacing:
            img_vert_lines = imo.open_image_vertically(region_image, staff_spacing, 3)
            vertical_lines = find_regions(img_vert_lines)[1]
            remove_white_pixels([region_image], vertical_lines)

            avg_vert_line_thickness = find_avg_thickness(vertical_lines)

            if tolerance is None:
                tolerance = avg_vert_line_thickness

            # Find beams by searching for regions between vertical lines
            print("Finding full beams...")
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
                elif len(lines) > 0:
                    connected_regions += [(sub_region,
                                           lines[0])]
                else:
                    separate_regions += [sub_region]

            # Find half beams
            print("Finding half beams...")
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
                        except ValueError:
                            continue
                        distance = None
                        if min_row > max_beam_row:
                            distance = min_row - max_beam_row
                        elif max_row < min_beam_row:
                            distance = min_beam_row - max_row
                        if distance is not None and distance < staff_spacing:
                            half_beams += [sub_region]

            for half_beam in half_beams:
                connected_regions.remove(half_beam)

            # find flags
            print("Finding flags...")
            flags = []
            flag_templates = search_for_templates("flags")
            for sub_region in connected_regions:
                best_match = template_match(get_region_image(region_image, sub_region[0]),
                                            template_filepaths=flag_templates,
                                            resize=True, print_results=False)
                if flag_min_match <= best_match[1]:
                    flags += [(sub_region, best_match)]

            for flag, match in flags:
                connected_regions.remove(flag)

            # find note_heads
            print("Finding note heads...")
            note_heads = []
            for connected_region in connected_regions:
                min_r = rel_staff[0][-1]
                line_index = 0.5
                while abs(min_r - org_reg_r) >= staff_spacing // 2:
                    if min_r > org_reg_r:
                        min_r -= staff_spacing // 2
                        line_index -= 0.5
                    else:
                        min_r += staff_spacing // 2
                        line_index += 0.5
                min_r -= org_reg_r
                min_r = int(min_r)

                max_r = max([r for r, c in connected_region[0]])
                for start_r in range(min_r, max_r, int(staff_spacing // 2)):
                    sub_region = [value for value in connected_region[0]
                                  if start_r + staff_spacing >= value[0] >= start_r]
                    if len(sub_region) > 0:
                        sub_region_img = get_region_image(region_image, sub_region)
                        best_match = template_match(sub_region_img,
                                                    template_images=note_heads_templates,
                                                    print_results=False)
                        if note_head_min_match <= best_match[1]:
                            note_heads += [(sub_region, connected_region, line_index, best_match)]
                        elif len(sub_region_img) >= staff_spacing:
                            # possible half note
                            note_heads += [(sub_region, connected_region, line_index,
                                            ("templates/note_heads/half_01", 0.8))]
                    line_index += 0.5

            for note_head, connected_region, line_index, match in note_heads:
                if connected_region in connected_regions:
                    connected_regions.remove(connected_region)

            # recognize note
            print("Recognizing notes' properties...")
            notes = []
            for note_head, connected_region, line_index, match in note_heads:
                height = line_index
                note_head_type = match[0].split('/')[-1].split('_')[0]
                flags_and_beams = 0
                line = connected_region[1]

                for beam in full_beams:
                    if line in beam[3]:
                        flags_and_beams += 1
                for half_beam in half_beams:
                    if line == half_beam[1]:
                        flags_and_beams += 1
                for flag, flag_match in flags:
                    if line == flag[1]:
                        flags_and_beams += int(flag_match[0].split('/')[-1].split('_')[0]) / 8

                if flags_and_beams > 0:
                    duration = 1 / 4.
                    for i in range(flags_and_beams):
                        duration /= 2
                else:
                    duration = 1 / 4. if note_head_type == "filled" else 0.5

                notes += [(min([c for r, c in connected_region[0]]), height, note_head_type, duration)]

            notes = sorted(notes)

            recognized_notes += [(region, org_reg_c, notes)]
            unrecognized_regions += [(region, connected_regions, separate_regions)]

            if False:
                # Remove flags and beams from original image
                to_remove = []
                to_remove_from_region_image = []

                for flag, match in flags:
                    for r, c in flag[0]:
                        to_remove += [(r + org_reg_r, c + org_reg_c)]
                        to_remove_from_region_image += [(r, c)]
                for half_beam in half_beams:
                    for r, c in half_beam[0]:
                        to_remove += [(r + org_reg_r, c + org_reg_c)]
                        to_remove_from_region_image += [(r, c)]
                for beam in full_beams:
                    for r, c in beam[0]:
                        to_remove += [(r + org_reg_r, c + org_reg_c)]
                        to_remove_from_region_image += [(r, c)]
                for note_head, connected_region, line_index, match in note_heads:
                    for r, c in note_head:
                        to_remove += [(r + org_reg_r, c + org_reg_c)]
                        to_remove_from_region_image += [(r, c)]
                for line in vertical_lines:
                    for r, c in line:
                        to_remove += [(r + org_reg_r, c + org_reg_c)]
                        to_remove_from_region_image += [(r, c)]

                remove_white_pixels([image], [to_remove])
                remove_white_pixels([region_image], [to_remove_from_region_image])
        else:
            small_regions += [region]
            # remove_white_pixels([image], [region])
    recognized_notes.sort(key=lambda x: x[1])
    return recognized_notes


def remove_vertical_notes(images, notes, regions):
    regions_to_delete = [note[0] for note in notes]
    remove_white_pixels(images, regions_to_delete, [regions])


def find_accidentals(org_image, regions, min_match=0.7):
    accidentals = []
    template_filepaths = search_for_templates(["accidentals"])
    for region in regions:
        region_image = irr.get_region_image(org_image, region)
        best_match = template_match(region_image,
                                    template_filepaths=template_filepaths,
                                    resize=True, print_results=False)
        if min_match <= best_match[1]:
            accidentals += [(region, best_match)]
    return accidentals


def remove_accidentals(images, accidentals, regions):
    return remove_white_pixels(images, [accidental[0] for accidental in accidentals], regions)