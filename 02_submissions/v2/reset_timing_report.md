# AirSense Reset Timing Report

> SYNTHETIC DEMONSTRATION EVIDENCE. All setup descriptions, run identifiers, and readings below are invented for a software test fixture. They are not actual laboratory observations, simulator outputs, or Espressif measurements. No hardware was built or tested.

- Document ID: AS-RST-001
- Version: 1.0
- Product ID: AS-ENV-001
- Hardware revision: B
- Related specification: AS-PRD-001 v2.0
- Related earlier finding: F-002
- Status: Submitted for reviewer evaluation; no reviewer approval recorded
- Evidence scope: Startup and reset timing under the stated fictional conditions only

## Configuration

| Parameter | Fictional setup |
| --- | --- |
| Module | ESP32-S3-WROOM-1U-N8 |
| Upstream input | 5.0 V |
| Regulator output | 3.3 V nominal |
| Regulator continuous output capacity | 250 mA |
| Reset network | 10 kohm EN pull-up; 1 uF EN capacitor |
| Ambient condition | 25 degrees C |
| Firmware state | RF disabled; startup/reset observation only |
| Observation channels | Module 3V3 rail and module EN |

## Procedure

For each fictional startup run, measure the interval between the module supply reaching a stable operating level and EN reaching its enable threshold. Record the interval as rail-stabilization time before enable.

For each fictional reset run, record how long EN remains below the applicable reset-low threshold. Record this as reset assertion duration. Timing values in the results are defined using the datasheet's signal thresholds, not merely the start of an RC waveform.

The reference minimum for each interval is 50 microseconds (hardware guidelines section 1.3.3, Table 2; module datasheet section 4.5). These timing checks do not verify available current under RF load.

## Recorded Results

All entries in this table are fabricated values for the synthetic fixture.

| Run ID | Supply during stable interval (V) | Rail stabilization before enable (microseconds) | Reset assertion duration (microseconds) |
| --- | --- | --- | --- |
| SYN-B-01 | 3.30 | 120 | 100 |
| SYN-B-02 | 3.29 | 118 | 102 |
| SYN-B-03 | 3.31 | 122 | 101 |

## Limitations

The table supplies traceable mock timing evidence for revision B so the software can assess F-002. It supplies no real measurement assurance. It does not cover temperature extremes, manufacturing tolerance, slow or unstable inputs, RF activity, regulator overload, or complete product reliability. No raw oscilloscope files or actual instrument records exist.

Finding status and closure decisions belong to the reviewer output. Merely adding this report must not be treated as resolving every power-related finding.
