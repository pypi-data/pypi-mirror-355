from tensorflow.keras import layers
from tensorflow import keras
import tensorflow as tf
from tensorflow.keras.layers import LSTM, GRU
import keras_cv
from Mylib import tf_create_image_pretrained_model


class ImageDataAugmentation(layers.Layer):
    """Tăng cường dữ liệu hình ảnh ở khía cạnh vị trí, bao gồm các lớp sau (**trong tf.keras.layers**)
    - RandomFlip
    - RandomRotation
    - RandomZoom

    Attributes:
        rotation_factor (float): Tham số cho lớp RandomRotation. Default to 0.2
        zoom_factor (float): Tham số cho lớp RandomZoom. Default to 0.2
    """

    def __init__(self, rotation_factor=0.2, zoom_factor=0.2, **kwargs):
        # super(ImageDataPositionAugmentation, self).__init__()
        super().__init__(**kwargs)
        self.rotation_factor = rotation_factor
        self.zoom_factor = zoom_factor

    def build(self, input_shape):
        self.RandomFlip = layers.RandomFlip(mode="horizontal_and_vertical")
        self.RandomRotation = layers.RandomRotation(factor=self.rotation_factor)
        self.RandomZoom = layers.RandomZoom(height_factor=self.zoom_factor)

        super().build(input_shape)

    def call(self, x):
        x = self.RandomFlip(x)
        x = self.RandomRotation(x)
        x = self.RandomZoom(x)

        return x

    def get_config(self):
        # Trả về cấu hình của lớp tùy chỉnh
        config = super().get_config()
        config.update(
            {
                "rotation_factor": self.rotation_factor,
                "zoom_factor": self.zoom_factor,
            }
        )
        return config

    @classmethod
    def from_config(cls, config):
        # Giải mã lại lớp từ cấu hình
        return cls(**config)


class KerascvImageDataAugmentation(layers.Layer):
    def __init__(
        self,
        rotation_factor,
        zoom_factor,
        bright_factor,
        blur_kernel_size,
        blur_factor,
        saturation_factor,
        contrast_factor,
        contrast_value_range,
        hue_factor,
        hue_value_range,
        centercrop_size,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.rotation_factor = rotation_factor
        self.zoom_factor = zoom_factor
        self.bright_factor = bright_factor
        self.blur_kernel_size = blur_kernel_size
        self.blur_factor = blur_factor
        self.saturation_factor = saturation_factor
        self.contrast_factor = contrast_factor
        self.contrast_value_range = contrast_value_range
        self.hue_factor = hue_factor
        self.hue_value_range = (hue_value_range,)
        self.centercrop_size = centercrop_size

    def build(self, input_shape):
        self.RandomFlip = keras_cv.layers.RandomFlip(mode="horizontal_and_vertical")
        self.RandomRotation = keras_cv.layers.RandomRotation(
            factor=self.rotation_factor
        )
        self.RandomZoom = keras_cv.layers.RandomZoom(height_factor=self.zoom_factor)
        self.RandomBrightness = keras_cv.layers.RandomBrightness(
            factor=self.bright_factor
        )
        self.RandomGaussianBlur = keras_cv.layers.RandomGaussianBlur(
            kernel_size=self.blur_kernel_size, factor=self.blur_factor
        )
        self.RandomSaturation = keras_cv.layers.RandomSaturation(
            factor=self.saturation_factor,
        )
        self.RandomContrast = keras_cv.layers.RandomContrast(
            factor=self.contrast_factor, value_range=self.contrast_value_range
        )
        self.RandomHue = keras_cv.layers.RandomHue(
            factor=self.hue_factor, value_range=self.hue_value_range
        )
        self.CenterCrop = keras_cv.layers.CenterCrop(
            height=self.centercrop_size, width=self.centercrop_size
        )

        super().build(input_shape)

    def call(self, x):
        # Xử lí x
        x = self.RandomFlip(x)
        x = self.RandomRotation(x)
        x = self.RandomZoom(x)
        x = self.RandomBrightness(x)
        x = self.RandomGaussianBlur(x)
        x = self.RandomSaturation(x)
        x = self.RandomContrast(x)
        x = self.RandomHue(x)
        x = self.CenterCrop(x)

        return x

    def get_config(self):
        # Trả về cấu hình của lớp tùy chỉnh
        config = super().get_config()
        config.update(
            {
                "rotation_factor": self.rotation_factor,
                "zoom_factor": self.zoom_factor,
                "bright_factor": self.bright_factor,
                "blur_kernel_size": self.blur_kernel_size,
                "blur_factor": self.blur_factor,
                "saturation_factor": self.saturation_factor,
                "contrast_factor": self.contrast_factor,
                "contrast_value_range": self.contrast_value_range,
                "hue_factor": self.hue_factor,
                "hue_value_range": self.hue_value_range,
            }
        )
        return config

    @classmethod
    def from_config(cls, config):
        # Giải mã lại lớp từ cấu hình
        return cls(**config)


class ImagePretrainedModel(layers.Layer):
    """Sử dụng các pretrained models ở trong **keras.applications**
    Danh sách các pretrained models: vgg16, vgg19,

    Attributes:
        model_name (str): Tên pretrained model, vd: vgg16, vgg19, ....
        num_trainable (int, optional): Số lượng các lớp đầu tiên cho trainable = True. Defaults to 0.
    """

    def __init__(self, model_name, num_trainable=0, **kwargs):
        if num_trainable < 0:
            raise ValueError(
                "=========ERROR: Tham số <num_trainable> trong class PretrainedModel phải >= 0   ============="
            )

        # super(ConvNetBlock, self).__init__()
        super().__init__(**kwargs)
        self.model_name = model_name
        self.num_trainable = num_trainable

    def get_config(self):
        # Trả về cấu hình của lớp tùy chỉnh
        config = super().get_config()
        config.update(
            {
                "model_name": self.model_name,
                "num_trainable": self.num_trainable,
            }
        )
        return config

    def build(self, input_shape):
        pretrained_model_lib = tf_create_image_pretrained_model.get_lib_name(
            self.model_name
        )
        ClassName = tf_create_image_pretrained_model.get_class_name(self.model_name)
        self.conv_layer = ClassName(weights="imagenet", include_top=False)
        self.preprocess_input = pretrained_model_lib.preprocess_input

        # Cập nhật trạng thái trainable cho các lớp đầu
        self.conv_layer.trainable = False
        if self.num_trainable > 0:
            self.set_layers_trainable()

        super().build(input_shape)

    def set_layers_trainable(self):
        for layer in self.conv_layer.layers[-self.num_trainable :]:
            layer.trainable = True

    def call(self, x):
        x = self.preprocess_input(x)
        x = self.conv_layer(x)

        return x

    @classmethod
    def from_config(cls, config):
        # Giải mã lại lớp từ cấu hình
        return cls(**config)
