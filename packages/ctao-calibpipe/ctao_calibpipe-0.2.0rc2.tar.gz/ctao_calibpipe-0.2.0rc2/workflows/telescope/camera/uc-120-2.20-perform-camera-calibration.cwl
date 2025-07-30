#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: Workflow

requirements:
  SubworkflowFeatureRequirement: {}

label: Perform camera calibration
doc: >
    Camera calibration data (from telescope-level calibration events) will be recorded alongside science data during and around each observation night by ACADA. Different calibration event types will be recorded to the different streams at this stage. Interleaved flat-field and sky pedestal events are tagged at the telescope level, allowing the data to directly align with the functional decomposition of the CalibPipe and avoid the need of additional event-type filtering.

    Following this, pixel- and channel-wise camera calibration coefficients are calculated as a function of time. This process includes the computation of aggregated time-series statistics for the calibration events, as well as the detection of non-nominal pixels and time periods (UC-120-2.21). The aggregated statistics are further processed to derive the sky pedestal offsets per waveform sample, flat-fielding coefficients, and pixel timing corrections.

    Additionally, the CalibPipe calculates the absolute gain for each pixel and gain channel as a function of time. This process will ultimately yield a multiplicative coefficient for the absolute calibration of extracted charge into photoelectrons. To achieve accurate absolute gain and charge calibration, CalibPipe derives telescope-specific systematic corrections (UC-120-2.22) and the conversion factors from digital counts to single photoelectrons (UC-120-2.23).

inputs:
  dl0_input_data:
    type: File
    label: DL0 calibration
    doc: >
        DL0 calibration data (observation or simulation) for calibration events.
  ped_process_config:
    type: File
    label: Pedestal process config
    doc: >
        Configuration file for the pedestal image extraction.
  ff_process_config:
    type: File
    label: Flat-field process config
    doc: >
        Configuration file for the flat-field image extraction.
  ped_img_pix_stats_config:
    type: File
    label: Pedestal pixel stats config
    doc: >
        Configuration file for the pixel statistics extraction of the charge for pedestal events.
  ff_img_pix_stats_config:
    type: File
    label: Flat-field pixel stats config
    doc: >
        Configuration file for the pixel statistics extraction of the charge for flat-field events.
  ff_time_pix_stats_config:
    type: File
    label: Peak time pixel stats config
    doc: >
        Configuration file for the pixel statistics extraction of the peak arrival time for flat-field events.
  camcalib_coeffs_config:
    type: File
    label: Camcalib coeffs config
    doc: >
        Configuration file for the calculation of camera calibration coefficients using the FFactor method.
  log-level:
    type: string?
    doc: >
        Log level for the process. Default is INFO.
outputs:
  processed_dl1_mon_data:
    type: File
    label: DL1 monitoring
    doc: >
        DL1 monitoring data containing camera calibration coefficients.
    outputSource: camcalib_coeffs/dl1_mon_data

steps:
  aggregate_pix_stats:
    run: uc-120-2.21-assess-statistical-description.cwl
    in:
      dl0_input_data: dl0_input_data
      ff_img_pix_stats_config: ff_img_pix_stats_config
      ped_img_pix_stats_config: ped_img_pix_stats_config
      ff_time_pix_stats_config: ff_time_pix_stats_config
      ped_process_config: ped_process_config
      ff_process_config: ff_process_config
      log-level: log-level
    out: [dl1_mon_data]
  camcalib_coeffs:
    run: calibpipe-camcalib-tool.cwl
    in:
      camcalib_tool_input: aggregate_pix_stats/dl1_mon_data
      configuration: camcalib_coeffs_config
      log-level: log-level
    out:  [dl1_mon_data]
