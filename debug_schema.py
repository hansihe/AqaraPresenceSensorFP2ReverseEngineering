# /// script
# dependencies = ["esphome"]
# ///
import esphome.components.binary_sensor as bs
import esphome.config_validation as cv

print(f"Has validate_device_class: {hasattr(bs, 'validate_device_class')}")
print(f"Has device_class: {hasattr(bs, 'device_class')}")

try:
    print(bs.device_class)
except AttributeError:
    print("bs.device_class raises AttributeError")

