############
# Standard #
############
import logging
import textwrap
from collections import namedtuple

###############
# Third Party #
###############
from jinja2 import Environment
from prettytable import PrettyTable
from bluesky.callbacks import CallbackBase

##########
# Module #
##########
logger = logging.getLogger(__name__)


#Data structure for holding alignment information
RunSummary = namedtuple('RunSummary', ['successful', 'mirrors', 'pixels',
                                       'elapsed', 'reason', 'suspension_count',
                                       'suspended', 'tolerance', 'averaging',
                                       'moves', 'cycles', 'table', 'detectors'])


class Watcher(CallbackBase):
    """
    The Watcher for the Skywalker run

    Absorbs messages after they are proccesed from the RunEngine, as well as
    receiving emitted to watch the progress of the alignment. In order to take
    full advantage of the feature set the Watcher should be subscribed to all
    events sent from the RunEngine, the Watcher should be set as the `msg_hook`
    for the RunEngine to capture motion requests, and finally the
    `record_interruptions` flag should be set to True

    Parameters
    ----------
    msg_hook : callable, optional
        Useful if you want to send the messages to another process or display

    report_hook : callable, optional
        Send the final report to another process, this will be done
        automatically at the end of a run
    """
    def __init__(self, msg_hook=None, report_hook=None):
        #Hooks for displaying information
        self.msg_hook    = msg_hook
        self.report_hook = report_hook or print
        #Store run parameters
        self.summary         = dict.fromkeys(RunSummary._fields, '')
        #Change default from str to int
        self.summary['suspension_count'] = 0
        self.summary['moves']            = 0
        self.last_known      = dict()
        self.msgs            = list()
        self.last_suspension = 0.0

    def start(self, doc):
        """
        Parse the start document for parameters of Skywalker run as well as
        start time
        """
        self.summary['detectors'] = ', '.join(doc.get('detectors', []))
        self.summary['mirrors'] = ', '.join(doc.get('mirrors',[]))
        self.summary['pixels'] = ', '.join([str(goal)
                                            for goal in doc.get('goals',[])])
        self.summary['averaging'] = doc.get('plan_args',{}).get('averages')
        self.summary['tolerance'] = doc.get('plan_args',{}).get('tolerances')
        self.mot_fields = doc.get('plan_args', {}).get('mot_fields')
        self.det_fields = doc.get('plan_args', {}).get('det_fields')
        self.summary['elapsed'] = doc['time']
        super().start(doc)


    def event(self, doc):
        """
        Parse event documents for information on suspensions and measured
        values
        """
        for key, value in doc['data'].items():
            if key == 'interruption':
                #Keep track of suspensions
                if value in ['suspend', 'pause']:
                    self.last_suspension = doc['time']
                    self.summary['suspension_count'] += 1
                #Integrate suspension time
                elif value == 'resume':
                    self.summary['suspended']+= (doc['time']
                                                 - self.last_suspension)
            #Update device state caches
            elif (value and any([field in key
                                 for group in [self.mot_fields,
                                               self.det_fields]
                                 for field in group])):
                self.last_known.update({key : value})

    def stop(self, doc):
        """
        Parse the stop document to find the end time and whether the beam was
        ulitmately aligned within the tolerances
        """
        #Save exit information
        self.summary['successful'] = doc['exit_status']
        self.summary['reason']     = doc['reason']
        self.summary['elapsed']    = doc['time'] - self.summary['elapsed']
        #Find 
        self.summary['moves'] = len([msg for msg in self.msgs
                                     if (msg.command == 'set'
                                     and msg.obj.name in self.summary['mirrors'])
                                   ])
        self.summary['cycles'] = round(len([msg for msg in self.msgs
                                      if (msg.command == 'set'
                                      and msg.obj.name in
                                      self.summary['detectors'])
                                      ])/2)
        #Create last known table
        pt = PrettyTable(['Field', 'Last Measured Value'])

        #Adjust Table settings
        pt.align = 'r'
        pt.align['Name'] = 'l'
        pt.align['Prefix'] = 'l'
        pt.float_format  = '8.5'

        #Add info
        for key, value in self.last_known.items():
            pt.add_row([key, value])

        self.summary['table'] = pt

        #Report the run summary
        super().stop(doc)


    def report(self, width=79):
        """
        Create a report

        Fill the template with the most recent run information as well as
        passing the report on to the :attr:`.report_hook`

        Returns
        -------
        report : str
            Filled report template
        """
        #Create summary document
        run=RunSummary(**self.summary)
        #Render report
        report=Environment(trim_blocks=True).from_string(report_tpl).render(run=run)
        #Clean and wrap text
        dedented = textwrap.dedent(report)
        report = textwrap.fill(dedented, width=width)
        #Assemble full report
        report = '\n'.join(['',report,'',str(self.summary['table'])])
        #Send report to optional hook
        if self.report_hook:
            self.report_hook(report)
        return report


    def __call__(self, *args):
        if len(args) > 1:
            super().__call__(*args)
        else:
            self.msgs.append(args[0])
            if self.msg_hook:
                self.msg_hook(args[0])


report_tpl = """\
{%if run.successful %}
Skywalker successfuly aligned {{run.mirrors}} to {{run.pixels}} on
{{run.detectors}} in {{run.elapsed | round(2)}} seconds!
{% else %}
Skywalker failed to align {{run.mirrors}} to {{run.pixels}} on
{{run.detectors}} after {{run.elapsed | round(2)}} seconds, failing because
"{{run.reason}}".
{% endif %}
{% if run.suspension_count > 0 %}
During the alignment procedure the scan was paused {{run.suspension_count}}
times for a total of {{run.suspended | round(2)}} seconds.
{% endif %}
{% if run.moves > 0 %}
The entire alignment moved the mirrors {{run.moves}} times, cycling between
YAGs {{run.cycles}} times.
{% endif %}
The user requested that the mirrors hit their targets within {{run.tolerance}}
pixels, averaging over {{run.averaging}} consecutive images after each mirror
motion. The resulting locations of mirrors and centroid measurements can be
seen in the table below.\n\n"""

