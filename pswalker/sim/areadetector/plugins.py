"""
Overrides for ophyd and pcdsdevices plugins to be used in simulated detectors.
"""
from ophyd.areadetector import plugins
from ophyd.device import Component
import numpy as np

from .base import ad_group
from ..signal import FakeSignal
from ..component import DynamicDeviceComponent

class PluginBase(plugins.PluginBase):
    """
    PluginBase but with components initialized to be empty signals.
    """
    array_counter = Component(FakeSignal, value=0)
    array_rate = Component(FakeSignal, value=0)
    asyn_io = Component(FakeSignal, value=0)
    nd_attributes_file = Component(FakeSignal, value=0)
    pool_alloc_buffers = Component(FakeSignal, value=0)
    pool_free_buffers = Component(FakeSignal, value=0)
    pool_max_buffers = Component(FakeSignal, value=0)
    pool_max_mem = Component(FakeSignal, value=0)
    pool_used_buffers = Component(FakeSignal, value=0)
    pool_used_mem = Component(FakeSignal, value=0)
    port_name = Component(FakeSignal, value=0)
    width = Component(FakeSignal, value=0)
    height = Component(FakeSignal, value=0)
    depth = Component(FakeSignal, value=0)
    array_size = DynamicDeviceComponent(ad_group(
        FakeSignal, (('height'), ('width'), ('depth')), value=0), 
                                        doc='The array size')
    bayer_pattern = Component(FakeSignal, value=0)
    blocking_callbacks = Component(FakeSignal, value=0)
    color_mode = Component(FakeSignal, value=0)
    data_type = Component(FakeSignal, value=0)
    dim0_sa = Component(FakeSignal, value=0)
    dim1_sa = Component(FakeSignal, value=0)
    dim2_sa = Component(FakeSignal, value=0)
    dim_sa = DynamicDeviceComponent(ad_group(
        FakeSignal, (('dim0'), ('dim1'), ('dim2')), value=0),
                                    doc='Dimension sub-arrays')
    dimensions = Component(FakeSignal, value=0)
    dropped_arrays = Component(FakeSignal, value=0)
    enable = Component(FakeSignal, value=0)
    min_callback_time = Component(FakeSignal, value=0)
    nd_array_address = Component(FakeSignal, value=0)
    nd_array_port = Component(FakeSignal, value='CAM')
    ndimensions = Component(FakeSignal, value=0)
    plugin_type = Component(FakeSignal, value="TEST", use_string=True)
    queue_free = Component(FakeSignal, value=0)
    queue_free_low = Component(FakeSignal, value=0)
    queue_size = Component(FakeSignal, value=0)
    queue_use = Component(FakeSignal, value=0)
    queue_use_high = Component(FakeSignal, value=0)
    queue_use_hihi = Component(FakeSignal, value=0)
    time_stamp = Component(FakeSignal, value=0)
    unique_id = Component(FakeSignal, value=0)


class StatsPlugin(plugins.StatsPlugin, PluginBase):
    """
    StatsPlugin but with components instantiated to be empty signals.

    To override centroid values, patch methods:

        _get_readback_centroid_x - Centroid x
        _get_readback_centroid_y - Centroid y

    This will guarantee that returned centroid will always be an int.
    """
    plugin_type = Component(FakeSignal, value='NDPluginStats')
    bgd_width = Component(FakeSignal, value=0)
    centroid_threshold = Component(FakeSignal, value=0)
    centroid = DynamicDeviceComponent(ad_group(FakeSignal, (('x'), ('y')), value=0),
                                      doc='The centroid XY')
    compute_centroid = Component(FakeSignal, value=0)
    compute_histogram = Component(FakeSignal, value=0)
    compute_profiles = Component(FakeSignal, value=0)
    compute_statistics = Component(FakeSignal, value=0)
    cursor = DynamicDeviceComponent(ad_group(FakeSignal, (('x'), ('y')), value=0),
                                    doc='The cursor XY')
    hist_entropy = Component(FakeSignal, value=0)
    hist_max = Component(FakeSignal, value=0)
    hist_min = Component(FakeSignal, value=0)
    hist_size = Component(FakeSignal, value=0)
    histogram = Component(FakeSignal, value=0)
    max_size = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='The maximum size in XY')
    max_value = Component(FakeSignal, value=0)
    max_xy = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Maximum in XY')
    mean_value = Component(FakeSignal, value=0)
    min_value = Component(FakeSignal, value=0)
    min_xy = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Minimum in XY')
    net = Component(FakeSignal, value=0)
    profile_average = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile average in XY')
    profile_centroid = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile centroid in XY')
    profile_cursor = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile cursor in XY')
    profile_size = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile size in XY')
    profile_threshold = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Profile threshold in XY')
    set_xhopr = Component(FakeSignal, value=0)
    set_yhopr = Component(FakeSignal, value=0)
    sigma_xy = Component(FakeSignal, value=0)
    sigma_x = Component(FakeSignal, value=0)
    sigma_y = Component(FakeSignal, value=0)
    sigma = Component(FakeSignal, value=0)
    ts_acquiring = Component(FakeSignal, value=0)
    ts_centroid = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Time series centroid in XY')
    ts_control = Component(FakeSignal, value=0)
    ts_current_point = Component(FakeSignal, value=0)
    ts_max_value = Component(FakeSignal, value=0)
    ts_max = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Time series maximum in XY')
    ts_mean_value = Component(FakeSignal, value=0)
    ts_min_value = Component(FakeSignal, value=0)
    ts_min = DynamicDeviceComponent(ad_group(
        FakeSignal, (('x'), ('y')), value=0), doc='Time series minimum in XY')
    ts_net = Component(FakeSignal, value=0)
    ts_num_points = Component(FakeSignal, value=0)
    ts_read = Component(FakeSignal, value=0)
    ts_sigma = Component(FakeSignal, value=0)
    ts_sigma_x = Component(FakeSignal, value=0)
    ts_sigma_xy = Component(FakeSignal, value=0)
    ts_sigma_y = Component(FakeSignal, value=0)
    ts_total = Component(FakeSignal, value=0)
    total = Component(FakeSignal, value=0)

    def __init__(self, prefix, *, noise_x=False, noise_y=False, 
                 noise_func_x=None, noise_func_y=None, noise_type_x="uni", 
                 noise_type_y="uni", noise_args_x=(), noise_args_y=(), 
                 noise_kwargs_x={}, noise_kwargs_y={}, **kwargs):
        super().__init__(prefix, **kwargs)
        self.noise_x = noise_x
        self.noise_y = noise_y
        self.noise_type_x = noise_type_x
        self.noise_type_y = noise_type_y
        self.noise_func_x = noise_func_x or (lambda : self._int_noise_func(
            self.centroid.x))
        self.noise_func_y = noise_func_y or (lambda : self._int_noise_func(
            self.centroid.y))
        self.noise_args_x = noise_args_x
        self.noise_args_y = noise_args_y
        self.noise_kwargs_x = noise_kwargs_x
        self.noise_kwargs_y = noise_kwargs_y
        # Override the default centroid calculator to always output ints
        self.centroid.x._get_readback = lambda **kwargs : int(np.round(
            self._get_readback_centroid_x()))
        self.centroid.y._get_readback = lambda **kwargs : int(np.round(
            self._get_readback_centroid_y()))

    def _get_readback_centroid_x(self, **kwargs):
        return self.centroid.x._raw_readback

    def _get_readback_centroid_y(self, **kwargs):
        return self.centroid.y._raw_readback

    def _int_noise_func(self, sig):
        if sig.noise_type == "uni":
            sig._check_args_uni()
            return int(np.round(sig.noise_uni()))
        elif self.noise_type == "norm":
            sig._check_args_norm()
            return int(np.round(sig.noise_norm()))
        else:
            raise ValueError("Invalid noise type. Must be 'uni' or 'norm'")        
                                            
    @property
    def noise_x(self):
        return self.centroid.x.noise

    @noise_x.setter
    def noise_x(self, val):
        self.centroid.x.noise = bool(val)

    @property
    def noise_y(self):
        return self.centroid.y.noise

    @noise_y.setter
    def noise_y(self, val):
        self.centroid.y.noise = bool(val)

    @property
    def noise_func_x(self):
        return self.centroid.x.noise_func()

    @noise_func_x.setter
    def noise_func_x(self, val):
        self.centroid.x.noise_func = val

    @property
    def noise_func_y(self):
        return self.centroid.y.noise_func()

    @noise_func_y.setter
    def noise_func_y(self, val):
        self.centroid.y.noise_func = val

    @property
    def noise_type_x(self):
        return self.centroid.x.noise_type

    @noise_type_x.setter
    def noise_type_x(self, val):
        self.centroid.x.noise_type = val

    @property
    def noise_type_y(self):
        return self.centroid.y.noise_type

    @noise_type_y.setter
    def noise_type_y(self, val):
        self.centroid.y.noise_type = val

    @property
    def noise_args_x(self):
        return self.centroid.x.noise_args

    @noise_args_x.setter
    def noise_args_x(self, val):
        self.centroid.x.noise_args = val

    @property
    def noise_args_y(self):
        return self.centroid.y.noise_args

    @noise_args_y.setter
    def noise_args_y(self, val):
        self.centroid.y.noise_args = val

    @property
    def noise_kwargs_x(self):
        return self.centroid.x.noise_kwargs

    @noise_kwargs_x.setter
    def noise_kwargs_x(self, val):
        self.centroid.x.noise_kwargs = val

    @property
    def noise_kwargs_y(self):
        return self.centroid.y.noise_kwargs

    @noise_kwargs_y.setter
    def noise_kwargs_y(self, val):
        self.centroid.y.noise_kwargs = val

class ImagePlugin(plugins.ImagePlugin, PluginBase):
    """
    Image plugin with a couple of the signals spoofed.

    To set ImagePlugin to return images using the array_data signal, override
    the _image method to be a method that returns the desired image
    """
    plugin_type = Component(FakeSignal, value="NDPluginStdArrays")
    array_data = Component(FakeSignal, value=np.zeros((256,256)))

    def __init__(self, prefix, *args, **kwargs):
        super().__init__(prefix, *args, **kwargs)
        # Spoof the different components
        self.array_data._get_readback = lambda : self._image().flatten()
        self.ndimensions._get_readback = lambda : len(self.array_size.get())
        self.array_size.height._get_readback = lambda : self._get_shape()[0]
        self.array_size.width._get_readback = lambda : self._get_shape()[1]
        self.array_size.depth._get_readback = lambda : self._get_shape()[2]

    def _get_shape(self):
        image_shape = self._image().shape
        pad_zeros = [0] * (3 - len(image_shape))
        return [*image_shape, *pad_zeros]

    def _image(self):
        return np.zeros((256, 256))
