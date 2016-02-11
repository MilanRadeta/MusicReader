import template_matching as tm
import image_region_recognition as irr


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


def remove_bar_lines(images, bar_lines, regions, vertical_lines):
    for bar_line in bar_lines:
        regions.remove(bar_line)
        vertical_lines.remove(bar_line)
        for img in images:
            for r, c in bar_line:
                img[r][c] = 0


def get_clefs(image, regions, bar_lines, min_match=0.75):
    template_filepaths = None
    clefs = []
    for index in range(len(bar_lines) - 1):
        bar_line = bar_lines[index]
        max_bar_line_col = max([c for r, c in bar_line])
        closest_region = None
        closest_col = len(image[0])
        for region in regions:
            region_cols = [c for r, c in region if c > max_bar_line_col]
            if len(region_cols) > 0:
                min_region_col = min(region_cols)
                if min_region_col < closest_col:
                    closest_col = min_region_col
                    closest_region = region
        if closest_region is not None:
            next_bar_line = bar_lines[index + 1]
            next_bar_line_min_col = min([c for r, c in next_bar_line])
            bar_width = next_bar_line_min_col - max_bar_line_col
            closest_col_distance = closest_col - max_bar_line_col
            if closest_col_distance < (bar_width / 3.):
                if template_filepaths is None:
                    template_filepaths = search_for_templates("clefs")
                best_match = template_match(get_region_image(image, closest_region), template_filepaths=template_filepaths,
                               resize=True,print_results=True)
                if min_match <= best_match[1]:
                    clefs += [(closest_region, best_match)]
    return clefs


def remove_clefs(images, clefs, regions):
    for clef in clefs:
        regions.remove(clef[0])
        for img in images:
            for r, c in clef[0]:
                img[r][c] = 0
