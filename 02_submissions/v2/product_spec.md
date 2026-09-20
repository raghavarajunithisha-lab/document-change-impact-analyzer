# AirSense Environmental Sensor

> SYNTHETIC DEMONSTRATION DOCUMENT. This fictional product and its design claims are test data, not an Espressif product, actual test evidence, or a Seamflow customer submission. Do not use this document to build hardware.

- Document ID: AS-PRD-001
- Version: 2.0
- Supersedes: AS-PRD-001 v1.0
- Status: Submitted for document review
- Product ID: AS-ENV-001
- Hardware revision: B

## Product Purpose

AirSense is a fictional temperature, humidity, and air-quality sensor that sends readings over Wi-Fi. Sensor selection and firmware are outside the scope of this demonstration. No physical device has been built or tested.

## Component Selection

| Field | Submitted value |
| --- | --- |
| Module | ESP32-S3-WROOM-1U-N8 |
| Antenna | External antenna via module connector |
| Flash | 8 MB |
| PSRAM | None |
| Module supply voltage at 3V3 pin | 3.3 V DC |
| Supply capacity allocated to the module | 250 mA |
| Module ambient operating-temperature target | -40 to 85 degrees C |

The temperature target applies to the environment immediately outside the module. It is not a validated operating rating for the complete sensor product.

## Power Design

Revision B adds a regulator between the 5.0 V input and the module's 3V3 pin. Its output is nominally 3.3 V, with a specified tolerance of +/-2 percent under its intended load conditions. No 5.0 V connection goes directly to the module supply pin.

The regulator has a continuous output capacity of 250 mA, allocated exclusively to the module; other product loads use a separate rail. This is the available capacity, not a claim of constant module consumption. RF-load transient measurements are not included.

AS-PWR-001 v1.0 is included as the previous assessment of hardware revision A, not as an assessment of this revised design. Its 5.0 V and 500 mA descriptions refer to the earlier design.

## Reset

Revision B retains a 10 kohm pull-up and a 1 uF capacitor on module EN. The newly submitted synthetic report AS-RST-001 v1.0 records startup and reset timings for the revision B configuration. All values in that report are invented demonstration measurements.

## Antenna and Enclosure

- The WROOM-1U module uses its external antenna connector; the integrated PCB antenna from revision A is no longer present.
- The proposed external antenna is fictional part AS-ANT-01, described as a 2.4 GHz antenna with a nominal 50 ohm feed through a coaxial cable.
- No host-PCB RF feed trace is added; the module connector connects to the antenna by cable. The nominal impedance is a design claim, not a measurement.
- The proposed installation provides a minimum 5 mm clearance between the external antenna radiating element and nearby housing or hardware inside a plastic enclosure.
- The external antenna supplier's installation guide, gain data, and integration approval evidence are not supplied.
- Enclosure material is unchanged; antenna mounting geometry is revised for AS-ANT-01.

AS-RF-001 v1.0 remains the previous assessment of revision A's integrated PCB antenna and enclosure arrangement. It has not been reissued for revision B.

## Submitted Evidence

| File | Document and version | Role in this package |
| --- | --- | --- |
| product_spec.md | AS-PRD-001 v2.0 | Current manufacturer specification for revision B |
| power_assessment.md | AS-PWR-001 v1.0 | Historical reviewer assessment of revision A; carried forward unchanged |
| rf_assessment.md | AS-RF-001 v1.0 | Historical reviewer assessment of revision A; carried forward unchanged |
| review_findings.json | Findings F-001 to F-003 from review of v1.0 | Previous open findings to reassess; not updated outcomes |
| reset_timing_report.md | AS-RST-001 v1.0 | New synthetic timing evidence for revision B |

No final-product throughput or range report, external-antenna specification, certification record, or physical test evidence is supplied. The historical assessments retain their original document versions even though they are included in the V2 submission folder. Reviewer decisions on V2 are not part of this input package.

## References

- esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf: sections 1.1, 1.2, 4.5 and 6.2.
- esp-hardware-design-guidelines-en-master-esp32s3.pdf: sections 1.3.3 and 1.4.7.
- AS-RST-001 v1.0, sections Configuration, Procedure and Recorded Results.
- Relevant reference-fact IDs from facts.csv include REF-001, REF-002, REF-003, REF-024 and REF-025. Use the source PDFs for exact variant applicability and conditions; WROOM-1-only rows do not establish WROOM-1U specifications.
