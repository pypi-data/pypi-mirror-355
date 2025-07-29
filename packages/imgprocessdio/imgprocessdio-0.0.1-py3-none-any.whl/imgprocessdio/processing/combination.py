import numpy as np
from skimage.color import rgb2gray
from skimage.exposure import match_histograms
from skimage.metrics import structural_similarity


def find_difference(img1, img2):
    assert img1.shape == img2.shape, "Especifique 2 imagens com o mesmo formato."
    gray_img1 = rgb2gray(img1)
    gray_img2 = rgb2gray(img2)
    (score, difference_img) = structural_similarity(gray_img1, gray_img2, full=True)
    print("semelhancas das imagens:  ", score)
    normalized_difference_img = (difference_img - np.min(difference_img)) / (
        np.max(difference_img) - np.min(difference_img)
    )
    return normalized_difference_img


def transfer_histogram(img1, img2):
    matched_img = match_histograms(img1, img2, multichannel=True)
    return matched_img
