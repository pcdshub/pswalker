from ophyd.areadetector import cam
from ophyd.device import Component

from .base import ad_group
from ..signal import FakeSignal
from ..component import DynamicDeviceComponent


class CamBase(cam.CamBase):
    # Shared among all cams and plugins
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
    port_name = Component(FakeSignal, value='CAM')

    # Cam-specific
    acquire = Component(FakeSignal, value=0)
    acquire_period = Component(FakeSignal, value=0)
    acquire_time = Component(FakeSignal, value=0)

    array_callbacks = Component(FakeSignal, value=0)
    array_size = DynamicDeviceComponent(ad_group(FakeSignal,
                              (('array_size_x'),
                               ('array_size_y'),
                               ('array_size_z')), value=0),
                     doc='Size of the array in the XYZ dimensions')

    array_size_bytes = Component(FakeSignal, value=0)
    bin_x = Component(FakeSignal, value=0)
    bin_y = Component(FakeSignal, value=0)
    color_mode = Component(FakeSignal, value=0)
    data_type = Component(FakeSignal, value=0)
    detector_state = Component(FakeSignal, value=0)
    frame_type = Component(FakeSignal, value=0)
    gain = Component(FakeSignal, value=0)

    image_mode = Component(FakeSignal, value=0)
    manufacturer = Component(FakeSignal, value=0)

    max_size = DynamicDeviceComponent(ad_group(FakeSignal,
                            (('max_size_x'),
                             ('max_size_y')), value=0),
                   doc='Maximum sensor size in the XY directions')

    min_x = Component(FakeSignal, value=0)
    min_y = Component(FakeSignal, value=0)
    model = Component(FakeSignal, value=0)

    num_exposures = Component(FakeSignal, value=0)
    num_exposures_counter = Component(FakeSignal, value=0)
    num_images = Component(FakeSignal, value=0)
    num_images_counter = Component(FakeSignal, value=0)

    read_status = Component(FakeSignal, value=0)
    reverse = DynamicDeviceComponent(ad_group(FakeSignal,
                           (('reverse_x'),
                            ('reverse_y')), value=0))

    shutter_close_delay = Component(FakeSignal, value=0)
    shutter_close_epics = Component(FakeSignal, value=0)
    shutter_control = Component(FakeSignal, value=0)
    shutter_control_epics = Component(FakeSignal, value=0)
    shutter_fanout = Component(FakeSignal, value=0)
    shutter_mode = Component(FakeSignal, value=0)
    shutter_open_delay = Component(FakeSignal, value=0)
    shutter_open_epics = Component(FakeSignal, value=0)
    shutter_status_epics = Component(FakeSignal, value=0)
    shutter_status = Component(FakeSignal, value=0)

    size = DynamicDeviceComponent(ad_group(FakeSignal,
                        (('size_x'),
                         ('size_y')), value=0))

    status_message = Component(FakeSignal, value=0)
    string_from_server = Component(FakeSignal, value=0)
    string_to_server = Component(FakeSignal, value=0)
    temperature = Component(FakeSignal, value=0)
    temperature_actual = Component(FakeSignal, value=0)
    time_remaining = Component(FakeSignal, value=0)
    trigger_mode = Component(FakeSignal, value=0)
    
    # Extra
    resolution = DynamicDeviceComponent(ad_group(FakeSignal,
                                                 (('resolution_x'),
                                                  ('resolution_y')), value=0))


class PulnixCam(CamBase):
    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        # Set some default values that are the same as the actual camera
        self.array_rate.put(120.0)
        self.nd_attributes_file.put('')
        self.port_name.put('CAM')
        self.acquire.put(1)
        self.acquire_time.put(0.000299991596655155)        
        self.array_size.array_size_x.put(640)
        self.array_size.array_size_y.put(480)
        self.array_size_bytes.put(307200)
        self.data_type.put(3)
        self.image_mode.put(2)
        self.manufacturer.put('PULNIX')
        self.max_size.max_size_x.put(640)
        self.max_size.max_size_y.put(480)
        self.model.put('SIMULATED')
        self.num_exposures.put(1)
        self.num_images.put(1)
        self.size.size_x.put(640)
        self.size.size_y.put(480)
        self.trigger_mode.put(2)
        self.resolution.resolution_x.put(0.0076)
        self.resolution.resolution_y.put(0.0062)
