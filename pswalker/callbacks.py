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
from bluesky.callbacks import (LiveFit, LiveFitPlot, CallbackBase)

##########
# Module #
##########

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
        This includes events missing the key entirely or reporting NaN

    Returns
    -------
    resp : bool
        Whether the event passes all provided filters

    Example
    -------
    ..code::

        apply_filters(doc, filters = {'a' : lambda x : x > 0,
                                      'c' : lambda x : 4 < x < 6})
    """
    resp    = []
    filters = filters or dict()

    #Iterate through filters
    for key, func in filters.items(): 
        try:
            #Handle NaN
            if pd.isnull(doc['data'][key]):
                resp.append(not drop_missing)

            #Evaluate filter
            else:
                resp.append(bool(func(doc['data'][key])))

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
    def eval(self, *args, **kwargs):
        """
        Estimate a point based on the current fit of the model.
        Reimplemented by subclasses
        """
        if not self.result:
            raise RuntimeError("Can not evaluate without a saved fit, "\
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

    update_every : int or None, optional
        Update rate of the model. If set to None, the model will only be
        computed at the end of the run. By default, this is set to 1 i.e
        update on every new event
    """
    def __init__(self, y, x, init_guess=None, update_every=1):
        #Create model
        model = LinearModel(missing='drop')
        
        #Initialize parameters
        init = {'slope' : 0, 'intercept' : 0}

        if init_guess:
            init.update(init_guess)
        
        #Initialize fit
        super().__init__(model, y, {'x': x},
                         init_guess=init,
                         update_every=update_every)


    def eval(self, x):
        """
        Evaluate the predicted outcome based on the most recent fit of
        the given information

        Parameters
        ----------
        x : float or int
            Independent variable to evaluate linear model
        """
        #Check result
        super().eval(x)
        
        #Structure input add past result
        kwargs = {'x' : np.asarray(x)} 
        kwargs.update(self.result.values)

        #Return prediction
        return self.result.model.eval(**kwargs)


class MultiPitchFit(LiveBuild):
    """
    Model to fit centroid position of two mirror system

    Parameters
    ----------
    centroid : str
        Keyword in the event document that reports centroid position

    alphas : tuple of str
        Tuple fo the mirror pitches (a1, a2)

    update_every : int or None, optional
        Update rate of the model. If set to None, the model will only be
        computed at the end of the run. By default, this is set to 1 i.e
        update on every new event
    """
    def __init__(self, centroid, alphas, init_guess=None, update_every=1):

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
                         init_guess=init, update_every=update_every)


    def eval(self, a0, a1):
        """
        Evaluate the predicted outcome based on the most recent fit of
        the given information

        Parameters
        ----------
        alphas : tuple of float
            Mirror angles
        """
        #Check result
        super().eval(a0, a1)

        #Structure input and add past result
        kwargs = {'a0' : np.asarray(a0),
                  'a1' : np.asarray(a1)}
        kwargs.update(self.result.values)

        #Return prediction
        return self.result.model.eval(**kwargs)


class LiveModelPlot(LiveFitPlot):
    """
    LivePlot to display the relationship between centroid and mirror positions

    Parameters
    ----------
    livefit : :class:`.LinearFit`
        Fit to plot

    imager : :class:`.PIM`
        Imager centroid position

    mirror : :class:`.Homs`
        Mirror pitch

    target : float, optional

    num_points : int, optional

    ax : Axes, optional
    """
    def __init__(self, livefit, imager, mirror,
                 num_points=100, target=None, ax=None):
        #Model information
        self.imager = imager
        self.mirror = mirror
        self.target = target
        #Initalize Plot
        super().__init__(livefit,
                         num_points=num_points,
                         ax=ax)


    def start(self, doc):
        super().start(doc)
        if self.target:
            self.ax.axvline(x=self.target, color='r')


class PositionSaving(CallbackBase):
    def __init__(self, save_mode='batch', csv=False, *args, **kwargs):
        self.save_mode = save_mode
        self.use_csv = csv
        self._json_stack = []
        self._csv_stack = []
        super().__init__(*args, **kwargs)
    
    def start(self, doc):
        # Build path to csv and json based on inputted mirrors and imagers
        self.run_id = doc['uid']
        self.run_id_short = self.run_id[-6:]
        self.file_str = "{0}_{1}_{2}_{3}".format(*doc['mirrors'], 
                                                 *doc['detectors'])
        
        # If json file doesnt exist then create a new one and add the start doc
        self.json_path = Path("/reg/g/pcds/pyps/apps/skywalker/json/{0}_{1}.json".format(
            self.file_str, self.run_id_short))
        if self.save_mode == "batch":
            self._json_stack.append(doc)
        elif self.save_mode == "stochastic":
            with self.json_path.open(mode='x') as json:
                sjson.dump(doc, json, indent=4)
                
        
        # If saving a csv, check if it exists and save a header if it doesnt
        if self.use_csv:
            self.csv_path = Path("/reg/g/pcds/pyps/apps/skywalker/csv/{0}.csv".format(self.file_str))
            if not self.csv_path.is_file():
                mirr_x = ["{0}_x".format(name) for name in doc['mirrors']]
                mirr_a = ["{0}_alpha".format(name) for name in doc['mirrors']]
                det_cent_x = ["{0}_cent_x".format(name) for name in 
                              doc['detectors']]
                det_cent_y = ["{0}_cent_y".format(name) for name in 
                              doc['detectors']]
                det_mean = ["{0}_mean".format(name) for name in doc['detectors']]

                columns = ['runid', 'uid', *mirr_x, *mirr_a, *det_cent_x, 
                           *det_cent_y, *det_mean]
                with self.csv_path.open(mode='x') as csv:
                    csv.write(", ".join(columns))

            # Grab the keys that will be used to create csv
            mirr_x_key = ["{0}_gan_x_p".format(name) for name in doc['mirrors']]
            mirr_a_key = ["{0}_pitch".format(name) for name in doc['mirrors']]
            det_cent_x_key = ["{0}_detector_stats2_centroid_x".format(name)
                              for name in doc['detectors']]
            det_cent_y_key = ["{0}_detector_stats2_centroid_x".format(name)
                              for name in doc['detectors']]
            det_mean = ["{0}_detector_stats2_mean_value".format(name)
                        for name in doc['detectors']]
            self.keys = ['uid', *mirr_x_key, *mirr_a_key, *det_cent_x_key,
                         *det_cent_y_key, *det_mean]

    def descriptor(self, doc):
        # Save the descriptor doc or add it to the stack
        if self.save_mode == "batch":
            self._json_stack.append(doc)
        elif self.save_mode == "stochastic":
            with self.json_path.open(mode='a') as json:
                sjson.dump(doc, json, indent=4)
        
    def event(self, doc):
        # Save the event doc or add it to the stack
        if self.save_mode == "batch":
            self._json_stack.append(doc)
        elif self.save_mode == "stochastic":
            with self.json_path.open(mode='a') as json:
                json.dump(doc, json, indent=4)
           
        # Check to see if this event document contains all the info we need, and
        # add it to the stack if in batch. Write it if not.
        if self.use_csv:
            try:
                vals = [self.run_id] + [doc[key] for key in self.keys]
            except KeyError:
                pass
            else:
                if self.save_mode == "batch":
                    self._json_stack.append(doc)
                elif self.save_mode == "stochastic":
                    with self.csv_path.open(mode='x') as csv:
                        csv.write(", ".join(columns))
    
    def stop(self, doc):
        # Save the stop doc or append to the stack
        if self.save_mode == "batch":
            self._json_stack.append(doc)
        elif self.save_mode == "stochastic":
            with self.json_path.open(mode='a') as json:
                sjson.dump(doc, json, indent=4)                

        # Save the stack if there is anything in it
        if self._json_stack:
            with self.json_path.open(mode='w+') as json:            
                try:
                    for jdoc in self._json_stack:
                        sjson.dump(jdoc, json, indent=4)                    
                except Exception as e:
                    print(e)
        # print(self.use_csv)
        # print(len(self._csv_stack))
        # print(self._csv_stack[0])
        # print(self._csv_stack[-1])
        if self.use_csv and self._csv_stack:
            print(len(self._csv_stack))
            with self.csv_path.open(mode='w+') as csv:
                for entry in self._csv_stack:
                    csv.write(", ".join(entry))
                
