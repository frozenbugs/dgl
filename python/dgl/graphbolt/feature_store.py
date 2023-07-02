"""Feature store for GraphBolt."""
import torch


class FeatureStore:
    r"""Base class for feature store."""

    def __init__(self):
        pass

    def read(self, key: str, ids: torch.Tensor = None):
        """Read a feature from the feature store.

        Parameters
        ----------
        key : str
            The key that uniquely identifies the feature in the feature store.
        ids : torch.Tensor, optional
            The index of the feature. If specified, only the specified indices
            of the feature are read. If None, the entire feature is returned.

        Returns
        -------
        torch.Tensor
            The read feature.
        """
        raise NotImplementedError

    def update(self, key: str, value: torch.Tensor, ids: torch.Tensor = None):
        """Update a feature in the feature store.

        This function is used to update a feature in the feature store. The
        feature is identified by a unique key, and its value is specified using
        a tensor.

        Parameters
        ----------
        key : str
            The key that uniquely identifies the feature in the feature store.
        value : torch.Tensor
            The updated value of the feature.
        ids : torch.Tensor, optional
            The indices of the feature to update. If specified, only the
            specified indices of the feature will be updated. For the feature,
            the `ids[i]` row is updated to `value[i]`. So the indices and value
            must have the same length. If None, the entire feature will be
            updated.
        """
        raise NotImplementedError


class TorchBasedFeatureStore(FeatureStore):
    r"""Torch based key-value feature store, where the key are strings and
    values are Pytorch tensors."""

    def __init__(self, feature_dict: dict):
        """Initialize a torch based feature store.

        The feature store is initialized with a dictionary of tensors, where the
        key is the name of a feature and the value is the tensor. The value can
        be multi-dimensional, where the first dimension is the index of the
        feature.

        Note that the values can be in memory or on disk.

        Parameters
        ----------
        feature_dict : dict, optional
            A dictionary of tensors.

        Examples
        --------
        >>> import torch
        >>> feature_dict = {
        ...     "user": torch.arange(0, 5),
        ...     "item": torch.arange(0, 6),
        ...     "rel": torch.arange(0, 6).view(2, 3),
        ... }
        >>> feature_store = TorchBasedFeatureStore(feature_dict)
        >>> feature_store.read("user", torch.tensor([0, 1, 2]))
        tensor([0, 1, 2])
        >>> feature_store.read("item", torch.tensor([0, 1, 2]))
        tensor([0, 1, 2])
        >>> feature_store.read("rel", torch.tensor([0]))
        tensor([[0, 1, 2]])
        >>> feature_store.update("user",
        ... torch.ones(3, dtype=torch.long), torch.tensor([0, 1, 2]))
        >>> feature_store.read("user", torch.tensor([0, 1, 2]))
        tensor([1, 1, 1])

        >>> import numpy as np
        >>> user = np.arange(0, 5)
        >>> item = np.arange(0, 6)
        >>> np.save("/tmp/user.npy", user)
        >>. np.save("/tmp/item.npy", item)
        >>> feature_dict = {
        ...     "user": torch.as_tensor(np.load("/tmp/user.npy",
        ...             mmap_mode="r+")),
        ...     "item": torch.as_tensor(np.load("/tmp/item.npy",
        ...             mmap_mode="r+")),
        ... }
        >>> feature_store = TorchBasedFeatureStore(feature_dict)
        >>> feature_store.read("user", torch.tensor([0, 1, 2]))
        tensor([0, 1, 2])
        >>> feature_store.read("item", torch.tensor([3, 4, 2]))
        tensor([3, 4, 2])
        """
        super(TorchBasedFeatureStore, self).__init__()
        assert isinstance(feature_dict, dict), (
            f"feature_dict in TorchBasedFeatureStore must be dict, "
            f"but got {type(feature_dict)}."
        )
        for k, v in feature_dict.items():
            assert isinstance(
                k, str
            ), f"Key in TorchBasedFeatureStore must be str, but got {k}."
            assert isinstance(v, torch.Tensor), (
                f"Value in TorchBasedFeatureStore must be torch.Tensor,"
                f"but got {v}."
            )

        self._feature_dict = feature_dict

    def read(self, key: str, ids: torch.Tensor = None):
        """Read a feature from the feature store by index.

        The returned feature is always in memory, no matter whether the feature
        to read is in memory or on disk.

        Parameters
        ----------
        key : str
            The key of the feature.
        ids : torch.Tensor, optional
            The index of the feature. If specified, only the specified indices
            of the feature are read. If None, the entire feature is returned.

        Returns
        -------
        torch.Tensor
            The read feature.
        """
        assert (
            key in self._feature_dict
        ), f"key {key} not in {self._feature_dict.keys()}"
        if ids is None:
            return self._feature_dict[key]
        return self._feature_dict[key][ids]

    def update(self, key: str, value: torch.Tensor, ids: torch.Tensor = None):
        """Update a feature in the feature store.

        This function is used to update a feature in the feature store. The
        feature is identified by a unique key, and its value is specified using
        a tensor.

        Parameters
        ----------
        key : str
            The key that uniquely identifies the feature in the feature store.
        value : torch.Tensor
            The updated value of the feature.
        ids : torch.Tensor, optional
            The indices of the feature to update. If specified, only the
            specified indices of the feature will be updated. For the feature,
            the `ids[i]` row is updated to `value[i]`. So the indices and value
            must have the same length. If None, the entire feature will be
            updated.
        """
        assert (
            key in self._feature_dict
        ), f"key {key} not in {self._feature_dict.keys()}"
        if ids is None:
            self._feature_dict[key] = value
        else:
            assert ids.shape[0] == value.shape[0], (
                f"ids and value must have the same length, "
                f"but got {ids.shape[0]} and {value.shape[0]}."
            )
            self._feature_dict[key][ids] = value