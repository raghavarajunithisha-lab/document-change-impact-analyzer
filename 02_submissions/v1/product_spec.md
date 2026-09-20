# AirSense Environmental Sensor

> SYNTHETIC DEMONSTRATION DOCUMENT. This fictional product and its design claims are test data, not an Espressif product, actual test evidence, or a Seamflow customer submission. Do not use this document to build hardware.

- Document ID: AS-PRD-001
- Version: 1.0
- Status: Submitted for document review
- Product ID: AS-ENV-001
- Hardware revision: A

## Product Purpose

AirSense is a fictional temperature, humidity, and air-quality sensor that sends readings over Wi-Fi. Sensor selection and firmware are outside the scope of this demonstration. No physical device has been built or tested.

## Component Selection

| Field | Submitted value |
| --- | --- |
| Module | ESP32-S3-WROOM-1-N8 |
| Antenna | Integrated PCB antenna |
| Flash | 8 MB |
| PSRAM | None |
| Module supply voltage at 3V3 pin | 5.0 V DC |
| Supply capacity allocated to the module | 500 mA |
| Module ambient operating-temperature target | -40 to 85 degrees C |

The temperature target applies to the environment immediately outside the module. It is not a validated operating rating for the complete sensor product.

## Power Design

The input power stage supplies a nominal 5.0 V rail directly to the module's 3V3 pin. No intermediate 3.3 V regulator or voltage conversion is included in revision A. The stated 500 mA is available supply capacity, not a claim of constant module consumption.

Document reference: AS-PWR-001 v1.0, section Power Path.

## Reset

The design description specifies a pull-up and RC delay on the module EN pin. Startup and reset timing measurements have not been provided. See AS-PWR-001 v1.0, section Reset.

## Antenna and Enclosure

- The integrated PCB antenna is placed beyond the edge of the host PCB.
- The design claims at least 15 mm of clear space around the PCB antenna in all directions inside a plastic enclosure.
- No external antenna, connector, or host-board RF feed is used.
- A nominal 50 ohm RF-path reference is recorded for the module's internal radio design; it is not an independently measured property of the host PCB.

See AS-RF-001 v1.0 for the baseline document assessment and missing evidence.

## Submitted Evidence

This package contains the product specification, a power document assessment, an RF document assessment, and a synthetic reviewer findings register. It contains no oscilloscope captures, schematics, PCB drawings, enclosure drawings, certification records, or physical test reports.

## References

- esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf: sections 1.1, 1.2 and 6.2.
- esp-hardware-design-guidelines-en-master-esp32s3.pdf: sections 1.3.3 and 1.4.7.
- Reference-fact IDs from facts.csv: REF-001 through REF-005, REF-024, REF-025, REF-031 and REF-032. The PDFs govern where CSV summaries omit conditions.
