import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def convert_an_image_to_numpy_array(img_path):
    """Đọc từ đường dẫn ảnh và convert thành mảng numpy

    Args:
        img_path (_type_): đường dẫn đến ảnh
    """
    img = cv2.imread(img_path)
    img = cv2.cvtColor(
        img, cv2.COLOR_BGR2RGB
    )  # Vì cv2 đọc ảnh theo BGR (ngược với RGB)
    return img


def show_img(img_path):
    """Show ảnh lên

    Args:
        img_path (str): đường dẫn đến file
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)
    img = mpimg.imread(img_path)
    ax.imshow(img)
    ax.axis("off")
