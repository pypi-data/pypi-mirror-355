from tensorflow.keras.applications import (
    vgg16,
    vgg19,
    resnet,
    resnet_v2,
    inception_v3,
    xception,
    mobilenet,
    mobilenet_v2,
    mobilenet_v3,
    densenet,
    nasnet,
    efficientnet,
    convnext,
)
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.vgg19 import VGG19
from tensorflow.keras.applications.resnet import ResNet50
from tensorflow.keras.applications.resnet_v2 import ResNet50V2
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.applications.xception import Xception
from tensorflow.keras.applications.mobilenet import MobileNet
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
from tensorflow.keras.applications.densenet import DenseNet121
from tensorflow.keras.applications.nasnet import NASNetMobile, NASNetLarge
from tensorflow.keras.applications.efficientnet import (
    EfficientNetB0,
)
from tensorflow.keras.applications.convnext import (
    ConvNeXtTiny,
    ConvNeXtSmall,
    ConvNeXtBase,
    ConvNeXtLarge,
)

LIB_FOR_MODEL_NAME_DICT = {
    "VGG16": "vgg16",
    "VGG19": "vgg19",
    "ResNet50": "resnet",
    "ResNet50V2": "resnet_v2",
    "InceptionV3": "inception_v3",
    "Xception": "xception",
    "MobileNet": "mobilenet",
    "MobileNetV2": "mobilenet_v2",
    "DenseNet121": "densenet",
    "NASNetMobile": "nasnet",
    "NASNetLarge": "nasnet",
    "EfficientNetB0": "efficientnet",
    "ConvNeXtTiny": "convnext",
    "ConvNeXtSmall": "convnext",
    "ConvNeXtBase": "convnext",
    "ConvNeXtLarge": "convnext",
}


def get_lib_name(model_name):
    lib_name = LIB_FOR_MODEL_NAME_DICT[model_name]
    return globals()[lib_name]


def get_class_name(model_name):
    return globals()[model_name]
