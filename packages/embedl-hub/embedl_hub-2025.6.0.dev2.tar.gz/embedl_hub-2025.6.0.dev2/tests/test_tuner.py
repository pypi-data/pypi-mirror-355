# Copyright (C) 2025 Embedl AB

"""Tests for the tuning module and related functions."""

import pytest
from torchvision.transforms import (
    Compose,
    Normalize,
    RandomCrop,
    Resize,
    ToTensor,
)

from embedl_hub.core.tuning.load_model import (
    load_model_from_torchvision,
    load_model_with_num_classes,
    load_timm_with_num_classes,
)
from embedl_hub.core.tuning.tuner import (
    _decode_tranforms,
    transforms_mapping,
)


@pytest.mark.parametrize(
    "model_id",
    ["torchvision/alexnet", "TORCHVISION/ALEXNET", "TorchVision/AlexNet"],
)
def test_load_alexnet_from_hub(model_id):
    """Test loading alexnet from the hub with different casing."""
    model = load_model_from_torchvision(model_id, pre_trained=False)
    assert model is not None


def test_load_unknown_model_from_hub():
    """Test loading an unknown model from the hub."""
    with pytest.raises(ValueError):
        load_model_from_torchvision(
            "torchvision/unknown_model", pre_trained=False
        )


def test_transforms_mapping_contains_known_class():
    """Sanity check that our mapping picked up torchvision classes."""
    assert "Resize" in transforms_mapping
    assert transforms_mapping["Resize"] is Resize


def test_decode_empty_list_returns_empty_compose():
    """Test that the composition can be empty."""
    comp = _decode_tranforms([])
    assert isinstance(comp, Compose)
    # Compose stores its list in .transforms
    assert comp.transforms == []


def test_decode_single_transform_by_name():
    """Test that a single transform can be decoded."""
    cfg = [{"type": "ToTensor"}]
    comp = _decode_tranforms(cfg)
    assert isinstance(comp, Compose)
    assert len(comp.transforms) == 1
    assert isinstance(comp.transforms[0], ToTensor)


def test_decode_with_parameters():
    """Test that parameterized transforms can be decoded."""
    cfg = [
        {"type": "RandomCrop", "size": (10, 20), "padding": 4},
        {"type": "Resize", "size": 50},
        {"type": "Normalize", "mean": [0.5, 0.5, 0.5], "std": [0.1, 0.1, 0.1]},
    ]
    comp = _decode_tranforms(cfg)
    transforms = comp.transforms

    assert isinstance(transforms[0], RandomCrop)
    assert transforms[0].size == (10, 20)
    assert transforms[0].padding == 4

    assert isinstance(transforms[1], Resize)
    # Resize stores target size under .size
    assert transforms[1].size == 50

    assert isinstance(transforms[2], Normalize)
    assert pytest.approx(transforms[2].mean) == [0.5, 0.5, 0.5]
    assert pytest.approx(transforms[2].std) == [0.1, 0.1, 0.1]


def test_decode_multiple_ordering_preserved():
    """Test that the ordering of transforms is preserved."""
    cfg = [
        {"type": "Resize", "size": 32},
        {"type": "ToTensor"},
        {"type": "Normalize", "mean": [0.0], "std": [1.0]},
    ]
    comp = _decode_tranforms(cfg)
    types = [type(t) for t in comp.transforms]
    assert types == [Resize, ToTensor, Normalize]


def test_unknown_transform_type_raises():
    """Check that unknown transforms raises value error."""
    cfg = [{"type": "NotARealTransform", "foo": "bar"}]
    with pytest.raises(ValueError) as excinfo:
        _decode_tranforms(cfg)
    assert "Unknown transform type: NotARealTransform" in str(excinfo.value)


def test_load_timm_model_from_hub():
    """Test loading a timm model from the hub."""
    with pytest.raises(ValueError):
        load_timm_with_num_classes(
            "timm/unknown_model", pre_trained=False, num_classes=1000
        )

    # Assuming we have a valid timm model ID
    model = load_timm_with_num_classes(
        "timm/tinynet_e_in1k, INT8", pre_trained=False, num_classes=1000
    )
    assert model is not None
    assert hasattr(model, "forward")


def test_load_torchvision_model_with_num_classes():
    """Test loading a torchvision model with a specific number of classes."""
    model = load_model_with_num_classes(
        "torchvision/resnet18", pre_trained=False, num_classes=10
    )
    assert model is not None
    assert hasattr(model, "forward")
    # Check if the last layer has the correct number of classes
    assert model.fc.out_features == 10


def test_load_timm_model_with_num_classes():
    """Test loading a timm model with a specific number of classes."""
    model = load_model_with_num_classes(
        "timm/tinynet_e_in1k, INT8", pre_trained=False, num_classes=10
    )
    assert model is not None
    assert hasattr(model, "forward")
    # Check if the last layer has the correct number of classes
    assert model.classifier.out_features == 10


if __name__ == "__main__":
    pytest.main([__file__])
