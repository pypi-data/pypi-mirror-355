#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: CommandLineTool

baseCommand: ctapipe-process

label: Process Tool
doc: >
    The ctapipe-process tool is a command line tool that processes DL0 data and produces DL1 data. It is part of the
    ctapipe software package and is used to process data from the Cherenkov Telescope Array Observatory (CTAO).

inputs:
  process_tool_input:
    type: File
    inputBinding:
      prefix: --input
    label: DL0
    doc: >
        DL0 data or simulation produced by ACADA or simtel_array, respectively.

  process_tool_output:
    type: [File, string]
    inputBinding:
      prefix: --output
    label: DL1
    doc: >
        DL1 data file including images.

  configuration:
    type: File
    inputBinding:
      prefix: --config

  log-level:
    type: string?
    inputBinding:
      prefix: --log-level

outputs:
  dl1_data:
    type: File
    outputBinding:
      glob: "*.dl1.h5"
