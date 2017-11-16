"""
The wntr.metrics.water_security module contains water security metrics.
"""
import numpy as np
import wntr.network
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def mass_contaminant_consumed(node_results):
    """ Mass of contaminant consumed, equation from [1].
    
    Parameters
    ----------
    node_results : pd.Panel
        A pandas Panel containing node results. 
        Items axis = attributes, Major axis = times, Minor axis = node names
        Mass of contaminant consumed uses 'demand' and quality' attrbutes.
    
     References
    ----------
    [1] EPA, U. S. (2015). Water security toolkit user manual version 1.3. 
    Technical report, U.S. Environmental Protection Agency
    """
    maskD = np.greater(node_results['demand'], 0) # positive demand
    deltaT = node_results['quality'].index[1] # this assumes constant timedelta
    MC = node_results['demand']*deltaT*node_results['quality']*maskD # m3/s * s * kg/m3 - > kg
    
    return MC
     
def volume_contaminant_consumed(node_results, detection_limit):
    """ Volume of contaminant consumed, equation from [1].
    
    Parameters
    ----------
    node_results : pd.Panel
        A pandas Panel containing node results. 
        Items axis = attributes, Major axis = times, Minor axis = node names
        Volume of contaminant consumed uses 'demand' and quality' attrbutes.
    
    detection_limit : float
        Contaminant detection limit
    
     References
    ----------
    [1] EPA, U. S. (2015). Water security toolkit user manual version 1.3. 
    Technical report, U.S. Environmental Protection Agency
    """
    maskQ = np.greater(node_results['quality'], detection_limit)
    maskD = np.greater(node_results['demand'], 0) # positive demand
    deltaT = node_results['quality'].index[1] # this assumes constant timedelta
    VC = node_results['demand']*deltaT*maskQ*maskD # m3/s * s * bool - > m3
    
    return VC
    

def extent_contamination_indirect(node_quality, flow_rate, 
                                  link_names, link_start_node, link_end_node, link_length, 
                                  detection_limit=0.0):
    r"""Extent of contamination calculated based on node quality and flow information.
    
    Calculate the extent of total contamination (in meters) as the sum of the length of pipes
    that have incoming water quality greater than some detection limit. This is equivalent to
    Equation 4.5 in [1].
    
    The maximum pipe concentration, :math:`Q` ,
    and extent of contamination, :math:`EC` , are defined as
    
    .. math::
        
        \begin{eqnarray}
            Q_{m,t_i} &=& \max_{0 \le j \le i} \tilde{C}_{m,t_j} 
                         \text{ where } \tilde{C}_{m,t_j} = \left\{ 
                         \begin{array}{ll} 
                             {C}_{x,t_j} & \text{if }F_{m,t_j} > 0 \\ 
                             {C}_{y,t_j} & \text{if }F_{m,t_j} < 0 \\ 
                             0 & \text{otherwise} 
                         \end{array} \right. \\
            EC_{t_i} &=& \sum_{m=1}^{M} L_{m} \delta_{m,t_i} 
                         \text{ where } \delta_{m,t_i} = \left\{ 
                         \begin{array}{ll}
                                 1 & \text{if } Q_{m,t_i} > \text{ detection limit} \\ 
                                 0 & \text{otherwise} 
                         \end{array} \right.
        \end{eqnarray}
    

    where :math:`t_i` is the time at simulation step :math:`i` ,
    :math:`x` is the start node of link :math:`m` ,
    :math:`y` is the end node of link :math:`m` ,
    :math:`F_{m,t_i}` is the flow through pipe :math:`m` at time step :math:`t_i` ,
    :math:`{C}_{n,t_j}` is the concentration at node :math:`n` at time step :math:`t_j` ,
    :math:`M` is the number of links, and 
    :math:`L_m` is the length of link :math:`m` .


    Parameters
    ----------
    node_quality : pandas.DataFrame
    flow_rate : pandas.DataFrame
    link_length : pandas.Series
    link_names : pandas.Series
    link_start_node : pandas.Series
    link_end_node : pandas.Series
    detection_limit : float
        the concentration at which water is considered contaminated


    Returns
    -------
    pandas.Series
        the EC for each time in the results


    References
    ----------
    [1] EPA, U. S. (2015). Water security toolkit user manual version 1.3. 
    Technical report, U.S. Environmental Protection Agency
    """
#    if not isinstance(results, NetResults):
#        raise ValueError('results must be a NetResults object')
#    flow_dir = np.sign(results.link['flowrate'].loc[:,results.meta['link_names']])
#    node_contam = results.node['quality'] > detection_limit
#    pos_flow = np.array(node_contam.loc[:,results.meta['link_start']])
#    neg_flow = np.array(node_contam.loc[:,results.meta['link_end']])
    flow_dir = np.sign(flow_rate.loc[:,link_names])
    node_contam = node_quality > detection_limit
    pos_flow = np.array(node_contam.loc[:,link_start_node])
    neg_flow = np.array(node_contam.loc[:,link_end_node])
    link_contam = ((flow_dir>0)&pos_flow) | ((flow_dir<0)&neg_flow)
#    contam_len = (link_contam * results.meta['link_length']).cummax()
    contam_len = (link_contam * link_length).cummax()
    ec = contam_len.sum(axis=1)
    return ec


def extent_contamination_direct(link_quality, link_length, detection_limit=0.0):
    r"""Extent of contamination calculated based directly on link quality.
    
    Calculate the extent of total contamination (in meters) as the sum of the length of pipes
    that have an average water quality greater than some detection limit. This is a modification
    of Equation 4.5 in [1] where link qualities were calculated and stored.
    
    The extent of contamination is defined as
    
    .. math::
        
        \begin{eqnarray}    
                Q_{m,t_i} &=& \max\limits_{0 \le j \le i} \bar{C}_{m,t_j} \\
                EC_{t_i} &=& \sum_{m=1}^{M} L_{m} \delta_{m,t_i} 
                   \text{ where } \delta_{m,t_i} = \left\{ 
                   \begin{array}{ll}
                        1 & \text{if } Q_{m,t_i} > \text{ detection limit} \\ 
                        0 & \text{otherwise} 
                   \end{array} \right.
        \end{eqnarray}
    

    where :math:`t_i` is the time at simulation step :math:`i` , :math:`\bar{C}_{m,t_j}`
    is the average concentration within pipe :math:`m` at time :math:`t_j` , :math:`M` is 
    the number of links and :math:`L_m` is the length of link :math:`m` .
    
    

    Parameters
    ----------
    link_quality : pandas.DataFrame
        link quality results
    link_length : pandas.Series
        link lengths
    detection_limit : float
        the concentration at which water is considered contaminated


    Returns
    -------
    pandas.Series
        the EC for each time in the results


    References
    ----------
    [1] EPA, U. S. (2015). Water security toolkit user manual version 1.3. 
    Technical report, U.S. Environmental Protection Agency
    """
#    if not isinstance(results, NetResults):
#        raise ValueError('results must be a NetResults object')
#    link_contam = results.link['linkquality'] > detection_limit
#    contam_len = (link_contam * results.meta['link_length']).cummax()
    link_contam = link_quality > detection_limit
    contam_len = (link_contam * link_length).cummax()
    ec = contam_len.sum(axis=1)
    return ec



def extent_contaminant(node_results, link_results, wn, detection_limit):
#    r""" Extent of contaminant in the pipes, equation from [1].
#
#    .. math::
#        \begin{eqnarray}
#        EC_{t'_i} &=& \sum_{n=1}^N L_{n,t'_i} \delta_{n,t'_i} \text{ where } \delta_{n,t'_i} = \left\{ \begin{array}{ll}1 & \text{if }C_{n,t'_i} > \text{ detection limit} \\ 0 & \text{otherwise} \end{array} \right. \\
#        \end{eqnarray}
#    
#    
#    Parameters
#    ----------
#    node_results : pd.Panel
#        A pandas Panel containing node results. 
#        Items axis = attributes, Major axis = times, Minor axis = node names
#        Extent of contamination uses the 'quality' attribute.
#    
#    link_results : pd.Panel
#        
#    detection_limit : float
#        Contaminant detection limit.
#    
#    Returns
#    -------
#    EC : pd.Series
#        Extent of contaminantion (m)
#    
#     References
#    ----------
#    [1] EPA, U. S. (2015). Water security toolkit user manual version 1.3. 
#    Technical report, U.S. Environmental Protection Agency
#    """
    G = wn.get_graph_deep_copy()
    EC = pd.DataFrame(index = node_results['quality'].index, columns = node_results['quality'].columns, data = 0)
    L = pd.DataFrame(index = node_results['quality'].index, columns = node_results['quality'].columns, data = 0)

    for t in node_results['quality'].index:
        # Weight the graph
        attr = link_results['flowrate'].loc[t, :]   
        G.weight_graph(link_attribute=attr)  
        
        # Compute pipe_length associated with each node at time t
        for node_name in G.nodes():
            for downstream_node in G.successors(node_name):
                for link_name in G[node_name][downstream_node].keys():
                    link = wn.get_link(link_name)
                    if isinstance(link, wntr.network.Pipe):
                        L.loc[t,node_name] = L.loc[t,node_name] + link.length
                    
    mask = np.greater(node_results['quality'], detection_limit)
    EC = L*mask
        
    #total_length = [link.length for link_name, link in wn.links(wntr.network.Pipe)]
    #sum(total_length)
    #L.sum(axis=1)
        
    return EC
    
#def cumulative_dose():
#    """
#    Compute cumulative dose for person p at node n at time step t
#    """
#    d_npt = 0
#    return d_npt
#
#def ingestion_model_timing(node_results, method='D24'):
#    """
#    Compute volume of water ingested for each node and timestep, equations from [1]
#   
#    Parameters
#    -----------
#    wn : WaterNetworkModel
#    
#    method : string
#        Options = D24, F5, and P5
#        
#    Returns
#    -------
#    Vnpt : pd.Series
#        A pandas Series that contains the volume of water ingested for each node and timestep
#        
#    References
#    ----------
#    [1] EPA, U. S. (2015). Water security toolkit user manual version 1.3. 
#    Technical report, U.S. Environmental Protection Agency
#    """
#    if method == 'D24':
#        Vnpt = 1
#    elif method == 'F5':
#        Vnpt = 1
#    elif method == 'P5':
#        Vnpt = 1
#    else:
#        logger.warning('Invalid ingestion timing model')
#        return
#    
#    return Vnpt
#    
#def ingestion_model_volume(method ='M'):
#    """
#    Compute per capita ingestion volume in m3/s for each person p at node n.
#    """
#    
#    if method == 'M':
#        Vnp = 1
#    elif method == 'P':
#        Vnp = 1 # draw from a distribution, for each person at each node
#    else:
#        logger.warning('Invalid ingestion volume model')
#        return
#
#    return Vnp
#  
#def population_dosed(node_results):
#    PD = 0
#    return PD
#
#def population_exposed(node_results):
#    PE = 0
#    return PE
#
#def population_killed(node_results):
#    PK = 0
#    return PK
