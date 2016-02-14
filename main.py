import image_processing as imp
import image_operations as imo
import staff_lines as sl
import image_region_recognition as irr
import music_classification as mc


def load_image(image_name):
    print("Loading image: %s" % image_name)
    return imp.load_image(image_name)


def image_gray(image):
    print("Grayscaling image...")
    return imp.image_gray(image)


def image_bin_adaptive_gauss(image, block_size):
    print("Binarizing image (Adaptive Gaussian Binarization)...")
    return imp.image_bin_adaptive_gauss(image, block_size)


def invert(image):
    print("Inverting image...")
    return imp.invert(image)


def display_image(image):
    return imp.display_image(image)


def open_image(image, kernel=None):
    return imo.open_image(image, kernel)


def open_image_vertically(staff_image, avg_staff_spacing):
    print("Opening staff image with vertical kernel...")
    return imo.open_image_vertically(staff_image, avg_staff_spacing)


def find_lines(inv_img):
    print("Finding staff lines...")
    return sl.find_lines(inv_img)


def remove_lines(inv_img, lines):
    print("Removing staff lines...")
    return sl.remove_lines(inv_img, lines)


def find_regions(img_vert_lines):
    return irr.find_regions(img_vert_lines)


def find_vertical_regions(staff_image, img_vert_lines, avg_staff_spacing, pixel_span=1):
    print("Finding vertical regions...")
    return irr.find_vertical_regions(staff_image, img_vert_lines, avg_staff_spacing, pixel_span=pixel_span)


def get_bar_lines(regions, vertical_lines, staff):
    print("Classifying bar lines...")
    return mc.get_bar_lines(regions, vertical_lines, staff)


def remove_bar_lines(images, bar_lines, regions):
    print("Removing bar lines from staff images and regions...")
    return mc.remove_bar_lines(images, bar_lines, regions)


def get_clefs(image, regions, bar_lines):
    print("Classifying clefs...")
    return mc.get_clefs(image, regions, bar_lines)


def remove_clefs(images, clefs, regions):
    if len(clefs) > 0:
        print("Removing clefs from staff images and regions...")
        return mc.remove_clefs(images, clefs, regions)


def get_time_signatures(staff_image, regions, bar_lines, clefs):
    print("Classyfing time signatures...")
    return mc.get_time_signatures(staff_image, regions, bar_lines, clefs)


def remove_time_signatures(images, time_signatures, regions):
    if len(time_signatures) > 0:
        print("Removing time signatures...")
        return mc.remove_time_signatures(images, time_signatures, regions)


def get_endings(staff_image, regions, top_staff_line_row):
    print("Classyfing endings...")
    return mc.get_endings(staff_image, regions, top_staff_line_row)


def remove_endings(images, endings, regions):
    if len(endings) > 0:
        print("Removing time signatures...")
        return mc.remove_endings(images, endings, regions)


def find_notes(image, regions, staff, staff_spacing):
    return mc.find_notes(image, regions, staff, staff_spacing)


def analyze_staff(img_wo_lines, staff, index, avg_staff_spacing, avg_staff_distance):
    print("Analyzing staff %s" % (index + 1))
    staff_image_top = staff[0][0] - avg_staff_distance//2
    staff_image_bot = staff[-1][-1] + avg_staff_distance//2
    staff_image = img_wo_lines[staff_image_top: staff_image_bot]
    img_vert_lines = open_image_vertically(staff_image, avg_staff_spacing)
    print("Saving vertical lines...")
    vertical_lines = find_regions(img_vert_lines)[1]
    img_vert_objects, vertical_regions = \
        find_vertical_regions(staff_image, img_vert_lines,
                              avg_staff_spacing, pixel_span=2)
    bar_lines = get_bar_lines(vertical_regions, vertical_lines, staff)
    remove_bar_lines([staff_image, img_vert_objects, img_vert_lines],
                     bar_lines, vertical_regions)
    clefs = get_clefs(staff_image, vertical_regions, bar_lines)
    remove_clefs([staff_image, img_vert_objects, img_vert_lines], clefs, vertical_regions)
    time_signatures = get_time_signatures(staff_image, vertical_regions, bar_lines,
                                          [clef[0] for clef in clefs])
    remove_time_signatures([staff_image, img_vert_objects, img_vert_lines],
                           time_signatures, vertical_regions)
    endings = get_endings(staff_image, vertical_regions, staff[0][0])
    remove_endings([staff_image, img_vert_objects, img_vert_lines],
                   endings, vertical_regions)
    find_notes(img_vert_objects, vertical_regions, staff, avg_staff_spacing)


def perform_recognition(image_name):
    org_image = load_image(image_name)
    img_gray = image_gray(org_image)
    img_otsu = image_bin_adaptive_gauss(img_gray, 7)
    inv_img = invert(img_otsu)
    lines, line_distances, avg_staff_spacing,\
        staff_distances, avg_staff_distance = find_lines(inv_img)
    img_wo_lines = remove_lines(inv_img, lines)
    for index, staff in enumerate(lines):
        analyze_staff(img_wo_lines, staff, index, avg_staff_spacing, avg_staff_distance)

perform_recognition("test2.png")