# Eaton ePDU integration for Home Assistant

[![Version](https://img.shields.io/github/v/release/jaroschek/home-assistant-eaton-epdu?label=version)](https://github.com/jaroschek/home-assistant-eaton-epdu/releases/latest)
[![Validate for HACS](https://github.com/jaroschek/home-assistant-eaton-epdu/workflows/Validate%20for%20HACS/badge.svg)](https://github.com/jaroschek/home-assistant-eaton-epdu/actions/workflows/hacs.yaml)
[![Validate with hassfest](https://github.com/jaroschek/home-assistant-eaton-epdu/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/jaroschek/home-assistant-eaton-epdu/actions/workflows/hassfest.yaml)

Custom Home Assistant integration for Eaton ePDU devices and sensors through SNMP.

## Install
### HACS
The easiest way to install this component is by clicking the badge below, which adds this repo as a custom repo in your HASS instance.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&owner=jaroschek&repository=home-assistant-eaton-epdu)

You can also add the integration manually by copying `custom_components/eaton_epdu` into `<HASS config directory>/custom_components`

## Accurate power monitoring

While the Eaton ePDU is capable of measuring power accurately, they made a huge messup and report power as an integer. This means the reporting will always be inaccurate by one watt which is especially annoying at lower power levels.
Fortunately the ePDU also reports power, current and power factor and each of them in thousands (I wonder why they did not just do the same for power).

When using the option "Use accurate power entity (VxIxCosPhi)", the integration will use voltage, current and power factor to provide a more accurate power estimate.

### Caveat

Even here, Eaton surprises and they just leave out the voltage information for the outlets, even though it's defined in the MIBs (https://mibs.observium.org/mib/EATON-EPDU-MIB/).
This means the accurate power option works well for input power but not for outlets.
However, since voltage is passed straight through from the input, we can use the input voltage as a proxy.
Unfortunately there could be many inputs and each outlet maps to an input.
It may be possible to use the group voltage via parent lookup, however, this required two additional SNMP queries.
For now, this extension assumes that all outlets use the first input voltage.
If you have multiple input voltages, either accept a small discrepancy, disable this option or update this extension.







Use accurate power entity (VxIxCosPhi)





