from tempfile import TemporaryDirectory, gettempdir
from typing import Self, Literal, Tuple

import hexdump
import numpy as np
import tensorflow.keras
from pandas import DataFrame
from sklearn.model_selection import train_test_split
from sympy.codegen import Print

from tinyml4all.support.types import coalesce, cast, TemplateDef
from tinyml4all.tabular.common.Targets import Targets
from tinyml4all.tensorflow.Report import Report
from tinyml4all.tensorflow.layers import Dense
from tinyml4all.transpile.Convertible import Convertible


class Sequential(Convertible):
    """
    Proxy to tf.keras.Sequential
    """

    def __init__(self):
        """
        Constructor
        """
        self.sequential = None
        self.task = None
        self.input_shape = None
        self.representative_dataset = None
        self.report = Report()
        self.layers = []

    def get_template(self) -> TemplateDef:
        """
        Get template
        :return:
        """
        import tensorflow as tf

        always = ["Shape", "Reshape", "Softmax", "Quantize", "Dequantize"]
        layers = [[layer.tflm_name] + layer.tflm_dependencies for layer in self.layers]
        layers = set([l for lst in layers for l in lst] + always)

        # LSTM deserves special treatment
        if "UnidirectionalSequenceLSTM" in layers:
            # see https://github.com/tensorflow/tflite-micro/issues/2006#issuecomment-1567349993
            model_dir = gettempdir()
            run_model = tf.function(lambda x: self.sequential(x))
            input_shape = [d or 1 for d in self.sequential.layers[0].input_shape]
            concrete_func = run_model.get_concrete_function(
                tf.TensorSpec(input_shape, self.sequential.inputs[0].dtype)
            )

            self.sequential.save(model_dir, save_format="tf", signatures=concrete_func)
            converter = tf.lite.TFLiteConverter.from_saved_model(model_dir)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        else:
            converter = tf.lite.TFLiteConverter.from_keras_model(self.sequential)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.inference_input_type = tf.int8
            converter.inference_output_type = tf.int8
            converter.target_spec.supported_ops = [
                tf.lite.OpsSet.TFLITE_BUILTINS_INT8,
                # tf.lite.OpsSet.SELECT_TF_OPS,
            ]
            converter.representative_dataset = lambda: self.representative_iterator()

        model_bytes = hexdump.dump(converter.convert()).split(" ")

        return "tensorflow/Sequential.jinja", {
            "class_name": self.__class__.__name__,
            "target_names": [
                f'"{label}"' for label in coalesce(self.report.unique_labels, [])
            ],
            "layers": layers,
            "io": {
                "num_inputs": np.prod(self.input_shape),
                "num_outputs": self.sequential.layers[-1].output_shape[1],
                "target_names": self.report.unique_labels,
            },
            "model": {
                "length": len(model_bytes),
                "data": ", ".join(["0x%02x" % int(byte, 16) for byte in model_bytes]),
            },
        }

    def classification_report(self) -> str:
        """
        Get classification report
        :return:
        """
        return self.report.classification_report()

    def add(self, layer) -> Self:
        """
        Add new layer
        :param layer:
        :return:
        """
        self.layers.append(layer)

        return self

    def compile(self, X, Y, task: Literal["classification", "regression"], **kwargs):
        """
        Compiles the network
        :param X:
        :param Y:
        :param task:
        :param kwargs:
        :return:
        """
        import tensorflow.keras.layers as tf
        from tensorflow.keras.optimizers import Adam

        X = self.reshape_x(X)
        Y = self.reshape_y(Y, task=task)
        input_shape = X.shape[1:]
        num_outputs = Y.shape[1]
        layers = []

        self.input_shape = input_shape
        self.sequential = tensorflow.keras.Sequential(
            [tf.Input(shape=input_shape, batch_size=1)]
        )

        # resolve layers with input shape from previous layer
        for layer in self.layers:
            resolved = layer.resolve(X=X, Y=Y, input_shape=input_shape)
            # allow single layer resolve to multiple layers
            resolved = cast(resolved, list, caster=lambda l: [l])

            for l in resolved:
                layers.append(l)
                self.sequential.add(l)
                input_shape = l.output_shape

        head = layers[-1]

        # set default loss and metrics
        kwargs.setdefault("optimizer", Adam(learning_rate=0.001))

        match task:
            case "classification":
                kwargs.setdefault("loss", "categorical_crossentropy")
                kwargs.setdefault("metrics", ["categorical_accuracy"])

                # append Dense layer with softmax activation, if not already
                if (
                    not isinstance(head, Dense)
                    or head.units != num_outputs
                    or head.activation != "softmax"
                ):
                    self.sequential.add(tf.Flatten())
                    self.sequential.add(
                        tf.Dense(
                            num_outputs,
                            activation="softmax",
                            name="classification_head",
                        )
                    )
            case "regression":
                kwargs.setdefault("loss", "mean_squared_error")
                kwargs.setdefault("metrics", ["mean_squared_error"])

                # append Dense layer with correct number of units, if not already
                if not isinstance(head, Dense) or head.units != num_outputs:
                    self.sequential.add(tf.Flatten())
                    self.sequential.add(tf.Dense(num_outputs, name="regression_head"))

        # define and compile network
        self.sequential.compile(**kwargs)

        return self.sequential.summary()

    def fit(
        self,
        X: np.ndarray[float, float],
        Y: np.ndarray[float, float],
        epochs: int = 30,
        validation_data: float | Tuple = 0.2,
        test_data: float | Tuple = None,
        plot: bool = False,
        **kwargs,
    ):
        """
        Fit network
        :param X:
        :param Y:
        :param epochs:
        :param validation_data:
        :param test_data:
        :param plot:
        :param kwargs:
        :return:
        """
        assert self.sequential is not None, (
            "You must compile() the network before fitting"
        )

        X_train, Y_train = self.reshape_x(X), self.reshape_y(Y)
        X_val, Y_val = (
            validation_data if isinstance(validation_data, tuple) else (None, None)
        )
        X_test, Y_test = test_data if isinstance(test_data, tuple) else (None, None)
        self.representative_dataset = X_train

        if isinstance(validation_data, float) and validation_data > 0:
            X_train, X_val, Y_train, Y_val = train_test_split(
                X_train, Y_train, test_size=validation_data
            )

        if isinstance(test_data, float) and test_data > 0:
            X_train, X_test, Y_train, Y_test = train_test_split(
                X_train, Y_train, test_size=test_data
            )
        elif X_test is None:
            X_test, Y_test = X_val, Y_val

        history = self.sequential.fit(
            X_train, Y_train, epochs=epochs, validation_data=(X_val, Y_val), **kwargs
        )
        self.report.set_history(history)

        # predict to get report
        Y_pred = self.predict(X=X_test)
        self.report.set_results(ground_truth=Y_test, pred=Y_pred)

        if plot:
            self.report.plot()

    def predict(self, X: np.ndarray[float, float]) -> np.ndarray[float]:
        """
        Predict
        :param X:
        :return:
        """
        return self.sequential.predict(self.reshape_x(X))

    def reshape_x(self, X: np.ndarray | DataFrame) -> np.ndarray:
        """
        Reshape X to (N, 1)
        :param X:
        :return:
        """
        if isinstance(X, DataFrame):
            return X.to_numpy()

        return X

    def reshape_y(
        self,
        Y: np.ndarray[float] | Targets,
        task: Literal["classification", "regression"] = None,
    ) -> np.ndarray[float]:
        """
        Reshape y to (N, 1)
        :param Y:
        :return:
        """
        from keras.utils import to_categorical

        if isinstance(Y, Targets):
            self.report.set_target_names(Y.unique_labels)
            Y = Y.numeric

        # Y must always be a 2D array
        if Y.ndim == 1:
            Y = Y.reshape(-1, 1)

        # if classification, Y must be one-hot encoded
        if coalesce(task, self.task) == "classification":
            Y = to_categorical(Y)

        if task:
            self.task = task

        return Y

    def representative_iterator(self):
        """
        Iterator for representative dataset quantization
        :return:
        """
        for x in self.representative_dataset:
            yield [x.astype(np.float32)]
