import numpy as np
import cv2


def preprocess_image(img, target_size=(512, 512)):
    if img is None:
        raise ValueError("Image could not be loaded")
    # Convert to grayscale to simplify comparison
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Resize to standard size
    resized = cv2.resize(gray, target_size, interpolation=cv2.INTER_AREA)
    return resized


# Load and preprocess images
base_img = cv2.imread("1747647344775.jpg")
base_img = preprocess_image(base_img)
base = np.fft.fft2(base_img)
base = np.fft.fftshift(base) / base_img.size

comp_img = cv2.imread("1747647346424.jpg")
comp_img = preprocess_image(comp_img)
comp = np.fft.fft2(comp_img)
comp = np.fft.fftshift(comp) / comp_img.size

test_img = cv2.imread("1fae5ba6083a597bd57c5c097fce42e79bd5099f.jpeg")
test_img = preprocess_image(test_img)
test = np.fft.fft2(test_img)
test = np.fft.fftshift(test) / test_img.size


def compare_magnitude_spectra(im1, im2):
    """
    Compare two images in the frequency domain by calculating the Euclidean distance
    between their normalized magnitude spectra.

    Parameters:
    -----------
    im1 : ndarray
        First image's FFT array (should be output of np.fft.fftshift(np.fft.fft2()))
    im2 : ndarray
        Second image's FFT array (should be output of np.fft.fftshift(np.fft.fft2()))

    Returns:
    --------
    float
        Euclidean distance between the normalized magnitude spectra of the two images.
        Smaller values indicate more similar frequency content between the images.
        The value is always non-negative, where 0 indicates identical spectra.

    Notes:
    ------
    The function performs the following steps:
    1. Computes the magnitude spectra of both FFT arrays
    2. Normalizes each spectrum to the range [0,1]
    3. Calculates the Euclidean distance between the normalized spectra
    """
    # Calculate the normalized magnitude spectra
    mag1 = np.abs(im1)
    mag2 = np.abs(im2)

    # Normalize the magnitudes to [0,1] range
    mag1 = (mag1 - mag1.min()) / (mag1.max() - mag1.min())
    mag2 = (mag2 - mag2.min()) / (mag2.max() - mag2.min())

    # Calculate the Euclidean distance between the normalized magnitude spectra
    return np.linalg.norm(mag1 - mag2)


print("Exactly same image:", compare_magnitude_spectra(base, base))

print("Distance between base and comp:", compare_magnitude_spectra(base, comp))
print("Distance between base and test:", compare_magnitude_spectra(base, test))
