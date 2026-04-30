# Do simple test of the epanet stepwise simulator.

import unittest
from os.path import abspath, dirname, join
import wntr
import pandas as pd
import numpy as np
import wntr.extensions.stepwise_simulator

TEST_DIR = dirname(abspath(__file__))
DATA_DIR = join(TEST_DIR, "..", "..", "..", "examples", "networks")


class TestEpanetSimulatorStep(unittest.TestCase):
    """EPANET Stepwise simulator testing."""

    def test_run(self):
        """Test forward run using `with ... sim`, `for ... in sim` paradigm"""
        inp_file = join(DATA_DIR, "Net3.inp")
        # inp_file = join(datadir, "Net6.inp")
        wn = wntr.network.WaterNetworkModel(inp_file)
        wn.options.time.hydraulic_timestep = 600
        wn.options.time.report_timestep = 600
        wn.options.time.duration = 24 * 3600
        wn.options.quality.parameter = "AGE"
        res = []
        
        ## Add test to compare to just a forward run

        # Open the stepwise simulator using a context manager
        with wntr.extensions.stepwise_simulator.StepwiseEpanetSimulator().open(wn) as sim:
            sim.add_node_sensor("20") # Set the read-only settings on the model object (wn)

            # Manually check any arbitrary value.
            res.append(
                (sim.current_time, sim.get_node_value("20", "head") * 0.3048)
            )

            # Do the step through the simulation
            for step in sim:
                # Manually check any arbitrary value
                res.append(
                    (sim.current_time, sim.get_node_value("20", "head") * 0.3048)
                )
                
                # Put a test in to check that sim._wn.nodes['20'].head was updated
        
        # Get the results from the simulation (for all nodes/times)
        res2 = sim.get_results()

        # Read the EPANET output file to compare results
        results = wntr.epanet.io.BinFile().read("temp.bin")
        self.assertLessEqual(
            np.nanmean(
                (
                    results.node["head"].loc[:, "20"]
                    - pd.DataFrame.from_records(res, columns=["ts", "head"])
                    .set_index("ts")
                    .T
                ).T.abs()
            ),
            1.0e-3,
            "Average head error greater than 1 mm!",
        )
        diff = (res2.node['head'] - results.node['head']).abs()
        self.assertLessEqual(np.nanmax(diff), 1.0e-3, 'Average head error greater than 1 mm!')


    def test_breakpoint(self):
        """Test breaking at specified point within the run rather"""
        inp_file = join(DATA_DIR, "Net3.inp")
        # inp_file = join(datadir, "Net6.inp")
        wn = wntr.network.WaterNetworkModel(inp_file)
        wn.options.time.hydraulic_timestep = 600
        wn.options.time.duration = 24 * 3600
        wn.options.quality.parameter = "AGE"
        res = []
        
        with wntr.extensions.stepwise_simulator.StepwiseEpanetSimulator().open(wn) as sim:
            # Add a breakpoint at time 7200
            sim.add_node_sensor("20")
            sim.set_breakpoint(7200)

            # Run until breakpoint
            step = sim.continue_run()
            res.append((sim.current_time, sim.get_node_value("20", "head") * 0.3048))

            for step in sim:
                res.append((sim.current_time, sim.get_node_value("20", "head") * 0.3048))

        results = wntr.epanet.io.BinFile().read("temp.bin")
        self.assertLessEqual(
            np.nanmean(
                (
                    results.node["head"].loc[:, "20"]
                    - pd.DataFrame.from_records(res, columns=["ts", "head"])
                    .set_index("ts")
                    .T
                ).T.abs()
            ),
            1.0e-3,
            "Average head error greater than 1 mm!",
        )


if __name__ == "__main__":
    unittest.main()
