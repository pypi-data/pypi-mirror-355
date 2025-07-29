"""
Extrapolators take discrete sample data and extrapolate the data onto a provided grid.

This file segments all extapolators that require tensorflow.
"""

from typing import List
from typing_extensions import Self

import numpy as np
import xarray as xr
import tqdm  # type: ignore

from AFL.double_agent.PipelineOp import PipelineOp
from AFL.double_agent.util import listify

import tensorflow as tf  # type: ignore
import gpflow

from sklearn.preprocessing import OrdinalEncoder


class TFExtrapolator(PipelineOp):
    """Base class for all tensorflow based extrapolators

    Parameters
    ----------
    feature_input_variable : str
        The name of the `xarray.Dataset` data variable to use as the input to the model that will be extrapolating
        the discrete data. This is typically a sample composition variable.
    predictor_input_variable : str
        The name of the `xarray.Dataset` data variable to use as the output of the model that will be extrapolating
        the discrete data. This is typically a class label or property variable.
    output_variables : List[str]
        The list of variables that will be output by this class.
    output_prefix : str
        The string prefix to apply to each output variable before inserting into the output `xarray.Dataset`
    grid_variable : str
        The name of the `xarray.Dataset` data variable to use as an evaluation grid.
    grid_dim : str
        The xarray dimension over each grid_point. Grid equivalent to sample.
    sample_dim : str
        The `xarray` dimension over the discrete 'samples' in the `feature_input_variable`. This is typically
        a variant of `sample` e.g., `saxs_sample`.
    optimize : bool
        Whether to optimize the model parameters
    name : str, default="Extrapolator"
        The name to use when added to a Pipeline
    """

    def __init__(
        self,
        feature_input_variable: str,
        predictor_input_variable: str,
        output_variables: List[str],
        output_prefix: str,
        grid_variable: str,
        grid_dim: str,
        sample_dim: str,
        optimize: bool,
        name: str = "Extrapolator",
    ) -> None:

        super().__init__(
            name=name,
            input_variable=[
                feature_input_variable,
                predictor_input_variable,
                grid_variable,
            ],
            output_variable=[
                output_prefix + "_" + o for o in listify(output_variables)
            ],
            output_prefix=output_prefix,
        )
        self.feature_input_variable = feature_input_variable
        self.predictor_input_variable = predictor_input_variable
        self.grid_variable = grid_variable
        self.sample_dim = sample_dim
        self.grid_dim = grid_dim
        self.optimize = True

        self._banned_from_attrs.extend(["kernel", "opt_logs"])

        self.ordinal_encoder = OrdinalEncoder()

    def calculate(self, dataset: xr.Dataset) -> Self:
        """Apply this `PipelineOp` to the supplied `xarray.Dataset`"""
        return NotImplementedError(".calculate must be implemented in subclasses")  # type: ignore

    def encode(self, labels):
        labels_np = labels.values.reshape(-1, 1)
        labels_np_ord = self.ordinal_encoder.fit_transform(labels_np)
        labels_ord = labels.copy(data=labels_np_ord.squeeze())
        return labels_ord

    def invert_encoded(self, labels):
        labels_np = labels.values.reshape(-1, 1)
        labels_np_orig = self.ordinal_encoder.fit_transform(labels_np)
        labels_orig = labels.copy(data=labels_np_orig.squeeze())
        return labels_orig



class TFGaussianProcessClassifier(TFExtrapolator):
    """Use a Gaussian process classifier to extrapolate class labels at discrete compositions onto a composition grid"""

    def __init__(
        self,
        feature_input_variable: str,
        predictor_input_variable: str,
        output_prefix: str,
        grid_variable: str,
        grid_dim: str,
        sample_dim: str,
        optimize: bool = True,
        kernel: str = 'Matern32',
        kernel_kwargs: dict = {'lengthscales':0.1, 'variance':0.1},
        name: str = "TFGaussianProcessClassifier",
    ) -> None:
        """
        Parameters
        ----------
        feature_input_variable : str
            The name of the `xarray.Dataset` data variable to use as the input to the model that will be extrapolating
            the discrete data. This is typically a sample composition variable.

        predictor_input_variable : str
            The name of the `xarray.Dataset` data variable to use as the output of the model that will be extrapolating
            the discrete data. For this `PipelineOp` this should be a class label vector.

        output_prefix: str
            The string prefix to apply to each output variable before inserting into the output `xarray.Dataset`

        grid_variable: str
            The name of the `xarray.Dataset` data variable to use as an evaluation grid.

        grid_dim: str
            The xarray dimension over each grid_point. Grid equivalent to sample.

        sample_dim: str
            The `xarray` dimension over the discrete 'samples' in the `feature_input_variable`. This is typically
            a variant of `sample` e.g., `saxs_sample`.

        kernel: str | None
            The name of the sklearn.gaussian_process.kernel to use the classifier. If not provided, will default to
            `Matern32`.
        
        kernel_kwargs: dict | None
            Additional keyword arguments to pass to the sklearn.gaussian_process.kernel

        name: str
            The name to use when added to a Pipeline. This name is used when calling Pipeline.search()
        """

        super().__init__(
            name=name,
            feature_input_variable=feature_input_variable,
            predictor_input_variable=predictor_input_variable,
            output_variables=["mean", "variance"],
            output_prefix=output_prefix,
            grid_variable=grid_variable,
            grid_dim=grid_dim,
            sample_dim=sample_dim,
            optimize=optimize,
        )

        self.kernel = kernel
        self.kernel_kwargs = kernel_kwargs

        self.output_prefix = output_prefix

    def calculate(self, dataset: xr.Dataset) -> Self:
        """Apply this `PipelineOp` to the supplied `xarray.Dataset`"""
        X = dataset[self.feature_input_variable].transpose(self.sample_dim, ...)
        y = dataset[self.predictor_input_variable].transpose(self.sample_dim, ...)
        grid = dataset[self.grid_variable]

        if len(np.unique(y)) == 1:

            self.output[self._prefix_output("mean")] = xr.DataArray(
                np.ones(dataset.grid.shape), dims=[self.grid_dim]
            )
            self.output[self._prefix_output("entropy")] = xr.DataArray(
                np.ones(dataset.grid.shape), dims=[self.grid_dim]
            )

        else:
            n_classes: int = len(np.unique(y.values))
            data = (X.values, y.values.reshape(-1,1))

            invlink = gpflow.likelihoods.RobustMax(n_classes)
            likelihood = gpflow.likelihoods.MultiClass(n_classes, invlink=invlink)
            kernel = getattr(gpflow.kernels, self.kernel)(**self.kernel_kwargs)
            model = gpflow.models.VGP(
                data=data,
                kernel=kernel,
                likelihood=likelihood,
                num_latent_gps=n_classes,
            )

            if self.optimize:
                opt = gpflow.optimizers.Scipy()
                self.opt_logs = opt.minimize(
                    model.training_loss_closure(),
                    model.trainable_variables,
                    options=dict(maxiter=1000),
                )

            mean, variance = model.predict_y(grid.values)

            param_dict = {}
            blocked_vars = ['q_mu', 'q_sqrt', 'f_mu', 'f_sqrt']
            for k, v in gpflow.utilities.parameter_dict(model).items():
                if k[0]=='.':
                    k = k[1:]
                if k in blocked_vars:
                    continue
                param_dict[k] = v.numpy().tolist()

            self.output[self._prefix_output("mean")] = xr.DataArray(
                mean.numpy().argmax(-1), dims=self.grid_dim
            )
            self.output[self._prefix_output("mean")].attrs.update(param_dict)
            self.output[self._prefix_output("variance")] = xr.DataArray(
                variance.numpy().sum(-1), dims=self.grid_dim
            )
            self.output[self._prefix_output("variance")].attrs.update(param_dict)

        return self
