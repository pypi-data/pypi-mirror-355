"""
Core DataGen class implementation
"""

import json
from datetime import datetime
from itertools import chain, cycle
from typing import Generator, List, Literal, Optional, Set, Union

import pandas as pd

from .schema.models import AggregationType, Dimensions, Granularity, Metrics, MultiItems
from .utils.functions import constant
from .utils.trends import Trends


class DataGen:
    """Main class for generating synthetic data"""

    def __init__(
        self,
        dimensions: List[Dimensions] = None,
        metrics: List[Metrics] = None,
        multi_items: List[MultiItems] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        granularity: Granularity = Granularity.FIVE_MIN,
    ):
        """Initialize DataGen with empty data"""

        self._dimensions = dimensions or []  # Initialize to an empty set if None
        self._metrics = metrics or []  # Initialize to an empty set if None
        self._multi_items = multi_items or []
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._granularity = granularity
        self._scale_factors = {}
        self.metric_data = pd.DataFrame()
        self.dimension_data = pd.DataFrame()
        self.multi_item_data = pd.DataFrame()
        self.data = pd.DataFrame()

    def __repr__(self):
        repr_string = "DataGen Class\n"
        repr_string += "  dimensions    = [\n"
        for d in self._dimensions:
            repr_string += " " * 20 + json.dumps(d.to_json()) + "\n"
        repr_string += "                  ]\n"
        repr_string += "  metrics       = [\n"
        for d in self._metrics:
            repr_string += " " * 20 + json.dumps(d.to_json()) + "\n"
        repr_string += "                  ]\n"
        repr_string += "  multi_items   = [\n"
        for d in self._multi_items:
            repr_string += " " * 20 + json.dumps(d.to_json()) + "\n"
        repr_string += "                  ]\n"
        repr_string += f"  start         = {self.start_datetime}\n"
        repr_string += f"  end           = {self.end_datetime}\n"
        repr_string += f"  granularity   = {Granularity(self.granularity).name}"
        return repr_string

    def __len__(self):
        return len(self.data)

    def shape(self):
        return self.data.shape

    def head(self, n: int = 5):
        return self.data.head(n=n)

    def tail(self, n: int = 5):
        return self.data.tail(n=n)
    
    def to_granularity(self, granularity: Granularity):
        """
        Sets the granularity of the data to the specified value.

        Args:
            granularity (str): The desired granularity . "s", "min", "5min", "h", "D", "W", "M", "Y".
        """

        self.granularity = Granularity(granularity)

    @property
    def start_datetime(self):
        return self._start_datetime

    @start_datetime.setter
    def start_datetime(self, value: str):
        """Set start_datetime and validate it.

        Args:
            value (str): Start date in ISO format (YYYY-MM-DD).
        """
        if value is not None:
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Dates must be in ISO format (YYYY-MM-DD)")
        self._start_datetime = value
        if self._start_datetime and self._end_datetime:
            self._generate_data()

    @property
    def end_datetime(self):
        return self._end_datetime

    @end_datetime.setter
    def end_datetime(self, value: str):
        """Set end_datetime and validate it.

        Args:
            value (str): End date in ISO format (YYYY-MM-DD).
        """
        if value is not None:
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Dates must be in ISO format (YYYY-MM-DD)")
        self._end_datetime = value
        if self._start_datetime and self._end_datetime:
            self._generate_data()

    @property
    def granularity(self):
        if isinstance(self._granularity, Granularity):
            return self._granularity.value
        return self._granularity

    @granularity.setter
    def granularity(self, value: Granularity):
        """Set granularity and validate it.

        Args:
            value (str): Granularity in "5min", "H", "D".
        """
        if value is not None:
            try:
                Granularity(value)
            except ValueError:
                raise ValueError("Granularity must be one of 's', 'min', '5min', 'h', 'D', 'W', 'M', 'Y'")
        self._granularity = value
        self._generate_data()

    @property
    def dimensions(self):
        return {
            name: d
            for d in self._dimensions
            for name in ([d.name] if isinstance(d.name, str) else d.name)
        }

    @property
    def multi_items(self):
        return {
            ",".join(names): mt
            for mt in self._multi_items
            for names in ([mt.names] if isinstance(mt.names, list) else mt.names)
        }

    @property
    def metrics(self):
        return {m.name: m for m in self._metrics}

    @property
    def trends(self):
        return {m.name: {t.name: t for t in m._trends} for m in self._metrics}

    def _validate_dates(self) -> None:
        """Validate start_datetime and end_datetime format and logic.

        Raises:
            ValueError: If dates are invalid or start_datetime is after end_datetime
        """
        if not self.start_datetime:
            raise ValueError("start_datetime must be set")

        if not self.end_datetime:
            raise ValueError("end_datetime must be set")

        if (self.start_datetime is None) != (self.end_datetime is None):
            raise ValueError(
                "Both start_datetime and end_datetime must be either set or None"
            )

        start = datetime.fromisoformat(self.start_datetime)
        end = datetime.fromisoformat(self.end_datetime)

        if start > end:
            raise ValueError("start_datetime cannot be after end_datetime")

    def add_dimension(
        self, name: str, function: Union[int, float, str, list, Generator]
    ) -> None:
        """
        Add a new dimension to the collection.

        A dimension represents an additional attribute or aspect of the dataset. Each dimension is
        identified by a unique name and associated with a function that generates its values.

        Args:
            name (str): The unique name of the dimension.
            function (int | float | str | Generator): A callable (e.g., generator function) that produces values for the dimension.

        Raises:
            ValueError: If a dimension with the same name already exists in the collection.

        Example:
            >>> def sample_generator():
            ...     while True:
            ...         yield "sample_value"
            ...
            >>> my_object.add_dimension(name="category", function=sample_generator())
        """
        # validate the function
        if not isinstance(function, Union[int, float, str, list, Generator]):
            raise ValueError(
                f"Function of the dimension {name} has to be int, float, str or generator object"
            )

        if isinstance(function, Union[int, float, str]):
            function = constant(function)

        if isinstance(function, list):
            if not function:  # if empty list
                raise IndexError
            function = cycle(function)

        dimension = Dimensions(name=name, function=function)

        if dimension in self._dimensions:
            raise ValueError(f"Dimension with name {dimension.name} already exists")

        self._dimensions.append(dimension)
        # Raise error if self._dimensions already contains a dimension with the same name

        self._generate_data()

    def update_dimension(self, name: str, function) -> None:
        """
        Update an existing dimension in the DataGen instance.

        Allows updating the function associated with a dimension. The dimension is identified by its name.

        Args:
            name (str): The unique name of the dimension to update.
            function (int | str | Generator): int or string or callable (e.g., generator function) that produces values for the dimension.
                If None, the function will remain unchanged.

        Raises:
            ValueError: If the dimension with the specified name does not exist.
            ValueError: If the provided function is not a callable object.

        Example:
            ```python
            # Updating an existing dimension
            def new_generator():
                while True:
                    yield "new_value"

            data_gen.update_dimension(name="category", function=new_generator())
            ```
        """
        if name not in self.dimensions:
            raise ValueError(f"Dimension with name '{name}' does not exist.")

        dimension = self.dimensions[name]

        if function is not None:
            if (
                not isinstance(function, Generator)
                and not isinstance(function, int)
                and not isinstance(function, str)
                and not isinstance(function, float)
            ):
                raise ValueError(
                    "Provided function must be callable or int or float or string."
                )
            dimension.function = function

    def remove_dimension(self, name: str) -> None:
        """
        Remove the dimension from the data generator by its name

        Args:
            name (str): The name of the dimension to remove.

        Raises:
            ValueError: If the dimension with the specified name does not exist.

        Example:
            ```python
            data_gen.remove_dimension(name="category")
            ```
        """
        if name in self.dimensions:
            # update the data
            self.data = self.data.drop([name], axis=1)

        # drop the dimension from dimension list
        self._dimensions = [d for d in self._dimensions if d.name != name]

    def add_multi_items(
        self,
        names: list,
        function: Union[int, float, str, list, Generator],
        aggregation_type: Optional[List] = None,
    ) -> None:
        """
        Add a new dimension to the collection.

        A dimension represents an additional attribute or aspect of the dataset. Each dimension is
        identified by a unique name and associated with a function that generates its values.

        Args:
            names (list): The list of names of the items (dimension or metric).
            function (int | float | str | Generator): A callable (e.g., generator function) that produces values for the items.
                                                    Should return the same number of values as the items
            aggregation_type (Optional[List]): The aggregation type for the multi-item. Must be one of ["mean", "sum", "min", "max"]. Item will be treaded as a metric if provided.

        Raises:
            ValueError: If a dimension with the same name already exists in the collection.

        Example:
            >>> def sample_generator():
            ...     while True:
            ...         yield ("sample_value", "another_value")
            ...
            >>> my_object.add_multi_items(names=["category"], function=sample_generator(), aggregation_type=["mean"])
        """
        # validate the function
        if not isinstance(function, Union[int, float, str, list, Generator]):
            raise ValueError(
                f"Function of the dimensions {names} has to be int, float, str or generator object"
            )

        if isinstance(function, Union[int, float, str]):
            function = constant(function)

        if isinstance(function, list):
            if not function:  # if empty list
                raise IndexError
            function = cycle(function)

        # if isinstance(names, list):
        # for i,n in enumerate(names):

        items = MultiItems(
            names=names, function=function, aggregation_type=aggregation_type
        )

        if any((overlapping := set(names) & set(mt.names)) for mt in self._multi_items):
            raise ValueError(f"Multi items with name(s) {overlapping} already exists")

        self._multi_items.append(items)

        try:
            self._generate_data()
        except Exception as e:
            self._multi_items.remove(items)
            raise ValueError(e)

    def remove_multi_item(self, names: list) -> None:
        """
        Remove the dimension from the data generator by its name

        Args:
            names (list): The name of the items to remove.

        Raises:
            ValueError: If the multi-item with the specified names does not exist.

        Example:
            ```python
            data_gen.remove_multi_item(name=["item1","item2"])
            ```
        """
        if isinstance(names, str):
            names = list(names)

        # if any of the items in the names is present in a multi-item collection,
        # that collection is completely removed
        if overlapping_items := [
            mt for mt in self._multi_items if set(names) & set(mt.names)
        ]:
            for i in overlapping_items:
                self.data.drop(i.names, axis=1, inplace=True)
                self._multi_items = [
                    mt for mt in self._multi_items if mt.names != i.names
                ]

    def add_metric(
        self,
        name: str,
        trends: Set[Trends],
        aggregation_type: AggregationType = AggregationType.AVG,
    ) -> None:
        """
        Add a metric to the DataGen instance.

        This method allows you to add a new metric with specified characteristics to the DataGen instance.
        The `function_type` determines the type of data generation (e.g., sine wave, constant value, etc.).
        For sine or cosine metrics, additional parameters (`frequency_in_hour`, `offset_in_minutes`, and `scale`)
        must be provided. For constant metrics, only `scale` is required.

        Args:
            name (str): The unique name of the metric.
            function_type (str): The type of function used for data generation.
                Must be one of ["sine", "cosine", "constant", "generator"].
            frequency_in_hour (Optional[float]): The frequency of oscillation in hours.
                Required for "sine" and "cosine".
            offset_in_minutes (Optional[float]): The phase offset in minutes.
                Required for "sine" and "cosine".
            scale (Optional[float]): The amplitude of the wave or the constant value.
                Required for all function types.

        Raises:
            ValueError: If a metric with the same name already exists.
            ValueError: If required parameters for the specified `function_type` are missing.

        Example:
            ```python
            # Adding a sine metric
            data_gen.add_metric(
                name="sine_metric",
                function_type="sine",
                frequency_in_hour=1.0,
                offset_in_minutes=15.0,
                scale=10.0
            )

            # Adding a constant metric
            data_gen.add_metric(
                name="constant_metric",
                function_type="constant",
                scale=5.0
            )
            ```
        """
        metric = Metrics(name=name, trends=trends, aggregation_type=aggregation_type)
        # Raise error if self._metrics already contains a metric with the same name
        for m in self._metrics:
            if name == m.name:
                raise ValueError(f"Metric with name '{name}' already exists")
        self._metrics.append(metric)
        self._generate_data()

    def remove_metric(self, name: str) -> None:
        """
        Remove the metric from the data generator by its name

        Args:
            name (str): The name of the metric to remove.

        Raises:
            ValueError: If the metric with the specified name does not exist.

        Example:
            ```python
            data_gen.remove_metric(name="category")
            ```
        """
        if name in self.metrics:
            # update the data
            self.data = self.data.drop([name], axis=1)

        # drop the dimension from dimension list
        self._metrics = [d for d in self._metrics if d.name != name]

    def _generate_data(self) -> pd.DataFrame:
        """Generate a sample DataFrame with unique IDs and values.

        Args:
            rows: Number of rows to generate. Must be positive.

        Returns:
            pd.DataFrame: Generated data with 'id' and 'value' columns

        Raises:
            ValueError: If rows is less than or equal to 0
            TypeError: If rows cannot be converted to int
        """
        # Validate dates
        self._validate_dates()

        self._timestamps = pd.date_range(
            start=self.start_datetime,
            end=self.end_datetime,
            freq=self.granularity,
        )
        self._unix_timestamp = [int(ts.timestamp()) for ts in self._timestamps]
        # create an empty dataframe with timestamps as index
        if self.metric_data.empty:
            self.metric_data = pd.DataFrame(index=self._timestamps)

        if self.dimension_data.empty:
            self.dimension_data = pd.DataFrame(index=self._timestamps)

        if self.multi_item_data.empty:
            self.multi_item_data = pd.DataFrame(index=self._timestamps)

        if self.data.empty:
            self.data = pd.DataFrame(index=self._timestamps)
        else:
            # if data present and if there is change in timestamp ranges, reset dimension, metric and data
            if len(self.data) != len(self._timestamps):
                # Clear existing data to ensure full regeneration
                self.metric_data = pd.DataFrame(columns=[], index=self._timestamps)
                self.dimension_data = pd.DataFrame(columns=[], index=self._timestamps)
                self.multi_item_data = pd.DataFrame(columns=[], index=self._timestamps)
                self.data = pd.DataFrame(columns=[], index=self._timestamps)

        # Generate metric data
        for metric in self.metrics.values():
            # only proceed if metric name is not in the dataset
            if metric.name not in self.data.columns:
                # recursively concant the dataframe to self.metric_data
                self.metric_data = pd.concat(
                    [self.metric_data, metric.generate(self._timestamps)], axis=1
                )

            # if the metric is already in dataset, ignore with an empty dataframe
            else:
                self.metric_data = pd.DataFrame(index=self._timestamps)

        # Generate dimension data
        for dimension in self.dimensions.values():
            # only proceed if dimension name is not in the dataset
            if dimension.name not in self.data.columns:
                self.dimension_data = pd.concat(
                    [self.dimension_data, dimension.generate(self._timestamps)], axis=1
                )
            else:
                self.dimension_data = pd.DataFrame(index=self._timestamps)

        for multi_item in self.multi_items.values():
            if any(item not in self.data.columns for item in multi_item.names):
                self.multi_item_data = pd.concat(
                    [self.multi_item_data, multi_item.generate(self._timestamps)],
                    axis=1,
                )
            else:
                self.multi_item_data = pd.DataFrame(index=self._timestamps)

        # self.dimension_data = pd.DataFrame(dimension_data_dict, index=self._timestamps)

        self.data = pd.concat(
            [self.data, self.dimension_data, self.metric_data, self.multi_item_data],
            axis=1,
        )

        if "epoch" not in self.data.columns:
            self.data = pd.concat(
                [
                    self.data,
                    pd.DataFrame(
                        self._unix_timestamp, columns=["epoch"], index=self._timestamps
                    ),
                ],
                axis=1,
            )

        try:
            self._sort_df()
        except Exception:
            pass

    def aggregate(self, granularity: Granularity) -> pd.DataFrame:
        """
        Aggregate the data to a coarser granularity if requested.

        Args:
            granularity: The target granularity for aggregation.

        Raises:
            ValueError: If the requested granularity is finer than the current data granularity.
        """
        # Map string granularities to pandas offset aliases for comparison
        granularity_order = {"s": 0, "min": 1, "5min": 2, "h": 3, "D": 4, "W": 5, "ME": 6, "Y": 7}


        if granularity_order[granularity] < granularity_order[self.granularity]:
            raise ValueError(
                f"Cannot aggregate to a finer granularity ({granularity}) than current data granularity ({self.granularity})"
            )


        # Prepare aggregation dictionary
        agg_dict = {k: v.aggregation_type for k, v in self.metrics.items()}

        # Resample and aggregate
        group_keys = list(self.dimensions.keys())

        # Append to agg_dict
        for k, v in self.multi_items.items():
            if v.aggregation_type:
                for i, item in enumerate(k.split(",")):
                    agg_dict[item] = v.aggregation_type[i]

            else:
                group_keys.extend(k.split(","))

        # Always keep 'epoch' out of groupby, as it will be recalculated
        resampled = (
            self.data.drop("epoch",axis=1).reset_index()
            .groupby(group_keys)
            .resample(granularity,on="index")
            .agg(agg_dict)
            .reset_index()
            .set_index("index")
            .sort_index()
        )

        resampled.columns = resampled.columns.get_level_values(0)
        # Recalculate epoch column
        resampled["epoch"] = resampled.index.astype("int64") // 10**9
        # resampled.set_index("index", inplace=True)

        return resampled

    def _sort_df(self):
        colum_order = (
            ["epoch"]
            + list(self.dimensions.keys())
            + list(self.metrics.keys())
            + list(chain(*[s.split(",") for s in self.multi_items.keys()]))
        )
        self.data = self.data.reindex(columns=colum_order)

    def normalize(self, method="min-max"):
        if method not in ("min-max", "mean-std"):
            raise NotImplementedError(
                f"Invalid method: {method}. Allowed values are 'min-max'"
            )

        df_numeric = self.data.select_dtypes(
            include=["number"]
        )  # Select only numeric columns

        if method == "min-max":
            # Min-Max Scaling
            df_scaled = (df_numeric - df_numeric.min()) / (
                df_numeric.max() - df_numeric.min()
            )  # Min-Max Normalization

        if method == "mean-std":
            # Mean-Std Scaling
            df_scaled = (df_numeric - df_numeric.mean()) / (
                df_numeric.std()
            )  # Min-Max Normalization

        self._scale_factors["min"] = df_numeric.min()
        self._scale_factors["max"] = df_numeric.max()

        # Merge back with non-numeric columns
        self.data[df_numeric.columns] = df_scaled

    def denormalize(self):
        df_numeric = self.data.select_dtypes(
            include=["number"]
        )  # Select only numeric columns
        # Reverse the Min-Max Scaling
        self.data[df_numeric.columns] = (
            self.data[df_numeric.columns]
            * (self._scale_factors["max"] - self._scale_factors["min"])
            + self._scale_factors["min"]
        )

    def plot(self, exclude: List[str] = [], include: List[str] = []):
        """
        Plots the data based on the specified inclusion and exclusion criteria.
        Parameters:
        exclude (List[str]): A list of strings specifying the data columns to exclude from the plot.
        include (List[str]): A list of strings specifying the data columns to include in the plot.
        Returns:
        None
        """
        if exclude and include:
            raise ValueError(
                "Only one of 'exclude' or 'include' should be provided, not both."
            )

        # Get only numeric columns
        numeric_cols = self.data.select_dtypes(include=["number"]).columns.tolist()
        numeric_cols.remove("epoch") if "epoch" in numeric_cols else numeric_cols

        if exclude:
            plot_cols = [col for col in numeric_cols if col not in exclude]
        elif include:
            plot_cols = [col for col in numeric_cols if col in include]
        else:
            plot_cols = numeric_cols  # Default: Plot all numeric columns

        if not plot_cols:
            raise ValueError("No numeric columns available for plotting.")

        self.data.plot(y=plot_cols)
