import json
import os
import warnings
from collections import namedtuple
from itertools import groupby
from pathlib import Path
from typing import Self, Generator, Tuple, List, Dict

import numpy as np
import pandas as pd

from tinyml4all.support.traits.HasClassmap import HasClassmap
from tinyml4all.support.types import TemplateDef, coalesce
from tinyml4all.time.TimeSeries import TimeSeries
from tinyml4all.time.episodic.classification.Line import Line
from tinyml4all.time.episodic.classification.LabelGUI import LabelGUI
from tinyml4all.time.episodic.classification.Source import Source
from tinyml4all.transpile.Convertible import Convertible


class EpisodicClassificationTimeSeries(TimeSeries, HasClassmap, Convertible):
    """
    Time series for episodic classification
    """

    @classmethod
    def read_csv_folder(cls: type[Self], folder: str, **kwargs) -> Self:
        """
        Read CSV folder
        :param folder:
        :param kwargs:
        :return:
        """
        ts = super().read_csv_folder(folder, **kwargs)

        # if a labels.json file exists, load labels from it
        if os.path.exists(os.path.join(folder, "labels.json")):
            for ev in json.loads(Path(os.path.join(folder, "labels.json")).read_text()):
                ts.add_label(label=ev["label"], t=ev["t"], height=float(ev["height"]))

        return ts

    @classmethod
    def get_source_class(cls) -> type[Self]:
        """
        Get source class
        :return:
        """
        return Source

    def __init__(
        self, sources: List[Source], event_durations: Dict[str, pd.Timedelta] = None
    ):
        """
        Constructor
        :param sources:
        """
        super().__init__(sources=sources)
        self.event_durations: Dict[str, pd.Timedelta] = coalesce(event_durations, {})

    @property
    def line(self) -> Line:
        """
        Get line plotter
        :return:
        """
        return Line(self)

    @property
    def label_gui(self) -> LabelGUI:
        """
        Get label UI
        :return:
        """
        return LabelGUI(self)

    @property
    def events(self) -> Generator[Tuple[Source, str, pd.Timestamp], None, None]:
        """
        Iterate over groups of labels
        :return:
        """
        for source in self.sources:
            for label, t, height in source.events:
                yield source, label, t, height

    def collapse(self) -> Self:
        """
        Collapse time series into a single source
        :return:
        """
        ts = super().collapse()
        ts.event_durations = self.event_durations

        return ts

    def add_label(self, label: str, t: str, height: float = None):
        """
        Add label
        :param label:
        :param t:
        :param height:
        :return:
        """
        [source.add_label(label, t, height=height) for source in self.sources]

    def set_duration(self, label: str, duration: str):
        """
        Set duration
        :param label:
        :param duration:
        :return:
        """
        self.event_durations[label] = pd.Timedelta(duration)

    def label_from_file(self, path: str):
        """
        Load labels from file
        :param path:
        :return:
        """
        assert os.path.exists(path), f"File {path} does not exist"
        assert path.endswith(".json"), f"File {path} is not a JSON file"

        with open(path, "r") as f:
            for event in json.load(f):
                # event duration
                if "duration" in event:
                    self.set_duration(event["label"], event["duration"])
                # event
                elif "t" in event:
                    self.add_label(
                        event["label"], event["t"], height=event.get("height", 0)
                    )
                else:
                    warnings.warn(f"Entry {event} is not valid")

    def split_by_events(self, test_size: float = 0.2) -> Tuple[Self, Self]:
        """
        Split time series in train and test
        :param test_size: percentage of test data
        :return: train, test
        """
        Event = namedtuple("Event", "label, t, height")
        events = [Event(label, t, h) for _, label, t, h in self.events]
        train_events = []
        test_events = []

        for label, label_events in groupby(events, lambda event: event.label):
            label_events = list(label_events)
            count = len(label_events)
            train_indices = np.random.choice(
                count, int(count * (1 - test_size)), replace=False
            )
            train_events.extend(
                [ev for i, ev in enumerate(label_events) if i in train_indices]
            )
            test_events.extend(
                [ev for i, ev in enumerate(label_events) if i not in train_indices]
            )

        def mask_events(
            ts: EpisodicClassificationTimeSeries,
            include_events: List[Event],
            exclude_events: List[Event],
        ):
            T = ts.T
            df = ts.df

            # drop test windows in train dataset
            for ev in exclude_events:
                duration = self.event_durations[ev.label]
                mask = (T < ev.t - duration / 2) | (T > ev.t + duration / 2)

                # fix overlapping events
                for ev in include_events:
                    mask[(T >= ev.t - duration / 2) & (T <= ev.t + duration / 2)] = True

                T = T[mask]
                df = df.iloc[mask]

            source = Source(source_name=":memory:", index=0, data=df, T=T)

            for ev in include_events:
                source.add_label(ev.label, ev.t, height=ev.height)

            return EpisodicClassificationTimeSeries(
                sources=[source], event_durations=self.event_durations
            )

        ts = self.collapse()
        train = mask_events(ts, include_events=train_events, exclude_events=test_events)
        test = mask_events(ts, include_events=test_events, exclude_events=train_events)

        return train, test

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        return "time/episodic/classification/TimeSeries", {
            "data": self.df.to_numpy(),
            "T": [str(t) for t in self.T],
        }
