from sklearn.datasets import load_iris
from tinyml4all.tabular.classification.ClassificationTable import (
    ClassificationTable as Table,
    Source,
)


iris = load_iris(as_frame=True)
Iris = Table(
    [
        Source(
            source_name="Iris.csv",
            index=0,
            data=iris.data,
            Y_true=[iris.target_names[y] for y in iris.target],
        )
    ]
)
