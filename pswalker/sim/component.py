from ophyd.device import Component
import ophyd.device as device


class DynamicDeviceComponent(device.DynamicDeviceComponent):
    """
    DynamicDeviceComponent that accepts signals with no suffix.
    """
    def create_attr(self, attr_name):
        try:
            cls, suffix, kwargs = self.defn[attr_name]
            inst = Component(cls, suffix, **kwargs)
        except ValueError:
            cls, kwargs = self.defn[attr_name]
            inst = Component(cls, **kwargs)
        inst.attr = attr_name
        return inst

    def __repr__(self):
        doc = []
        for attr, items in self.defn.items():
            try:
                cls, suffix, kwargs = items
            except ValueError:
                cls, kwargs = items
                suffix = None
            kw_str = ', '.join('{}={!r}'.format(k, v)
                               for k, v in kwargs.items())
            if suffix is not None:
                suffix_str = '{!r}'.format(suffix)
                if kwargs:
                    suffix_str += ', '
            else:
                suffix_str = ''
            if suffix_str or kw_str:
                arg_str = ', {}{}'.format(suffix_str, kw_str)
            else:
                arg_str = ''
            doc.append('{attr} = Component({cls.__name__}{arg_str})'
                       ''.format(attr=attr, cls=cls, arg_str=arg_str))
        return '\n'.join(doc)
