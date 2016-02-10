import cv2
import matplotlib.pyplot as plt


def load_image(path):
    """Loads image from path as RGB image
    :param path:
    """
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)


def image_gray(image):
    """Converts RGB image to grayscale image
    :param image:
    """
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def image_bin(image_gs, threshold=127):
    """Global image binarization
    :param threshold:
    :param image_gs:
    """
    ret, image = cv2.threshold(image_gs, threshold, 255, cv2.THRESH_BINARY)
    return image


def image_bin_otsu(image_gs):
    """Otsu binarization
    :param image_gs:
    """
    ret, image = cv2.threshold(image_gs, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return image


def image_bin_adaptive(image_gs, block_size=51):
    """Adaptive binarization
    :param block_size:
    :param image_gs:
    """
    image = cv2.adaptiveThreshold(image_gs, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, 2)
    return image


def image_bin_adaptive_gauss(image_gs, block_size=51):
    """Adaptive Gaussian binarization
    :param image_gs:
    :param block_size:
    """
    image = cv2.adaptiveThreshold(image_gs, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 2)
    return image


def blur(image):
    """Gaussian Blur of an image
    :param image:
    """
    return cv2.GaussianBlur(image, (5, 5), 0)


def invert(image):
    """Image inversion
    :param image:
    """
    return 255-image


def display_image(image, color=False):
    """Display image as plot figure
    :param color:
    :param image:
    """
    plt.figure()
    if color:
        plt.imshow(image)
    else:
        plt.imshow(image, 'gray')
    plt.show()


def resize_image(image, size):
    """Resize image to desired size
    :param image:
    :param size:
    """
    return cv2.resize(image, size, interpolation=cv2.INTER_CUBIC)
