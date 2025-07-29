from skimage.io import imread, imsave


def read_image(path, is_gray=False):
    img = imread(path, as_gray=is_gray)
    return img


def save_image(img, path):
    imsave(path, img)
