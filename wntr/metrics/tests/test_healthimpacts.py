from __future__ import print_function
from nose.tools import *
from nose import SkipTest
from os.path import abspath, dirname, join
import wntr

testdir = dirname(abspath(str(__file__)))
datadir = join(testdir,'..','..','tests','networks_for_testing')
net3dir = join(testdir,'..','..','..','examples','networks')
packdir = join(testdir,'..','..','..')

def test_average_water_consumed_net3_node101():
    inp_file = join(net3dir,'Net3.inp')
    wn = wntr.network.WaterNetworkModel(inp_file)
    qbar = wntr.metrics.average_water_consumed(wn)
    expected = 0.012813608
    error = abs((qbar['101'] - expected)/expected)
    assert_less(error, 0.01) # 1% error

def test_population_net6():
    inp_file = join(net3dir,'Net6.inp')
    wn = wntr.network.WaterNetworkModel(inp_file)
    pop = wntr.metrics.population(wn)
    expected = 152000
    error = abs((pop.sum() - expected)/expected)
    assert_less(error, 0.01) # 1% error

"""
Compare the following results to WST impact files using TSG file
121          SETPOINT      100000          0                86400
"""
def test_mass_consumed():
    inp_file = join(net3dir,'Net3.inp')

    wn = wntr.network.WaterNetworkModel(inp_file)

    wn.options.quality.mode = 'CHEMICAL'
    wn.options.hydraulic.units = 'LPS'
    newpat = wntr.network.elements.Pattern.BinaryPattern('NewPattern', 0, 24*3600, wn.options.time.pattern_timestep, wn.options.time.duration)
    wn.add_pattern(newpat.name, newpat)
    
    wn.add_source('Source1', '121', 'SETPOINT', 100, 'NewPattern')
    #WQ = wntr.scenario.Waterquality('CHEM', ['121'], 'SETPOINT', 100, 0, 24*3600)

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    junctions = [junction_name for junction_name, junction in wn.junctions()]
    node_results = {} #results.node #.loc[:, :, junctions]
    node_results['quality'] = results.node['quality'].loc[:, junctions]
    node_results['demand'] = results.node['demand'].loc[:, junctions]
    MC = wntr.metrics.mass_contaminant_consumed(node_results)
    MC_timeseries = MC.sum(axis=1)
    MC_cumsum = MC_timeseries.cumsum()
    #MC_timeseries.to_csv('MC.txt')

    expected = float(39069900000/1000000) # hour 2
    error = abs((MC_cumsum[2*3600] - expected)/expected)
    # print(MC_cumsum[900], expected, error)
    assert_less(error, 0.01) # 1% error

    expected = float(1509440000000/1000000) # hour 12
    error = abs((MC_cumsum[12*3600] - expected)/expected)
    # print(MC_cumsum[12*3600], expected, error)
    assert_less(error, 0.01) # 1% error

def test_volume_consumed():
    """
    TODO: Volume consumed - get better (more accurate) numbers from the WST simulations and make sure
    the time settings were the same
    """

    inp_file = join(net3dir,'Net3.inp')

    wn = wntr.network.WaterNetworkModel(inp_file)
    
    wn.options.quality.mode = 'CHEMICAL'
    newpat = wntr.network.elements.Pattern.BinaryPattern('NewPattern', 0, 24*3600, wn.options.time.pattern_timestep, wn.options.time.duration)
    wn.add_pattern(newpat.name, newpat)
    wn.add_source('Source1', '121', 'SETPOINT', 100, 'NewPattern')
    #WQ = wntr.scenario.Waterquality('CHEM', ['121'], 'SETPOINT', 100, 0, 24*3600)

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    junctions = [junction_name for junction_name, junction in wn.junctions()]
    node_results = results.node.loc[:, :, junctions]

    VC = wntr.metrics.volume_contaminant_consumed(node_results, 0)
    VC_timeseries = VC.sum(axis=1)
    VC_cumsum = VC_timeseries.cumsum()
    #VC_timeseries.to_csv('VC.txt')

    expected = float(156760/264.172) # hour 2
    error = abs((VC_cumsum[2*3600] - expected)/expected)
    print(VC_cumsum[2*3600], expected, error)
    assert_less(error, 0.02) # 1% error

    expected = float(4867920/264.172) # hour 12
    error = abs((VC_cumsum[12*3600] - expected)/expected)
    print(VC_cumsum[12*3600], expected, error)
    assert_less(error, 0.02) # 1% error

def test_extent_contaminated():
    """Test the extent of contamination metrics.
    
    Compare extent_contamination_indirect against WST results.
    Compare extent_contamination_direct against indirect results for overall matching.
    Methods will not be exact matches at all timesteps as they use different methods.
    
    """

    inp_file = join(net3dir,'Net3.inp')

    wn = wntr.network.WaterNetworkModel(inp_file)
    
    wn.options.quality.mode = 'CHEMICAL'
    newpat = wntr.network.elements.Pattern.BinaryPattern('NewPattern', 0, 24*3600, wn.options.time.pattern_timestep, wn.options.time.duration)
    wn.add_pattern(newpat.name, newpat)
    wn.add_source('Source1', '121', 'SETPOINT', 100, 'NewPattern')
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()


    fun = wntr.metrics.water_security.extent_contamination_indirect
    ECi = fun(results.node['quality'], results.link['flowrate'], results.meta['link_names'],
             results.meta['link_start'], results.meta['link_end'], results.meta['link_length'],
             detection_limit=0)
    expected = float(80749.9) # hour 2
    errori2 = abs((ECi[2*3600] - expected)/expected)
    assert_less(errori2, 0.001) # 0.1% error
    expected = float(135554.0) # hour 12
    errori12 = abs((ECi[12*3600] - expected)/expected)
    assert_less(errori12, 0.001) # 0.1% error

    # Check direct method for similar results to indirect (WST/TEVASIM) method
    fun = wntr.metrics.water_security.extent_contamination_direct
    ECd = fun(results.link['linkquality'], results.meta['link_length'], detection_limit=0)
    assert_less(sum(abs(ECi-ECd))/sum(ECi), 0.005)  # 0.5% difference average
    assert_less((abs(ECi.iloc[-1]-ECd.iloc[-1]))/(ECi.iloc[-1]), 0.00005)  # 0.0005% difference in final value


if __name__ == '__main__':
    test_mass_consumed()
    test_volume_consumed()
    test_extent_contaminated()
