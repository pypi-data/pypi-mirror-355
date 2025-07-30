from tinyml4all.tabular.features.PowerTransform import PowerTransform


class YeoJohnson(PowerTransform):
    """
    Yeo-Johnson power transformation.
    See https://en.wikipedia.org/wiki/Power_transform
    """

    def method(self) -> str:
        """

        :return:
        """
        return "yeo-johnson"
