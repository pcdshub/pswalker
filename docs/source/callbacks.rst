Fits and Plots
==============
``pswalker`` uses callbacks to monitor live data, create fits and pipe this
back into scanning logic in order to reach desired positions. These all build
off of :class:`.LiveBuild` in order to be used with the :func:`.fitwalk`. The
most prominent example of this in the repository is :func:`.walk_to_pixel`


LiveBuild
---------

.. autoclass:: pswalker.callbacks.LiveBuild
   :members:
   :show-inheritance:


.. autoclass:: pswalker.callbacks.LinearFit
   :members:
   :show-inheritance:


Plots
-----

.. autoclass:: pswalker.callbacks.LivePlotWithGoal
   :members:
   :show-inheritance:
