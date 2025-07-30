#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: Workflow
requirements:
  InlineJavascriptRequirement: {}
  StepInputExpressionRequirement: {}
label: Assess the statistical description of calibration events
doc: >
    When DPPS receives a new DL0 data product, the CalibPipe is triggered to process the calibration events. The CalibPipe performs charge integration and peak time extraction for the entire set of calibration events, and computes aggregated time-series statistics, including the mean, median, and standard deviation.

    Using these aggregated statistics, the CalibPipe identifies faulty camera pixels, such as those affected by starlight, by applying various outlier detection criteria. Time periods with a significant number of faulty pixels, exceeding a predefined threshold, are flagged as invalid. A refined treatment can then be applied to these time periods to account for the issues.

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
  log-level:
    type: string?
    doc: >
        Log level for the process. Default is INFO.

outputs:
  dl1_mon_data:
    type: File
    label: DL1 monitoring
    doc: >
        Aggregated pixel statistics (observation or simulation) for calibration events.
    outputSource: agg_stats_time/dl1_mon_data

steps:
  process_pedestal:
    run: ../ctapipe-process-tool.cwl
    in:
      process_tool_input: dl0_input_data
      process_tool_output:
        valueFrom: $(inputs.dl0_input_data.basename.replace(/\..*$/, '.pedestal.dl1.h5'))
      configuration: ped_process_config
      log-level: log-level
    out: [dl1_data]
  process_flatfield:
    run: ../ctapipe-process-tool.cwl
    in:
      process_tool_input: dl0_input_data
      process_tool_output:
        valueFrom: $(inputs.dl0_input_data.basename.replace(/\..*$/, '.flatfield.dl1.h5'))
      configuration: ff_process_config
      log-level: log-level
    out: [dl1_data]
  agg_stats_pedestal:
    run: ../ctapipe-pix-stats-tool.cwl
    in:
      pix_stats_tool_input: process_pedestal/dl1_data
      pix_stats_tool_output:
        valueFrom: $(inputs.dl0_input_data.basename.replace(/\..*$/, '.monitoring.dl1.h5'))
      configuration: ped_img_pix_stats_config
      log-level: log-level
    out: [dl1_mon_data]
  agg_stats_flatfield:
    run: ../ctapipe-pix-stats-tool.cwl
    in:
      pix_stats_tool_input: process_flatfield/dl1_data
      pix_stats_tool_output: agg_stats_pedestal/dl1_mon_data
      configuration: ff_img_pix_stats_config
      log-level: log-level
    out: [dl1_mon_data]
  agg_stats_time:
    run: ../ctapipe-pix-stats-tool.cwl
    in:
      pix_stats_tool_input: process_flatfield/dl1_data
      pix_stats_tool_output: agg_stats_flatfield/dl1_mon_data
      configuration: ff_time_pix_stats_config
      log-level: log-level
    out: [dl1_mon_data]
