# -*- coding: utf-8 -*-
"""
Tools for analyzing network models and results
"""

import pandas as pd
import numpy as np

from wntr.network.options import WaterNetworkOptions
from wntr.network.elements import LinkType, NodeType, LinkStatus
from wntr.network.elements import TimeSeries, Pattern, Curve, Demands, Source
from wntr.network.model import WaterNetworkModel
from wntr.network.model import Node, Junction, Tank, Reservoir
from wntr.network.model import Link, Pipe, Pump, Valve
from wntr.epanet.util import FlowUnits, from_si, HydParam        

class NetworkAnalyzer(object):
    """Perform network analysis tasks.
    
    Provides methods to get statistics about a WaterNetworkModel.
    Also provides the ability to compare the structure of two networks
    with different restrictions.
    
    """
    
    class NetComparisonResult(object):
        """Structure for storing results of network/results comparisons"""
        def __init__(self):
            self.comparison = None
            self.netA = None
            self.netB = None
            self.only_in_netA = {}
            self.only_in_netB = {}
            self.in_both_but_differ = {}
            self.in_both_and_equiv = {}
#    
#    @classmethod        
#    def summarize(cls, model, units=FlowUnits.SI):
#        """Return a dictionary of some summary statistics.
#        
#        * counts
#        * * number of nodes
#        * * number of junctions
#        * * number of tanks
#        * * number of reservoirs
#        * * number of links
#        * * number of pipes
#        * * number of pumps
#        * * number of valves
#        * * number of patterns
#        * * number of curves
#        * * number of sources
#        * * number of controls
#        * totals
#        * * total duration
#        * * total pipe length
#        * * total system consumption
#        
#        """
#        summary = dict(counts=dict(), stats=dict())
#        summary['counts']['junctions'] = model.num_junctions
#        summary['counts']['tanks'] = model.num_tanks
#        summary['counts']['reservoirs'] = model.num_reservoirs
#        summary['counts']['pipes'] = model.num_pipes
#        summary['counts']['pumps'] = model.num_pumps
#        summary['counts']['valves'] = model.num_valves
#        summary['counts']['patterns'] = model.num_patterns
#        summary['counts']['curves'] = model.num_curves
#        summary['counts']['sources'] = model.num_sources
#        summary['counts']['controls'] = model.num_controls
#        total_pipe_len = sum(model.query_link_attribute('length').values())
#        summary['stats']['reporting-units'] = units._vlt
#        summary['stats']['total-pipe-length'] = from_si(units, total_pipe_len, HydParam.length)
#        def map_time(time):
#            def map_at(dlist):
#                v = dlist.at(time)
#                return v if v > 0 else 0
#            return sum(map(map_at, model.query_node_attribute('demand_timeseries_list', node_type=Junction).values()))
#        pattern_steps = np.arange(0, model.options.time.duration, model.options.time.pattern_timestep)
#        demand = sum(map(map_time, pattern_steps))*model.options.time.pattern_timestep
#        summary['stats']['total-consumption'] = from_si(units, demand, HydParam.demand) / units.time_factor
#        summary['stats']['average-demand'] = from_si(units, demand / model.options.time.duration, HydParam.demand)
#        summary['stats']['total-duration'] = model.options.time.duration / units.time_factor
#        return summary

    @classmethod
    def describe(cls, *args, **kwargs):
        summary_columns = []
        for arg in args:
            if not isinstance(arg, WaterNetworkModel):
                raise ValueError('arguments must be WaterNetworkModels')
            summary_columns.append(arg.name)
        summary_rows = ['Node ct.', 'Junctions', 'Tanks', 'Reservoirs',
                        'Link ct.', 'Pipes', 'Pumps', 'Valves',
                        'Pattern ct.', 'Curve ct.', 'Control ct.', 'Source ct.',
                        'Sim. duration', 'Pat. step', 'Hyd. step', 'Qual. step',
                        'Total pipe len.', 'Cum. system demand', 'Ave. daily demand']
        summary = pd.DataFrame(index=summary_rows, columns=summary_columns)
        steps = [0, 0, 0]
        def get_values(item):
            if hasattr(item[1],'demand_timeseries_list'):
                v = item[1].demand_timeseries_list.get_values(*steps)
            else:
                v = np.zeros([1+int(steps[1]/steps[2])])
            return (item[0], v)
        for ct, netA in enumerate(args):
            i = summary_columns[ct]
            tplA = sum(netA.query_link_attribute('length').values())
            summary.at['Total pipe len.',i] = tplA
            steps[:] = [0, netA.options.time.duration-netA.options.time.pattern_timestep, netA.options.time.pattern_timestep]
            demandA = pd.DataFrame.from_items(map(get_values, netA._nodes.items()))
            cumA = np.sum(demandA.sum())*netA.options.time.pattern_timestep
            summary.at['Cum. system demand',i] = cumA
            dailyA = cumA / netA.options.time.duration * 86400
            summary.at['Ave. daily demand',i] = dailyA
            summary.at['Node ct.',i] = netA.num_nodes
            summary.at['Junctions',i] = netA.num_junctions
            summary.at['Tanks',i] = netA.num_tanks
            summary.at['Reservoirs',i] = netA.num_reservoirs
            summary.at['Link ct.',i] = netA.num_links
            summary.at['Pipes',i] = netA.num_pipes
            summary.at['Pumps',i] = netA.num_pumps
            summary.at['Valves',i] = netA.num_valves
            summary.at['Pattern ct.',i] = netA.num_patterns
            summary.at['Curve ct.',i] = netA.num_curves
            summary.at['Control ct.',i] = netA.num_controls
            summary.at['Source ct.',i] = netA.num_sources
            summary.at['Sim. duration',i] = netA.options.time.duration
            summary.at['Pat. step',i] = netA.options.time.pattern_timestep
            summary.at['Hyd. step',i] = netA.options.time.hydraulic_timestep
            summary.at['Qual. step',i] = netA.options.time.quality_timestep
        
        return summary
        

    def compare_structure(cls, netA, netB):
        """Compare for structural differences between two network models.
        
        This compares the physical layout of the network: i.e., nodes and links.
        For this to work nodes which are the same must have the same name in
        each network model - it does not do a topological equivalency to map 
        names.
        
        Compared:
            names
            node/link type
            elevations
            min/max level
            min volume
            lengths
            diameters
            curves
            roughness
            minor loss
            connectivity
            check valve
            mixing model            
            
        Not compared:
            demands
            reservoir head/head pattern
            initial level, setting or status
            speeds, energy or efficiency
            initial quality
            reaction coefficients
            pipe vertices
            
        """
        res = cls.NetComparisonResult()
        res.netA = netA
        res.netB = netB
        

class ResultsAnalyzer(object):
    """Perform analyses on net results objects"""
    def init(self):
        pass
    
    def summarize(self, results, units=FlowUnits.SI):
        pass
    
    def compare_results(cls, net1, net2):
        pass