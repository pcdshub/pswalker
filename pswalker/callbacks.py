"""
Specialized Callbacks for Skywalker
"""
############
# Standard #
############
import logging
from pathlib import Path

###############
# Third Party #
###############
import lmfit
from lmfit.models import LinearModel
from bluesky.callbacks import (LiveFit, CallbackBase)

##########
# Module #
##########


class LinearFit(LiveFit):
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
    def __init__(self, y, x, update_every=1):
        #Initialize fit
        super().__init__(y, x, {'x': axis},
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
        #Report error if no past fit
        if not self.result:
            raise RuntimeError("Can not evaluate without a saved fit,
                                use .update_fit()")

        #Return prediction
        return self.result.model.eval({'x': x})


    @property
    def report(self):
        """
        Report of most recent fit
        """
        #Report error if no past fit
        if not self.result:
            raise RuntimeError("No fit has been performed")

        return self.result.report


class PositionSaving(CallbackBase):
    def __init__(self, save_mode='batch', *args, **kwargs):
        self.save_mode = save_mode
        super().__init__(*args, **kwargs)
    
    def start(self, doc):
        print(doc)
    def descriptor(self, doc):
        
        # Build path to csv based on inputted mirrors and imagers
        self.csv_path = Path("")
        
        # If it doesnt already exist create it with correct headings
        if not self.csv_path.is_file():
            mirr_x = ["{0}_x".format(name) for name in doc['mirrors']]
            mirr_a = ["{0}_alpha".format(name) for name in doc['mirrors']]
            det_cent_x = ["{0}_cent_x".format(name) for name in doc['detectors']]
            det_cent_y = ["{0}_cent_y".format(name) for name in doc['detectors']]
            
            columns = ['uid', *mirr_x, *mirr_a, *det_cent_x, *det_cent_y, 
                       "imager"]

    def event(self, doc):
        print(doc)
    def stop(self, doc):
        print(doc)
