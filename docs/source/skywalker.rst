Iterwalk
========
The main workhorse of the Skywalker routine is :func:`.pswalker.iterwalk`. This
handles iteratively aligning a two mirror system on two imagers until the final
solution is converged upon.

.. autofunction:: pswalker.iterwalk.iterwalk

In practice, we wrap this function to automatically configure a number of the
parameters, as well as handle setup of other utilities such as plotting and
suspension

.. autofunction:: pswalker.skywalker.skywalker
