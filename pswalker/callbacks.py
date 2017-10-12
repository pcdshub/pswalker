"""
Specialized Callbacks for Skywalker
"""
############
# Standard #
############
import logging
import simplejson as sjson
from pathlib import Path

###############
# Third Party #
###############
import lmfit
import pandas as pd
import numpy  as np
from lmfit.models import LinearModel
from bluesky.callbacks import (LiveFit, LiveFitPlot, CallbackBase, LivePlot)

##########
# Module #
##########
from .utils.argutils import isiterable

logger = logging.getLogger(__name__)

def apply_filters(doc, filters=None, drop_missing=True):
    """
    Filter an event document

    Parameters
    ----------
    doc : dict
        Bluesky Document to filter

    filters : dict
        Filters are provided in a dictionary of key / callable pairs that take
        a single input from the data stream and return a boolean value.

    drop_missing : bool, optional
        Only include documents who have associated data for each filter key.
        This includes events missing the key entirely, reporting NaN or
    	reporting Inf.

    Returns
    -------
    resp : bool
        Whether the event passes all provided filters

    Example
    ------
    ..code::

        apply_filters(doc, filters = {'a' : lambda x : x > 0,
                                      'c' : lambda x : 4 < x < 6})
    """
    resp    = []
    filters = filters or dict()
    #Iterate through filters
    for key, func in filters.items(): 
        try:
            
            #Check iterables for nan and inf
            if isiterable(doc[key]):
                if any(np.isnan(doc[key])) or any(np.isinf(doc[key])):
                    resp.append(not drop_missing)
                    continue

            #Check string entries for nan and inf
            elif isinstance(doc[key], str):
                if "inf" == doc[key].lower() or "nan" == doc[key].lower():
                    resp.append(not drop_missing)
                    continue

            #Handle all other types
            else:
                if np.isnan(doc[key]) or np.isinf(doc[key]):
                    resp.append(not drop_missing)
                    continue

            #Evaluate filter
            resp.append(bool(func(doc[key])))
            
        #Handle missing information
        except KeyError:
            resp.append(not drop_missing)

        #Handle improper filter
        except Exception as e:
            logger.critical('Filter associated with event_key {}'\
                            'reported exception "{}"'\
                            ''.format(key, e))
    #Summarize
    return all(resp)


def rank_models(models, target, **kwargs):
    """
    Rank a list of models based on the accuracy of their prediction

    Parameters
    ----------
    models : list
        List of models to evaluate

    target : float
        Actual value of target

    kwargs :
        All of the keys the models will need to evaluate

    Returns
    -------
    model_ranking : list
        List of models sorted by accuracy of predictions
    """
    #Initialize values
    model_ranking = np.asarray(models)
    diffs         = list()
    bad_models    = list()

    #Calculate error of each model
    for model in models:
        try:
            estimate = model.eval(**kwargs)
            diffs.append(np.abs(estimate-target))
            logger.debug("Model {} predicted a value of {}"
                         "".format(model.name, estimate))
        except RuntimeError as e:
            bad_models.append(model)
            diffs.append(np.inf)
            logger.debug("Unable to yield estimate from model {}"
                         "".format(model.name))
            logger.debug(e)
    #Rank performances
    model_ranking = model_ranking[np.argsort(diffs)]
    #Remove models who failed to make an estimate
    return [model for model in model_ranking
            if model not in bad_models]


class LiveBuild(LiveFit):
    """
    Base class for live model building in Skywalker

    Parameters
    ----------
    model : lmfit.Model

    y: string
        Key of dependent variable

    indpendent_vars : dict
        Map independent variables names to keys in the event document stream

    init_guess: dict, optional
        Initial guesses for other values if expected 

    update_every : int or None, optional
        Update rate of the model. If set to None, the model will only be
        computed at the end of the run. By default, this is set to 1 i.e
        update on every new event
    """
    def __init__(self, model, y, independent_vars, init_guess=None,
                 update_every=1, filters=None, drop_missing=True,
                 average=1):
        super().__init__(model, y, independent_vars,
                         init_guess=init_guess,
                         update_every=update_every)
        #Add additional keys
        self.average      = average
        self.filters      = filters or {}
        self.drop_missing = drop_missing
        self._avg_cache   = list()



    @property
    def name(self):
        """
        Name of the model
        """
        return self.model.name


    @property
    def field_names(self):
        """
        Name of all the keys associated with the fit
        """
        return [self.y] + list(self.independent_vars.values())


    def install_filters(self, filters):
        """
        Install additional filters

        Parameters
        ----------
        filters : dict
            Filters are provided in a dictionary of key / callable pairs that
            take a single input from the data stream and return a boolean
            value.
        """
        self.filters.update(filters)


    def event(self, doc):
        #Run event through filters
        if not apply_filters(doc['data']):
            return

        #Add doc to average cache
        self._avg_cache.append(doc)

        #Check we have the right number of shots to average
        if len(self._avg_cache) >= self.average:
            #Overwrite event number
            #This can be removed with an update to Bluesky Issue #684
            doc['seq_num'] = len(self.ydata) +1 
            #Rewrite document with averages
            for key in self.field_names:
                doc['data'][key] = np.mean([d['data'][key]
                                            for d in self._avg_cache])
            #Send to callback
            super().event(doc)
            #Clear cache
            self._avg_cache.clear()


    def eval(self, *args, **kwargs):
        """
        Estimate a point based on the current fit of the model.
        Reimplemented by subclasses
        """
        logger.debug("Evaluating model {} with args : {}, kwargs {}"
                     "".format(self.name, args, kwargs))
        if not self.result:
            raise RuntimeError("Can not evaluate without a saved fit, "\
                               "use .update_fit()")

    def backsolve(self, target, **kwargs):
        """
        Use the most recent fit to find the independent variables that create
        the requested dependent variable

        ..note::

            For multivariable functions the user may have to specify which
            variable to solve for, and which to keep fixed
        """
        logger.debug("Backsolving model {} for target {} and kwargs {}"
                     "".format(self.name, target, kwargs))
        if not self.result:
            raise RuntimeError("Can not backsolve without a saved fit, "\
                               "use .update_fit()")


class LinearFit(LiveBuild):
    """
    Model to fit a linear relationship between a single variable axis and a 
    depended variable

    Parameters
    ----------
    y : str
        Keyword in the event document that reports the dependent variable

    x: str
        Keyword in the event document that reports the independent variable

    init_guess : dict, optional
        Initialization guess for the linear fit, available keys are ``slope``
        and ``intercept``

    name : optional , str
        Name for the contained model. When None (default) the name is the same
        as the model function

    update_every : int or None, optional
        Update rate of the model. If set to None, the model will only be
        computed at the end of the run. By default, this is set to 1 i.e
        update on every new event
    """
    def __init__(self, y, x, init_guess=None,
                 update_every=1, name=None,
                 average=1):
        #Create model
        model = LinearModel(missing='drop', name=name)

        #Initialize parameters
        init = {'slope' : 0, 'intercept' : 0}

        if init_guess:
            init.update(init_guess)

        #Initialize fit
        super().__init__(model, y, {'x': x},
                         init_guess=init,
                         update_every=update_every,
                         average=average)


    def eval(self, **kwargs):
        """
        Evaluate the predicted outcome based on the most recent fit of
        the given information.

        Parameters
        ----------
        x : float or int, optional
            Independent variable to evaluate linear model

        kwargs : 
            The value for the indepenedent variable can also be given as the
            field name in the event document
        Returns
        -------
        estimate : float
            Y value as determined by current linear fit
        """
        #Check result
        super().eval(**kwargs)

        #Standard x setup
        if kwargs.get('x'):
            x = kwargs['x']

        elif self.independent_vars['x'] in kwargs.keys():
            x = kwargs[self.independent_vars['x']]

        else:
            raise ValueError("Must supply keyword `x` or use fieldname {}"
                             "".format(self.independent_vars['x']))

        #Structure input add past result
        kwargs = {'x' : np.asarray(x)}
        kwargs.update(self.result.values)

        #Return prediction
        return self.result.model.eval(**kwargs)


    def backsolve(self, target, **kwargs):
        """
        Find the ``x`` position that solves the reaches the given target

        Parameters
        ----------
        target : float
            Desired ``y`` value

        Returns
        -------
        x : dict
            Variable name and floating value
        """
        #Make sure we have a fit
        super().backsolve(target, **kwargs)
        
        #Gather line information
        (m, b) = (self.result.values['slope'],
                  self.result.values['intercept'])
        #Return x position
        if m == 0 and b != target:
            raise ValueError("Unable to backsolve, because fit is horizontal " 
                             " after {} data points".format(len(self.ydata)))

        return {'x' : (target-b)/m}


class MultiPitchFit(LiveBuild):
    """
    Model to fit centroid position of two mirror system

    Parameters
    ----------
    centroid : str
        Keyword in the event document that reports centroid position

    alphas : tuple of str
        Tuple fo the mirror pitches (a1, a2)

    init_guess : dict, optional
        Initialization guess for the linear fit, available keys are be ``x0``,
        ``x1``, and ``x2``

    name : optional , str
        Name for the contained model. When None (default) the name is the same
        as the model function

    update_every : int or None, optional
        Update rate of the model. If set to None, the model will only be
        computed at the end of the run. By default, this is set to 1 i.e
        update on every new event
    """
    def __init__(self, centroid, alphas,
                 name=None, init_guess=None,
                 update_every=1, average=1):

        #Simple model of two-bounce system
        def two_bounce(a0, a1, x0, x1, x2):
            return x0 + a0*x1 + a1*x2

        #Create model
        model = lmfit.Model(two_bounce,
                            independent_vars = ['a0', 'a1'],
                            missing='drop')

        #Initialize parameters
        init = {'x0' : 0, 'x1': 0, 'x2' : 0}

        if init_guess:
            init.update(init_guess)


        #Initialize fit
        super().__init__(model, centroid,
                         independent_vars={'a0' : alphas[0],
                                           'a1' : alphas[1]},
                         init_guess=init, update_every=update_every,
                         average=average)


    def eval(self, a0=0., a1=0., **kwargs):
        """
        Evaluate the predicted outcome based on the most recent fit of
        the given information

        Parameters
        ----------
        a0 : float
            Pitch of the first mirror

        a1 : float
            Pitch of the second mirror

        Returns
        -------
        centroid : float
            Position of the centroid as predicted by the current model fit
        """
        #Check result
        super().eval(a0, a1)

        #Structure input and add past result
        kwargs = {'a0' : np.asarray(a0),
                  'a1' : np.asarray(a1)}
        kwargs.update(self.result.values)

        #Return prediction
        return self.result.model.eval(**kwargs)


    def backsolve(self, target, a0=None, a1=None):
        """
        Find the mirror configuration to reach a certain pixel value

        Because this is a multivariable function you must fix one of the
        mirrors in place, while the other one is solved for.

        Parameters
        ----------
        target : float
            Desired pixel location

        a0 : float, optional
            Fix the first mirror in the system

        a1 : float, optional
            Fix the second mirror in the system

        Returns
        -------
        angles : dict
            Dictionary with the variable mirror key and solvable value
        """
        #Make sure we have a fit
        super().backsolve(target, a0=a0, a1=a1)

        #Check for valid request
        if not any([a0,a1]) or all([a0,a1]):
            raise ValueError("Exactly one of the mirror positions "\
                             "must be specified to backsolve for the target")
        #Gather fit information
        (x0, x1, x2) = (self.result.values['x0'],
                        self.result.values['x1'],
                        self.result.values['x2'])
        #Return computed value
        if a0:
            return {'a1' : (target - x0 - a0*x1)/ x2,
                    'a0' : a0}
        else:
            return {'a0' : (target - x0 - a1*x2)/ x1,
                    'a1' : a1}


class LivePlotWithGoal(LivePlot):
    """
    Build a function that updates a plot from a stream of Events.
    
    
    Parameters
    ----------
    y : str
        the name of a data field in an Event
    x : str, optional
        the name of a data field in an Event, or 'seq_num' or 'time'
        If None, use the Event's sequence number.
        Special case: If the Event's data includes a key named 'seq_num' or
        'time', that takes precedence over the standard 'seq_num' and 'time'
        recorded in every Event.
    goal : float
        the target pixel
    tolerance : float, optional
        the tolerance for the pixel
    averages : float, optional
        The number of images to average. If None is specified, every point is rendered as they come,
        otherwise the graph will update every ```averages``` points.
    legend_keys : list, optional
        The list of keys to extract from the RunStart document and format
        in the legend of the plot. The legend will always show the
        scan_id followed by a colon ("1: ").  Each
    xlim : tuple, optional
        passed to Axes.set_xlim
    ylim : tuple, optional
        passed to Axes.set_ylim
    ax : Axes, optional
        matplotib Axes; if none specified, new figure and axes are made.
    fig : Figure, optional
        deprecated: use ax instead
    epoch : {'run', 'unix'}, optional
        If 'run' t=0 is the time recorded in the RunStart document. If 'unix',
        t=0 is 1 Jan 1970 ("the UNIX epoch"). Default is 'run'.
    kwargs :
    All additional keyword arguments are passed through to ``Axes.plot``.
    
    Notes
    -----
    If your figure blocks the main thread when you are trying to scan with this
    callback, call `plt.ion()` in your IPython session.
    
    Examples
    --------
    >>> my_plotter = LivePlotWithGoals('det', 'motor', goal=10.0, tolerance=1.5, averages=None, legend_keys=['sample'])
    >>> RE(my_scan, my_plotter)
    """
    def __init__(self, y, x=None, *, goal=0.0, tolerance=0.0, averages=None, **kwargs):
        super().__init__(y, x, **kwargs)
        self.legend_title = None
        self.goal = goal
        self.tolerance = tolerance
        self.averages = averages
        self.event_count = 0

    def start(self, doc):
        self.goal_data = []
        self.goal_axis, = self.ax.plot([],[],'r--', label='Target')
        super().start(doc)

    def event(self, doc):
        super().event(doc)
        self.event_count += 1

    def update_plot(self, force=False):
        if self.averages is None or (self.averages is not None and self.event_count % self.averages == 0) or force:
            self.goal_axis.set_data(self.x_data, self.goal_data)
            goal = np.asarray(self.goal_data)
            distance = 2 if self.averages is None else self.averages+1
            if force:
                distance -= 1
            self.ax.fill_between(self.x_data[-distance:], goal[-distance:]-self.tolerance, goal[-distance:]+self.tolerance,
                                 alpha=0.2, facecolor='r')
            super().update_plot()
            self.ax.set_xlim(left=0, right=None, auto=True)

    def update_caches(self, x, y):
        self.goal_data.append(self.goal)
        super().update_caches(x, y)

    def stop(self, doc):
        # Ensure that the last events are plotted
        # Only necessary when we are grouping the points
        if self.averages is not None:
            self.update_plot(force=True)
        super().stop(doc)
