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
    remove_white_pixels(images, bar_lines, regions)


def get_clefs(staff_image, regions, bar_lines, min_match=0.75):
    template_filepaths = None
    clefs = []
    for index in range(len(bar_lines) - 1):
        bar_line = bar_lines[index]
        bar_line_height = max([r for r, c in bar_line]) - min([r for r, c in bar_line]) + 1
        closest_region, closest_col, closest_index = find_closest_region(bar_line, regions)
        if closest_region is not None and check_region_location(bar_line, bar_lines[index + 1],
                                                                closest_region, bar_line_height / 4.):
            reg_height, reg_width = get_region_image(staff_image, closest_region).shape[:2]
            if reg_height > bar_line_height / 2.:
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
            if white_region in regions:
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
    closest_index = -1
    for index, region in enumerate(regions):
        if region not in exceptions:
            reg_cols = [c for r, c in region if c > max_ref_reg_col]
            if len(reg_cols) > 0 and len(reg_cols) == len(region):
                min_clef_col = min(reg_cols)
                if min_clef_col < closest_col or closest_col == -1:
                    closest_col = min_clef_col
                    closest_region = region
                    closest_index = index
    return closest_region, closest_col, closest_index


def check_region_location(start_region, end_region, region, staff_spacing, factor=2.5):
    max_start_reg_col = max([c for r, c in start_region])
    min_end_reg_col = max([c for r, c in end_region])
    min_reg_col = min([c for r, c in region])
    distance = min_reg_col - max_start_reg_col
    return (factor == 0 or staff_spacing == 0 or distance <= staff_spacing * factor) and min_reg_col < min_end_reg_col


def get_time_signatures(staff_image, regions, bar_lines, clefs, min_match=0.7, tolerance=0):
    template_filepaths = None
    time_signatures = []
    for index in range(len(bar_lines) - 1):
        bar_line = bar_lines[index]
        bar_line_top = min([r for r, c in bar_line])
        bar_line_bot = max([r for r, c in bar_line])
        bar_line_height = bar_line_bot - bar_line_top + 1
        closest_clef, closest_clef_col, closest_index = find_closest_region(bar_line, clefs)
        if closest_clef is not None and check_region_location(bar_line, bar_lines[index + 1],
                                                              closest_clef, bar_line_height / 4.):
            start_region = closest_clef
        else:
            start_region = bar_line
        closest_region, closest_col, closest_index = find_closest_region(start_region, regions)

        if closest_region is not None and check_region_location(start_region, bar_lines[index + 1],
                                                                closest_region, 0):
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
                    closest_region_right_copy = max([c for r, c in closest_region])
                    closest_region, closest_col, closest_index = \
                        find_closest_region(start_region, regions, [closest_region])
                    if closest_region is not None and \
                            check_region_location(start_region, bar_lines[index + 1],
                                                  closest_region, 0):
                        closest_region_top = min([r for r, c in closest_region])
                        closest_region_bot = max([r for r, c in closest_region])
                        closest_region_left = min([c for r, c in closest_region])
                        closest_region_height = closest_region_bot - closest_region_top + 1
                        if closest_region_left < closest_region_right_copy and \
                                        closest_region_top >= bar_line_top - tolerance and \
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
                        best_matches += [template_match(image,
                                                        template_filepaths=template_filepaths,
                                                        resize=True, print_results=False)]
                    try:
                        top = best_matches[0][0]
                        top = top.split('/')[-1]
                        top = top.split('_')[0]
                        top = int(top)

                        bot = best_matches[1][0]
                        bot = bot.split('/')[-1]
                        bot = bot.split('_')[0]
                        bot = int(bot)
                        success = min_match <= best_matches[0][1] and min_match <= best_matches[1][1]
                    except:
                        success = False

                    if success:
                        time_signatures += [(closest_region, best_matches)]
                    elif full_region_image is not None:
                        best_match = template_match(full_region_image,
                                                    template_filepaths=template_filepaths,
                                                    resize=True, print_results=False)
                        try:
                            sign = best_match[0]
                            sign = sign.split('/')[-1]
                            sign = sign.split('_')[0]
                            sign = int(sign)
                            success = False
                        except:
                            success = min_match <= best_match[1]

                        if success:
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
                        tolerance=None, flag_min_match=0.7, note_head_min_match=0.8,
                        half_note_head_min_match=0.65):
    image = org_image.copy()

    rel_staff = get_rel_staff(staff, staff_distance)

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

    half_note_heads_templates = {}

    for templateName in search_for_templates(["note_heads/half", "note_heads/whole"]):
        template = imp.load_image(templateName)
        template = imp.resize_image(template, (int(round(staff_spacing)), int(round(staff_spacing))))
        template = imp.image_gray(template)
        template = imp.image_bin_otsu(template)
        template = imp.invert(template)
        half_note_heads_templates[templateName] = template

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
                        else:
                            best_match = template_match(sub_region_img,
                                                        template_images=half_note_heads_templates,
                                                        print_results=False)
                            if half_note_head_min_match <= best_match[1]:
                                note_heads += [(sub_region, connected_region, line_index,
                                                ("templates/note_heads/half_01", best_match[1]))]
                    line_index += 0.5

            for note_head, connected_region, line_index, match in note_heads:
                if connected_region in connected_regions:
                    connected_regions.remove(connected_region)

            # recognize note
            print("Recognizing notes' properties...")
            checked_flags = []
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
                        checked_flags += [(flag, flag_match)]

                if flags_and_beams > 0:
                    duration = 1 / 4.
                    for i in range(flags_and_beams):
                        duration /= 2
                else:
                    duration = 1 / 4. if note_head_type == "filled" else 0.5

                notes += [(min([c for r, c in connected_region[0]]), height, note_head_type, duration)]

            for flag in flags:
                if flag not in checked_flags:
                    connected_region = flag[0]
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
                            best_match = template_match(get_region_image(region_image,sub_region),
                                                        template_images=half_note_heads_templates,
                                                        print_results=False)
                            if half_note_head_min_match <= best_match[1]:
                                note_heads += [(sub_region, connected_region, line_index,
                                                ("templates/note_heads/half_01", best_match[1]))]
                                notes += [(min([c for r, c in connected_region[0]]), line_index, "half", 0.5)]
                            imp.display_image(get_region_image(region_image,sub_region))
                        line_index += 0.5

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


def find_duration_dots(image, regions, staff_spacing, tolerance=2):
    dots = []
    dot_templates = {}
    for templateName in search_for_templates("dots"):
        template = imp.load_image(templateName)
        template = imp.resize_image(template, (int(round(staff_spacing / 2)), int(round(staff_spacing / 2))))
        template = imp.image_gray(template)
        template = imp.image_bin_otsu(template)
        template = imp.invert(template)
        dot_templates[templateName] = template

    for region in regions:
        region_image = get_region_image(image, region)
        height, width = region_image.shape[:2]
        if height <= staff_spacing / 2 + tolerance and width <= staff_spacing / 2 + tolerance:
            best_match = template_match(region_image,
                                        template_images=dot_templates,
                                        print_results=False)
            dots += [(region, best_match)]
    return dots


def remove_duration_dots(images, dots, regions):
    return remove_white_pixels(images, [dot[0] for dot in dots], regions)


def remove_ledgers(images, regions, staff, staff_distance, tolerance=1):
    avg_line_thickness = 0
    for line in staff:
        avg_line_thickness += line[-1] - line[0] + 1
    avg_line_thickness *= 1. / len(staff)

    rel_staff = get_rel_staff(staff, staff_distance)

    regions_to_remove = []
    for region in regions:
        region_top = min([r for r, c in region])
        region_bot = max([r for r, c in region])
        region_height = region_bot - region_top + 1
        if avg_line_thickness + tolerance > region_height and \
                (region_bot < rel_staff[0][0] or region_top > rel_staff[-1][-1]):
            regions_to_remove += [region]
    remove_white_pixels(images, regions_to_remove, [regions])


def get_rel_staff(staff, staff_distance):
    rel_staff = []
    for line in staff:
        rel_line = []
        for row in line:
            rel_line += [row - (staff[0][0] - staff_distance // 2)]
        rel_staff += [rel_line]

    return rel_staff


def get_possible_whole_note_regions(regions, bar_lines, clefs, time_signatures, staff_spacing, tolerance=1):
    bar_line_top = min([r for r, c in bar_lines[0]])
    bar_line_bot = max([r for r, c in bar_lines[0]])
    possible_non_whole_note_regions = []
    to_remove = []
    for region in regions:
        region_top = min([r for r, c in region])
        region_bot = max([r for r, c in region])
        region_height = region_bot - region_top + 1
        if region_height < 1.5 * staff_spacing and (region_top > bar_line_bot or region_bot < bar_line_top):
            possible_non_whole_note_regions += [region]

    for bar_line in bar_lines:
        closest_region = None
        diff = tolerance * staff_spacing + 1
        closest_time_signature, closest_col, closest_index = \
            find_closest_region(bar_line, time_signatures)
        if closest_time_signature is None:
            closest_clef, closest_col, closest_index = find_closest_region(bar_line, clefs)
            if closest_clef is None:
                for region in regions:
                    region_left = min([c for r, c in region])
                    region_right = max([c for r, c in region])
                    bar_line_left = min([c for r, c in bar_line])
                    if region_left <= bar_line_left <= region_right:
                        to_remove += [region]
                        break
            else:
                closest_region, closest_col, closest_index = \
                    find_closest_region(closest_clef, possible_non_whole_note_regions)
                diff = closest_col - max([c for r, c in closest_clef])
        else:
            closest_region, closest_col, closest_index = \
                find_closest_region(closest_time_signature, possible_non_whole_note_regions)
            diff = closest_col - max([c for r, c in closest_time_signature])
        if closest_region is not None and diff < tolerance * staff_spacing:
            to_remove += [closest_region]

    ret_regs = []
    for reg in regions:
        if reg not in to_remove:
            ret_regs += [reg]
    return ret_regs


def find_whole_notes(image, regions, bar_lines, clefs, time_signatures,
                     staff, staff_spacing, staff_distance, min_match=0.61):
    note_templates = {}
    for templateName in search_for_templates(["note_heads/whole", "note_heads/double_whole"]):
        template = imp.load_image(templateName)
        template = imp.resize_image(template, (int(round(staff_spacing)), int(round(staff_spacing))))
        template = imp.image_gray(template)
        template = imp.image_bin_otsu(template)
        template = imp.invert(template)
        note_templates[templateName] = template

    rel_staff = get_rel_staff(staff, staff_distance)
    # find note_heads
    print("Finding whole note heads...")
    notes = []
    possible_regions = get_possible_whole_note_regions(regions, bar_lines, clefs, time_signatures, staff_spacing)
    for region in possible_regions:
        reg_top = min([r for r, c in region])
        reg_height, reg_width = get_region_image(image, region).shape[:2]
        if staff_spacing <= reg_width and reg_height >= staff_spacing:
            min_r = rel_staff[0][-1]
            line_index = 0.5
            while abs(min_r - reg_top) >= staff_spacing // 2:
                if min_r > reg_top:
                    min_r -= staff_spacing // 2
                    line_index -= 0.5
                else:
                    min_r += staff_spacing // 2
                    line_index += 0.5
            min_r = int(min_r)

            max_r = max([r for r, c in region])
            for start_r in range(min_r, max_r, int(staff_spacing // 2)):
                sub_region = [value for value in region
                              if start_r + staff_spacing >= value[0] >= start_r]
                if len(sub_region) > 0:
                    sub_region_img = get_region_image(image, sub_region)
                    best_match = template_match(sub_region_img,
                                                template_images=note_templates,
                                                print_results=False)
                    if min_match <= best_match[1]:
                        notes += [(region, line_index, best_match)]
                line_index += 0.5
    return notes


def remove_whole_notes(images, whole_notes, regions):
    remove_white_pixels(images, whole_notes, regions)


def find_rests(image, regions, bar_lines, crotchet_min_match=0.68, min_match=0.7):
    rests = []
    crotchet_templates = search_for_templates("rests/4")
    all_templates = search_for_templates("rests")
    bar_line_top = min([r for r, c in bar_lines[0]])
    bar_line_bot = max([r for r, c in bar_lines[0]])
    for region in regions:
        reg_top = min([r for r, c in region])
        reg_bot = max([r for r, c in region])
        if reg_top > bar_line_top and reg_bot < bar_line_bot:
            region_image = get_region_image(image, region)
            best_match = template_match(region_image,
                                        template_filepaths=crotchet_templates,
                                        resize=True,
                                        print_results=False)
            if best_match[1] < crotchet_min_match:
                best_match = template_match(region_image,
                                            template_filepaths=all_templates,
                                            resize=True,
                                            print_results=False)
                if best_match[1] >= min_match:
                    rests += [(region, best_match)]
            else:
                rests += [(region, best_match)]
    return rests


def remove_rests(images, white_pixels, regions):
    remove_white_pixels(images, white_pixels, regions)


def export_data(index, bar_lines, clefs, time_signatures, endings, notes,
                accidentals, dots, whole_notes, rests, staff, staff_spacing, staff_distance):
    rel_staff = get_rel_staff(staff, staff_distance)
    print("Analysis results of staff %s" % (index + 1))
    for index, bar_line in enumerate(bar_lines):
        print("Bar Line %s" % (index + 1))
        if index + 1 < len(bar_lines):
            bar_line_left = min([c for r, c in bar_line])
            next_bar_line_left = min([c for r, c in bar_lines[index + 1]])
            closest_region, closest_col, closest_index = find_closest_region(bar_line, [clef[0] for clef in clefs])
            if next_bar_line_left > closest_col > bar_line_left:
                clef = clefs[closest_index]
                clef = clef[1]
                clef = clef[0]
                clef = clef.split('/')[-1]
                clef = clef.split('_')[0]

                if clef == "g":
                    print("G-Clef")
                elif clef == "f":
                    print("F-Clef")
                elif clef == "c":
                    print("C-Clef")
                else:
                    print("Unknown clef!")

            closest_region, closest_col, closest_index = \
                find_closest_region(bar_line, [time_signature[0] for time_signature in time_signatures])
            if next_bar_line_left > closest_col > bar_line_left:
                time_signature = time_signatures[closest_index]
                time_signature = time_signature[1]
                if type(time_signature) is list:
                    top = time_signature[0][0]
                    top = top.split('/')[-1]
                    top = top.split('_')[0]
                    bot = time_signature[1][0]
                    bot = bot.split('/')[-1]
                    bot = bot.split('_')[0]
                    print("Time: %s/%s" % (top, bot))
                else:
                    time_signature = time_signature[0]
                    time_signature = time_signature.split('/')[-1]
                    time_signature = time_signature.split('_')[0]
                    print("Time: %s" % time_signature)

            closest_region, closest_col, closest_index = \
                find_closest_region(bar_line, [ending[0] for ending in endings])
            if next_bar_line_left > closest_col > bar_line_left:
                print("Ending")

            sorted_notes = get_sorted_bar_objects(notes, bar_line_left, next_bar_line_left)
            sorted_whole_notes = get_sorted_bar_objects(whole_notes, bar_line_left, next_bar_line_left)
            sorted_dots = get_sorted_bar_objects(dots, bar_line_left, next_bar_line_left)
            sorted_rests = get_sorted_bar_objects(rests, bar_line_left, next_bar_line_left)
            sorted_accidentals = get_sorted_bar_objects(accidentals, bar_line_left, next_bar_line_left)

            key_accidentals = []
            for accidental in sorted_accidentals:
                col = accidental[0]
                if (len(sorted_notes) == 0 or col < sorted_notes[0][0]) and \
                        (len(sorted_whole_notes) == 0 or col < sorted_whole_notes[0][0]) and \
                        (len(sorted_rests) == 0 or col < sorted_rests[0][0]):

                    if len(sorted_notes) > 0:
                        distance_to_note = sorted_notes[0][0] - col
                    else:
                        distance_to_note = staff_spacing + 1

                    if len(sorted_whole_notes) > 0:
                        distance_to_whole_note = sorted_whole_notes[0][0] - col
                    else:
                        distance_to_whole_note = staff_spacing + 1

                    if min([distance_to_note, distance_to_whole_note]) > staff_spacing:
                        key_accidentals += [accidental]

            if len(key_accidentals) > 0:
                print("Key Accidentals:")
                for accidental in key_accidentals:
                    sorted_accidentals.remove(accidental)
                    acc = accidental[1][1][0]
                    acc = acc.split('/')[-1]
                    acc = ' '.join(acc.split('_')[:-1])
                    print("\t %s" % acc)

            concat_notes = []
            for note in sorted_whole_notes:
                concat_notes += [(note[0], note, 0)]
            for note in sorted_notes:
                concat_notes += [(note[0], note, 1)]
            concat_notes = sorted(concat_notes)
            if len(concat_notes) > 0:
                print("Notes:")
            for note in concat_notes:
                note_type = note[2]
                if note_type == 0:
                    print("\twhole note")
                    print("\t\tcolumn: %s" % note[0])
                    print("\t\theight: %s" % (note[1][1][1]))
                    print("\t\tduration: %s" % 1)
                    min_note_c = note[0]
                    max_note_c = max([c for r, c in note[1][1][0]])
                    note_rows = [r for r, c in note[1][1][0]]
                    prolonged = False
                    for dot in sorted_dots:
                        if staff_spacing * 1.5 > dot[0] - max_note_c > 0:
                            for r, c in dot[1][0]:
                                if r in note_rows:
                                    sorted_dots.remove(dot)
                                    prolonged = True
                                    print("\t\tprolonged duration")
                                    break
                            if prolonged:
                                break
                    for accidental in sorted_accidentals:
                        max_accidental_c = max([c for r, c in accidental[1][0]])
                        if 0 < min_note_c - max_accidental_c < staff_spacing * 2:
                            for r, c in accidental[1][0]:
                                if r in note_rows:
                                    acc = accidental[1][1][0]
                                    acc = acc.split('/')[-1]
                                    acc = ' '.join(acc.split('_')[:-1])
                                    print("\t\taccidental: %s" % acc)
                                    sorted_accidentals.remove(accidental)

                else:
                    subnotes = note[1][1][2]
                    region = note[1][1][0]
                    region_min_r = min([r for r, c in region])
                    region_max_r = max([r for r, c in region])
                    for subnote in subnotes:
                        print("\tstem note")
                        note_col = note[0] + subnote[0]
                        print("\t\tcolumn: %s" % note_col)
                        print("\t\theight: %s" % subnote[1])
                        print("\t\tduration: %s" % subnote[3])
                        for dot in sorted_dots:
                            dot_min_r = min([r for r, c in dot[1][0]])
                            if staff_spacing * 2.5 > dot[0] - note_col > 0 \
                                    and region_min_r < dot_min_r < region_max_r:
                                dot_height = dot_min_r - rel_staff[0][0]
                                dot_height /= staff_spacing
                                if abs(dot_height - subnote[1]) < 1:
                                    sorted_dots.remove(dot)
                                    print("\t\tprolonged duration")
                                    break

                        for accidental in sorted_accidentals:
                            max_accidental_c = max([c for r, c in accidental[1][0]])
                            min_accidental_r = min([r for r, c in accidental[1][0]])
                            center_accidental_r =\
                                (max([r for r, c in accidental[1][0]]) - min_accidental_r) / 2 + min_accidental_r
                            if 0 < note_col - max_accidental_c < staff_spacing * 2 and \
                                    region_min_r < center_accidental_r < region_max_r:
                                acc_height = center_accidental_r - rel_staff[0][0]
                                acc_height /= staff_spacing
                                if abs(acc_height - subnote[1]) <= 0.5:
                                    acc = accidental[1][1][0]
                                    acc = acc.split('/')[-1]
                                    acc = ' '.join(acc.split('_')[:-1])
                                    print("\t\taccidental: %s" % acc)
                                    sorted_accidentals.remove(accidental)
            if len(sorted_rests) > 0:
                print("Rests:")
            for rest in sorted_rests:
                print("\trest")
                rest_type = rest[1][1][0]
                rest_type = rest_type.split('/')[-1]
                rest_type = rest_type.split('_')[0]
                rest_type = int(rest_type)
                rest_type = 1. / rest_type
                if rest_type == 0.5:
                    rest_reg = rest[1][0]
                    min_rest_r = min([r for r, c in rest_reg])
                    if min_rest_r in rel_staff[1]:
                        rest_type = 1
                print("\t\tcolumn: %s" % rest[0])
                print("\t\tduration: %s" % rest_type)
                for dot in sorted_dots:
                    if staff_spacing * 2 > dot[0] - rest[0] > 0:
                        sorted_dots.remove(dot)
                        print("\t\tprolonged duration")
                        break
            repeat_begin = []
            repeat_end = []
            for dot in sorted_dots:
                if dot[0] - bar_line_left < 2 * staff_spacing:
                    repeat_begin += [dot]
                elif next_bar_line_left - dot[0] < 2 * staff_spacing:
                    repeat_end += [dot]

            if len(repeat_begin) == 2:
                print("Repeat Begin")
            if len(repeat_end) == 2:
                print("Repeat End")

                # repeat dots


def get_sorted_bar_objects(objects, min_c, max_c):
    sorted_objects = []
    for obj in objects:
        bar_obj_cols = [c for r, c in obj[0] if max_c > c > min_c]
        if len(bar_obj_cols) > 0:
            obj_left = min(bar_obj_cols)
            sorted_objects += [(obj_left, obj)]
    sorted_objects = sorted(sorted_objects)
    return sorted_objects
