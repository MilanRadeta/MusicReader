from os import listdir

from image_processing import *


def search_for_templates(template_filepaths):
    """Search for template images in templates folder
    that are in specified folders and optionally
    start with specified prefix
    :param template_filepaths:
    """

    templates = []
    if template_filepaths == str:
        filenames = [template_filepaths]
    else:
        filenames = template_filepaths

    for filename in filenames:
        split = filename.split('/')
        for listedFile in listdir("templates"):
            if listedFile == split[0]:
                for innerFile in listdir("templates/%s" % listedFile):
                    if len(split) == 1 or innerFile.startswith(split[1]):
                        templates += ["templates/%s/%s" % (listedFile, innerFile)]
        return templates


def template_match(obj,
                   template_filepaths=None,
                   template_images=None,
                   resize=False,
                   print_results=True):
    """Return best match from templates for image
    containing the object (region).
    :param obj:
    :param template_filepaths:
    :param template_images:
    :param resize:
    :param print_results:
    """
    obj_height, obj_width = obj.shape[:2]
    best_match = (None, 0)
    templates = {}
    if template_filepaths is None and template_images is None:
        raise Exception("Missing template filepaths or template images")
    elif template_filepaths is not None and template_images is not None:
        raise Exception("Template filepaths and images mutual exclusion",
                        "Can use only template filepaths or template images.")
    elif template_filepaths is not None:
        templates = make_template_images(template_filepaths,
                                         size=None if not resize
                                         else (int(round(obj_width)),
                                               int(round(obj_height))))
    elif template_images is not None:
        if type(template_images) != dict:
            raise Exception("Template images must be a dictionary, with"
                            "filepaths for keys and images for values!")
        templates = template_images

    for templateName, template in templates.items():
        template_height, template_width = template.shape[:2]
        for row in range(obj_height - template_height + 1):
            for col in range(obj_width - template_width + 1):
                match = 0
                for r in range(template_height):
                    for c in range(template_width):
                        match += 1\
                            if obj[row + r][col + c] == template[r][c]\
                            else 0
                match *= 1. / (template_height * template_width)

                if match > best_match[1]:
                    best_match = (templateName, match)

    if print_results:
        if best_match[0] is None:
            print("NO MATCH!")
        else:
            print("best match: %d%%" % (best_match[1] * 100))
            print("templateName: %s" % best_match[0])
    return best_match


def make_template_images(template_filepaths, size=None):
    """Make dictionary of images from template_filepaths.
    :param template_filepaths:
    :param size:
    """
    templates = {}
    for filepath in template_filepaths:
        template = load_image(filepath)
        if size is not None:
            template = resize_image(template, size)
        template = image_gray(template)
        template = image_bin_otsu(template)
        template = invert(template)
        templates[filepath] = template
    return templates
