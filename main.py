import image_processing as imp
import image_operations as imo
import staff_lines as sl
import image_region_recognition as irr

image_name = "test.png"
print("Loading image: %s" % image_name)
org_image = imp.load_image(image_name)
print("Grayscaling image...")
img_gray = imp.image_gray(org_image)
print("Binarizing image...")
img_otsu = imp.image_bin_adaptive_gauss(img_gray, 7)
print("Inverting image...")
inv_img = imp.invert(img_otsu)
print("Finding staff lines...")
lines, line_distances, avg_staff_spacing,\
    staff_distances, avg_staff_distance = sl.find_lines(inv_img)
print("Removing staff lines...")
img_wo_lines = sl.remove_lines(inv_img, lines)
for index, staff in enumerate(lines):
    print("Analyzing staff %s" % (index + 1))
    staff_image_top = staff[0][0] - avg_staff_distance//2
    staff_image_bot = staff[-1][-1] + avg_staff_distance//2
    staff_image = img_wo_lines[staff_image_top: staff_image_bot]
    print("Morphologically opening image with vertical kernel...")
    img_vert_lines = imo.open_image_vertically(staff_image, avg_staff_spacing)
    imp.display_image(img_vert_lines)
    print("Saving vertical lines...")
    vertical_lines = irr.find_regions(img_vert_lines)[1]
    print("Finding vertical regions...")
    img_vert_objects, regions = \
        irr.find_vertical_regions(staff_image, img_vert_lines, avg_staff_spacing)
    print("Classifying bar lines...")
    for region in regions:
        if region in vertical_lines:
            min_row = min([r for r, c in region])
            max_row = max([r for r, c in region])
            height = max_row - min_row
            staff_height = staff[-1][-1] - staff[0][0]
            if height == staff_height:
                print("Bar Line")
            else:
                print("Not Bar Line")
    imp.display_image(img_vert_objects)

