Slit Fiducialization
====================
In order to define an alignment trajectory, the target pixel on each imager
must be defined. To avoid issues that arise with cameras either being adjusted
or even those with unreliable focus and zoom, it was a goal of this project to
automate the fiducialization process. ``pswalker`` provides to plans to
accomplish the goal, the first is the simplest; close the slits, insert the
imager and take a centroid measurement :func:`.slit_scan_fiducialize`. However,
there may be a case where we are trying to fiducialize our YAG with a
misaligned beam. In this case, :func:`.fiducialize` starts with a small
aperature, attempts to fiducialize, and upon failure increases the aperature
size and attempts again.

.. autofunction:: pswalker.plan_stubs.slit_scan_fiducialize

.. autofunction:: pswalker.plan_stubs.fiducialize


The information given by these methods are entirely in pixels. Clearly, we can
use the slits to set a known aperature size and count the pixels of the square
we have created to convert back to known unit. This process is automated using:

.. autofunction:: pswalker.plan_stubs.slit_scan_area_comp
