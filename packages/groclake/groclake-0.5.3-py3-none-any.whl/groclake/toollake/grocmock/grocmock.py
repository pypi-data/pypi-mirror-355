from typing import Dict, Any
from datetime import datetime, timedelta
import numpy as np
import random

class Grocmock:
    def __init__(self, tool_config: Dict[str, Any]):
        """
        Initialize Grocmock connection with tool configuration.
        """
        self.tool_config = tool_config

    def get_duration_in_seconds(self, duration_str):
        """Convert '5 min' or '2 hour' to seconds."""
        value, unit = duration_str.strip().split()
        value = int(value)
        unit = unit.lower()
        if unit in ['sec', 'second', 'seconds']:
            return value
        elif unit in ['min', 'minute', 'minutes']:
            return value * 60
        elif unit in ['hour', 'hours']:
            return value * 3600
        elif unit in ['day', 'days']:
            return value * 86400
        else:
            raise ValueError(f"Unsupported unit: {unit}")

    def generate_grocmock_data_timeseries(self, grocmock_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate grocmock data for timeseries with anomalies.
        """
        grocmock_config = grocmock_payload.get("grocmock_config", {})
        grocmock_anomaly_type = grocmock_config.get("anomaly_type", "").lower()

        aggregation_interval = grocmock_payload.get('aggregation_interval', '1 min')
        lookback_window = grocmock_payload.get('lookback_window', '1 hour')
        y_value_min = grocmock_config.get('y_value_min', 0)
        y_value_max = grocmock_config.get('y_value_max', 100)
        y_value_mean = grocmock_config.get('y_value_mean', (y_value_min + y_value_max) / 2)
        y_value_base_data_profile = grocmock_config.get('y_value_base_data_profile', 'gaussian')
        y_value_base_data_std_dev = grocmock_config.get('y_value_base_data_std_dev', 10)

        anomaly_duration = grocmock_config.get('anomaly_duration', '1 min')
        anomaly_percentage = grocmock_config.get('anomaly_percentage', 10)

        aggregation_interval_seconds = self.get_duration_in_seconds(aggregation_interval)
        lookback_window_seconds = self.get_duration_in_seconds(lookback_window)
        anomaly_duration_seconds = self.get_duration_in_seconds(anomaly_duration)

        num_points = int(lookback_window_seconds / aggregation_interval_seconds)
        anomaly_duration_num_points = max(1, int(anomaly_duration_seconds / aggregation_interval_seconds))
        total_anomaly_points = max(1, int(anomaly_percentage * num_points / 100))
        num_anomaly_blocks = max(1, int(total_anomaly_points / anomaly_duration_num_points))

        x_value_end = grocmock_config.get('x_value_end', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end_time = datetime.strptime(x_value_end, '%Y-%m-%d %H:%M:%S') if x_value_end else datetime.now()
        start_time = end_time - timedelta(seconds=lookback_window_seconds)

        timestamps = [start_time + timedelta(seconds=i * aggregation_interval_seconds) for i in range(num_points)]

        # Generate base values
        if y_value_base_data_profile == 'gaussian':
            values = np.random.normal(loc=y_value_mean, scale=y_value_base_data_std_dev, size=num_points)
        elif y_value_base_data_profile == 'uniform':
            values = np.random.uniform(low=y_value_min, high=y_value_max, size=num_points)
        elif y_value_base_data_profile == 'sinusoidal':
            values = y_value_mean + y_value_base_data_std_dev * np.sin(np.linspace(0, 6.28, num_points))
        elif y_value_base_data_profile == 'poisson':
            values = np.random.poisson(lam=y_value_mean, size=num_points)
        else:
            raise ValueError(f"Unsupported base profile: {y_value_base_data_profile}")

        # Inject anomalies
        anomaly_indices = set()
        for _ in range(num_anomaly_blocks):
            start_idx = random.randint(0, num_points - anomaly_duration_num_points)
            for j in range(anomaly_duration_num_points):
                idx = start_idx + j
                anomaly_indices.add(idx)
                if grocmock_anomaly_type == "spike":
                    values[idx] += y_value_max * 0.5
                elif grocmock_anomaly_type == "drop":
                    values[idx] -= y_value_max * 0.5
                elif grocmock_anomaly_type == "ramp_up" and idx + anomaly_duration_num_points < num_points:
                    values[idx] += j * 2
                elif grocmock_anomaly_type == "ramp_down" and idx + anomaly_duration_num_points < num_points:
                    values[idx] -= j * 2

        # Clamp values
        values = np.clip(values, y_value_min, y_value_max)

        # Package result
        result = []
        for i in range(num_points):
            result.append({
                "x_value": timestamps[i].strftime('%Y-%m-%d %H:%M:%S'),
                "y_value": round(float(values[i]), 2),
                "ground_truth_anomaly": "true" if i in anomaly_indices else "false"
            })

        grocmock_payload['data'] = result
        grocmock_payload['status'] = "success"
        return grocmock_payload
    
    def generate_grocmock_data_snapshot(self, grocmock_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate grocmock data for snapshot with anomalies.
        """
        grocmock_config = grocmock_payload.get("grocmock_config", {})
        grocmock_anomaly_type = grocmock_config.get("grocmock_anomaly_type", "").lower()
        
        grocmock_payload['data'] = []
        return grocmock_payload
