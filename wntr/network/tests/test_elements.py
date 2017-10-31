"""
Test the wntr.network.elements classes
"""
from __future__ import print_function
import nose.tools
from nose.tools import *
from os.path import abspath, dirname, join
import numpy as np
import wntr.network.elements as elements

testdir = dirname(abspath(str(__file__)))
datadir = join(testdir,'..','..','tests','networks_for_testing')
net1dir = join(testdir,'..','..','..','examples','networks')
packdir = join(testdir,'..','..','..')

def test_Curve():
    pts1 = [[3,5]]
    pts2 = [[3, 6], [7, 2], [10, 0]]
    pts3 = [[3, 6], [7, 2], [10, 1]]
    expected_str = "<Curve: 'curve2', curve_type='HEAD', points=[[3, 6], [7, 2], [10, 0]]>"
    # Create the curves
    curve1 = elements.Curve('curve1', 'PUMP', pts1)
    curve2a = elements.Curve('curve2', 'HEAD', pts2)
    curve2b = elements.Curve('curve2', 'HEAD', pts3)
    curve2c = elements.Curve('curve2', 'HEAD', pts3)
    # Test that the assignments are working
    nose.tools.assert_list_equal(curve2b.points, pts3)
    nose.tools.assert_equal(curve1.num_points, 1)
    nose.tools.assert_equal(len(curve2c), 3)
    # Testing __eq__
    nose.tools.assert_not_equal(curve1, curve2a)
    nose.tools.assert_not_equal(curve2a, curve2b)
    nose.tools.assert_equal(curve2b, curve2c)
    # testing __getitem__ and __getslice__
    nose.tools.assert_list_equal(curve2a[0], [3,6])
    nose.tools.assert_list_equal(curve2a[:2], [[3, 6], [7, 2]])
    # verify that the points are being deep copied
    nose.tools.assert_not_equal(id(curve2b.points), id(curve2c.points))
    # test __repr__ and __str__
    nose.tools.assert_equal(repr(curve2a), expected_str)
    nose.tools.assert_equal(str(curve2a), expected_str)

def test_Pattern():
    pattern_points1 = [1, 2, 3, 4, 3, 2, 1]
    pattern_points2 = [1.0, 1.2, 1.0 ]
    pattern_points3 = 3.2
    
    # test constant pattern creation
    pattern1a = elements.Pattern('constant', multipliers=pattern_points3)
    pattern1b = elements.Pattern('constant', multipliers=[pattern_points3])
    nose.tools.assert_list_equal(pattern1a.multipliers.tolist(), [pattern_points3])
    nose.tools.assert_true(np.all(pattern1a.multipliers == pattern1b.multipliers))
    nose.tools.assert_false(id(pattern1a.multipliers) == id(pattern1b.multipliers))
    nose.tools.assert_equal(pattern1a, pattern1b)
    
    # def multipliers setter
    pattern2a = elements.Pattern('oops', multipliers=pattern_points3, step_size=5)
    pattern2b = elements.Pattern('oops', multipliers=pattern_points1, step_size=5)
    pattern2a.multipliers = pattern_points1
    nose.tools.assert_equal(pattern2a, pattern2b)
    
    # test pattern evaluations
    expected_value = pattern_points1[2]
    nose.tools.assert_equal(pattern2a[2], expected_value)
    nose.tools.assert_equal(pattern2b.at(10), expected_value)
    nose.tools.assert_equal(pattern2b.at(12.5), expected_value)
    nose.tools.assert_equal(pattern2b(14), expected_value)
    nose.tools.assert_equal(pattern2b(9*5), expected_value)
    nose.tools.assert_not_equal(pattern2b.at(15), expected_value)
    
    pattern3 = elements.Pattern('nowrap', multipliers=pattern_points2, step_size=100, wrap=False)
    nose.tools.assert_equal(pattern3[5], 0.0)
    nose.tools.assert_equal(pattern3[-39], 0.0)
    nose.tools.assert_equal(pattern3(-39), 0.0)
    nose.tools.assert_equal(pattern3.at(50), 1.0)
    
    pattern4 = elements.Pattern('constant')
    nose.tools.assert_equal(len(pattern4), 0)
    nose.tools.assert_equal(pattern4(492), 1.0)
    
    pattern5a = elements.Pattern('binary', [0,0,1,1,1,1,0,0,0], wrap=False)
    pattern5b = elements.Pattern.BinaryPattern('binary', step_size=1, start_time=2, end_time=6, duration=9)
    nose.tools.assert_equals(pattern5a, pattern5b)
    nose.tools.assert_raises(NotImplementedError, elements.Pattern._SquareWave, *(None, None, None, None, None))

def test_TimeSeries():
    pattern_points2 = [1.0, 1.2, 1.0 ]
    pattern2 = elements.Pattern('oops', multipliers=pattern_points2, step_size=10)
    pattern5 = elements.Pattern.BinaryPattern('binary', step_size=1, start_time=2, end_time=6, duration=9)
    base1 = 2.0
    
    # test constructor and setters, getters
    tvv1 = elements.TimeSeries(base1, None, None)
    tvv2 = elements.TimeSeries(base1, pattern2, 'tvv2')
    nose.tools.assert_raises(ValueError, elements.TimeSeries, *('A', None, None))
    nose.tools.assert_raises(ValueError, elements.TimeSeries, *(1.0, 'A', None))
    nose.tools.assert_equals(tvv1._base, base1)
    nose.tools.assert_equal(tvv1.base_value, tvv1._base)
    nose.tools.assert_equals(tvv1.pattern_name, None)
    nose.tools.assert_equals(tvv1.pattern, None)
    nose.tools.assert_equals(tvv1.category, None)
    tvv1.set_base_value(3.0)
    nose.tools.assert_equals(tvv1.base_value, 3.0)
    tvv1.set_pattern(pattern5)
    nose.tools.assert_equals(tvv1.pattern_name, 'binary')
    tvv1.set_category('binary')
    nose.tools.assert_equals(tvv1.category, 'binary')
    
    # Test getitem
    nose.tools.assert_equals(tvv1[1], 0.0)
    nose.tools.assert_equals(tvv1[2], 3.0)
    nose.tools.assert_equals(tvv2[1], 2.4)
    nose.tools.assert_equals(tvv2(16), 2.4)
    
    price1 = elements.TimeSeries(base=35.0, pattern=None, category="base")
    price2 = elements.TimeSeries(base=35.0, pattern=None, category="base")
    nose.tools.assert_equal(price1, price2)
    nose.tools.assert_equal(price1.base_value, 35.0)
    nose.tools.assert_equal(price1.category, 'base')
    
    speed1 = elements.TimeSeries(base=35.0, pattern=pattern5, category="base")
    speed2 = elements.TimeSeries(base=35.0, pattern=pattern5, category="base")
    nose.tools.assert_equal(speed1, speed2)
    nose.tools.assert_equal(speed1.base_value, 35.0)
    nose.tools.assert_equal(speed1.category, 'base')
    
    head1 = elements.TimeSeries(base=35.0, pattern=pattern2, category="base")
    head2 = elements.TimeSeries(base=35.0, pattern=pattern2, category="base")
    nose.tools.assert_equal(head1, head2)
    nose.tools.assert_equal(head1.base_value, 35.0)
    nose.tools.assert_equal(head1.category, 'base')

    demand1 = elements.TimeSeries(base=1.35, pattern=pattern2, category="base")
    demand2 = elements.TimeSeries(base=1.35, pattern=pattern2, category="base")
    nose.tools.assert_equal(demand1, demand2)
    nose.tools.assert_equal(demand1.base_value, 1.35)
    nose.tools.assert_equal(demand1.category, 'base')
    expected_values1 = np.array([1.35, 1.62, 1.35, 1.35, 1.62])
    demand_values1 = demand2.get_values(0, 40, 10)
    nose.tools.assert_true(np.all(np.abs(expected_values1-demand_values1)<1.0e-10))
    expected_values1 = np.array([1.35, 1.35, 1.62, 1.62, 1.35, 1.35, 1.35, 1.35, 1.62])
    demand_values1 = demand2.get_values(0, 40, 5)
    nose.tools.assert_true(np.all(np.abs(expected_values1-demand_values1)<1.0e-10))
    
    source1 = elements.Source('source1', 'NODE-1131', 'CONCEN', 1000.0, pattern5)
    source2 = elements.Source('source1', 'NODE-1131', 'CONCEN', 1000.0, pattern5)
    nose.tools.assert_equal(source1, source2)
    nose.tools.assert_equal(source1.quality, 1000.0)
    

def test_Demands():
    pattern_points1 = [0.5, 1.0, 0.4, 0.2 ]
    pattern1 = elements.Pattern('1', multipliers=pattern_points1, step_size=10)
    pattern_points2 = [1.0, 1.2, 1.0 ]
    pattern2 = elements.Pattern('2', multipliers=pattern_points2, step_size=10)
    demand1 = elements.TimeSeries( 2.5, pattern1, '_base_demand')
    demand2 = elements.TimeSeries( 1.0, pattern2, 'residential')
    demand3 = elements.TimeSeries( 0.8, pattern2, 'residential')
    expected1 = 2.5 * np.array(pattern_points1*3)
    expected2 = 1.0 * np.array(pattern_points2*4)
    expected3 = 0.8 * np.array(pattern_points2*4)
    expectedtotal = expected1 + expected2 + expected3
    expectedresidential = expected2 + expected3
    demandlist1 = elements.Demands( demand1, demand2, demand3 )
    demandlist2 = elements.Demands()
    demandlist2.append(demand1)
    demandlist2.append(demand1)
    demandlist2[1] = demand2
    demandlist2.append((0.8, pattern2, 'residential'))
    nose.tools.assert_list_equal(list(demandlist1), list(demandlist2))
    demandlist2.extend(demandlist1)
    nose.tools.assert_equal(len(demandlist1), 3)
    nose.tools.assert_equal(len(demandlist2), 6)
    del demandlist2[3]
    del demandlist2[3]
    del demandlist2[3]
    del demandlist2[0]
    demandlist2.insert(0, demand1)
    nose.tools.assert_list_equal(list(demandlist1), list(demandlist2))
    demandlist2.clear()
    nose.tools.assert_equal(len(demandlist2), 0)
    nose.tools.assert_false(demandlist2)
    nose.tools.assert_equal(demandlist1.at(5), expectedtotal[0])
    nose.tools.assert_equal(demandlist1.at(13), expectedtotal[1])
    nose.tools.assert_equal(demandlist1.at(13, 'residential'), expectedresidential[1])
    nose.tools.assert_true(np.all(np.abs(demandlist1.get_values(0,110,10)-expectedtotal)<1.0e-10))
    nose.tools.assert_list_equal(demandlist1.base_demand_list(), [2.5, 1.0, 0.8])
    nose.tools.assert_list_equal(demandlist1.base_demand_list('_base_demand'), [2.5])
    nose.tools.assert_list_equal(demandlist1.pattern_list(), [pattern1, pattern2, pattern2])
    nose.tools.assert_list_equal(demandlist1.pattern_list(category='residential'), [pattern2, pattern2])
    nose.tools.assert_list_equal(demandlist1.category_list(), ['_base_demand','residential','residential'])    
    

def test_Enums():
    pass


if __name__ == '__main__':
    test_Curve()
    test_Pattern()
    test_TimeSeries()
    test_Demands()
    test_Enums()