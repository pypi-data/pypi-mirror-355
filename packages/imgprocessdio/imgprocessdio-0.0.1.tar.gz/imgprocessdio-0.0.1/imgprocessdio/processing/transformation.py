from skimage.transform import resize


def resize_image(img, proportion):
    assert 0 <= proportion <= 1, "Specify a valid proportion between 0 and 1."
    height = round(img.shape[0] * proportion)
    width = round(img.shape[1] * proportion)
    img_resized = resize(img, (height, width), anti_aliasing=True)
    return img_resized
