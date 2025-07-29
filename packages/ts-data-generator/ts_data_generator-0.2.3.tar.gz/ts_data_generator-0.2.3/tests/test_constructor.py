"""
Tests for the DataGen class
"""
import random
import pytest
import pandas as pd
from ts_data_generator import DataGen
from ts_data_generator.utils.functions import random_choice, random_int
from ts_data_generator.utils.trends import SinusoidalTrend


class TestDataGenInitialization:
    # Setup method to initialize the Calculator instance
    
    @pytest.fixture
    def data_gen_instance(self):
        """Fixture to create a DataGen instance"""
        data_gen = DataGen()
        data_gen.start_datetime = "2022-01-01"
        data_gen.end_datetime = "2022-12-31"
        data_gen.granularity = "5min"
        # Create function that will return random choice from list
        data_gen.add_dimension(name="protocol", function=random_choice(["TCP", "UDP"]))
        data_gen.add_dimension(name="port", function=random_int(1, 65536))

        metric1_trend = SinusoidalTrend(name="sine", amplitude=1, freq=24, phase=0, noise_level=1)
        data_gen.add_metric(name="metric1", trends=[metric1_trend])

        return data_gen

    def test_setting_dates(self, data_gen_instance):
        """Test initialization of DataGen"""
        assert data_gen_instance.start_datetime == "2022-01-01"
        assert data_gen_instance.end_datetime == "2022-12-31"
        
    def test_dimension_protocol_values(self, data_gen_instance):
        assert data_gen_instance.dimensions["protocol"].name == "protocol"
        assert next(data_gen_instance.dimensions["protocol"].function) in ["TCP", "UDP"]
        with pytest.raises(ValueError):
            data_gen_instance.add_dimension(name="port", function="INVALID_FUNCTION")
    
    def test_granularity(self, data_gen_instance):
        assert data_gen_instance.granularity == "5min"
        with pytest.raises(ValueError):
            data_gen_instance.granularity = "invalid_granularity"
        
    def test_metric_values(self, data_gen_instance):
        assert data_gen_instance.metrics["metric1"].name == "metric1"
        assert data_gen_instance.trends['metric1']["sine"].name == "sine"
        assert data_gen_instance.trends['metric1']["sine"].amplitude == 1
        assert data_gen_instance.trends['metric1']["sine"].freq == 24
        assert data_gen_instance.trends['metric1']["sine"].phase == 0
        assert data_gen_instance.trends['metric1']["sine"].noise_level == 1
        
    def test_can_not_add_duplicate_dimension(self, data_gen_instance):
        with pytest.raises(ValueError):
            data_gen_instance.add_dimension(name="port", function=random_int(1, 65536))
