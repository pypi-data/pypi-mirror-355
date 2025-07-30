# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: CC0-1.0

meta:
  id: vtf
  -author: b5327157
  -ksy-version: 1.1.0
  title: Valve Texture Format
  application: Source Engine
  file-extension: vtf
  xref:
    - mime: image/vnd.valve.source.texture
    - pronom: fmt/985
    - wikidata: Q28207412
  license: CC0-1.0
  ks-version: 0.9
  endian: le

doc-ref:
  - https://developer.valvesoftware.com/wiki/Valve_Texture_Format
  - https://github.com/NeilJed/VTFLib
  - https://github.com/StrataSource/VTFLib

seq:
  - id: header
    type: header

instances:
  body:
    pos: header.base.header_size - (header.logical.num_resources * 8)
    type: body

enums:
  image_format:
    0xffffffff: none
    0: rgba8888
    1: abgr8888
    2: rgb888
    3: bgr888
    4: rgb565
    5: i8
    6: ia88
    7: p8
    8: a8
    9: rgb888_bluescreen
    10: bgr888_bluescreen
    11: argb8888
    12: bgra8888
    13: dxt1
    14: dxt3
    15: dxt5
    16: bgrx8888
    17: bgr565
    18: bgrx5551
    19: bgra4444
    20: dxt1_onebitalpha
    21: bgra5551
    22: uv88
    23: uvwq8888
    24: rgba16161616f
    25: rgba16161616
    26: uvlx8888
    34: strata_source_ati2n
    35: strata_source_ati1n
    70: strata_source_bc7
    71: strata_source_bc6h

  resource_tag:
    0x010000: low_res_image
    0x300000: high_res_image
    0x100000: particle_sheet
    0x435243: crc
    0x4C4F44: lod_control
    0x54534F: extended_flags
    0x4B5644: key_values_data

types:
  b1_container:
    params:
      - id: value
        type: b1

  u4_container:
    params:
      - id: value
        type: u4

  header:
    seq:
      - id: base
        type: header_base

      - id: v7_0
        type: header_v7_0

      - id: v7_2
        if: base.version.minor >= 2
        type: header_v7_2

      - id: v7_3
        if: base.version.minor >= 3
        type: header_v7_3

      - id: logical
        type: header_logical

  header_base:
    seq:
      - id: magic
        contents: ['VTF', 0]

      - id: version
        type: version

      - id: header_size
        type: u4

  version:
    seq:
      - id: major
        type: u4
        valid:
          min: 7
          max: 7

      - id: minor
        type: u4
        valid:
          min: 0
          max: 6

  header_v7_0:
    seq:
      - id: width
        type: u2
        valid:
          min: 1

      - id: height
        type: u2
        valid:
          min: 1

      - id: flags
        type: u4

      - id: num_frames
        type: u2

      - id: first_frame
        type: u2

      - id: reserved0
        size: 4

      - id: reflectivity
        type: f4
        repeat: expr
        repeat-expr: 3

      - id: reserved1
        size: 4

      - id: bumpmap_scale
        type: f4

      - id: high_res_image_format
        type: u4
        enum: image_format

      - id: num_mipmaps
        type: u1

      - id: low_res_image_format
        type: u4
        enum: image_format

      - id: low_res_image_width
        type: u1

      - id: low_res_image_height
        type: u1

  header_v7_2:
    seq:
      - id: num_slices
        type: u2
        valid:
          min: 1

  header_v7_3:
    seq:
      - id: reserved2
        size: 3

      - id: num_resources
        type: u4

      - id: reserved3
        size: 8

  header_logical:
    instances:
      flags:
        type: header_flags

      num_faces:
        value: >-
          not flags.envmap ? 1 :
          _root.header.base.version.minor < 1 or _root.header.base.version.minor > 4 ? 6 :
          _root.header.v7_0.first_frame == 0xff ? 6 : 7

      num_slices:
        value: '(_root.header.base.version.minor >= 2 ? _root.header.v7_2.num_slices : 1)'

      num_resources:
        value: '(_root.header.base.version.minor >= 3 ? _root.header.v7_3.num_resources : 0)'

  header_flags:
    instances:
      onebitalpha:
        value: '(_root.header.v7_0.flags & 0x00001000 != 0 ? true : false)'

      eightbitalpha:
        value: '(_root.header.v7_0.flags & 0x00002000 != 0 ? true : false)'

      envmap:
        value: '(_root.header.v7_0.flags & 0x00004000 != 0 ? true : false)'

  body:
    seq:
    - id: low_res_image
      if: >-
        _root.header.base.version.minor < 3
        and _root.header.v7_0.low_res_image_format != image_format::none
        and _root.header.v7_0.low_res_image_width != 0
        and _root.header.v7_0.low_res_image_height != 0
      type: image(
          _root.header.v7_0.low_res_image_width,
          _root.header.v7_0.low_res_image_height,
          _root.header.v7_0.low_res_image_format
        )

    - id: high_res_image
      if: >-
        _root.header.base.version.minor < 3
        and _root.header.v7_0.high_res_image_format != image_format::none
      type: high_res_image

    - id: resources
      if: _root.header.base.version.minor >= 3
      type: resource
      repeat: expr
      repeat-expr: _root.header.logical.num_resources

  image:
    params:
      - id: logical_width
        type: u4

      - id: logical_height
        type: u4

      - id: image_format
        type: u4
        enum: image_format

    instances:
      image_format_to_bpp:
        type: image_format_to_bpp(image_format)

      bpp:
        value: image_format_to_bpp.bpp_container.value

      image_format_to_is_compressed:
        type: image_format_to_is_compressed(image_format)

      is_compressed:
        value: image_format_to_is_compressed.is_compressed_container.value

      physical_width:
        value: >-
          not is_compressed ? logical_width :
          logical_width >= 4 ? logical_width :
          4

      physical_height:
        value: >-
          not is_compressed ? logical_height :
          logical_height >= 4 ? logical_height :
          4

    seq:
      - id: image_data
        size: physical_width * physical_height * bpp / 8

  image_format_to_bpp:
    params:
      - id: image_format
        type: u4
        enum: image_format

    instances:
      bpp_container:
        type:
          switch-on: image_format
          cases:
            'image_format::rgba8888': u4_container(32)
            'image_format::abgr8888': u4_container(32)
            'image_format::rgb888': u4_container(24)
            'image_format::bgr888': u4_container(24)
            'image_format::rgb565': u4_container(16)
            'image_format::i8': u4_container(8)
            'image_format::ia88': u4_container(16)
            'image_format::p8': u4_container(8)
            'image_format::a8': u4_container(8)
            'image_format::rgb888_bluescreen': u4_container(24)
            'image_format::bgr888_bluescreen': u4_container(24)
            'image_format::argb8888': u4_container(32)
            'image_format::bgra8888': u4_container(32)
            'image_format::dxt1': u4_container(4)
            'image_format::dxt3': u4_container(8)
            'image_format::dxt5': u4_container(8)
            'image_format::bgrx8888': u4_container(32)
            'image_format::bgr565': u4_container(16)
            'image_format::bgrx5551': u4_container(16)
            'image_format::bgra4444': u4_container(16)
            'image_format::dxt1_onebitalpha': u4_container(4)
            'image_format::bgra5551': u4_container(16)
            'image_format::uv88': u4_container(16)
            'image_format::uvwq8888': u4_container(32)
            'image_format::rgba16161616f': u4_container(64)
            'image_format::rgba16161616': u4_container(64)
            'image_format::uvlx8888': u4_container(32)
            'image_format::strata_source_ati2n': u4_container(8)
            'image_format::strata_source_ati1n': u4_container(4)
            'image_format::strata_source_bc7': u4_container(8)
            'image_format::strata_source_bc6h': u4_container(8)

  image_format_to_is_compressed:
    params:
      - id: image_format
        type: u4
        enum: image_format

    instances:
      is_compressed_container:
        type:
          switch-on: image_format
          cases:
            _: b1_container(false)
            'image_format::dxt1': b1_container(true)
            'image_format::dxt3': b1_container(true)
            'image_format::dxt5': b1_container(true)
            'image_format::dxt1_onebitalpha': b1_container(true)
            'image_format::strata_source_ati2n': b1_container(true)
            'image_format::strata_source_ati1n': b1_container(true)
            'image_format::strata_source_bc7': b1_container(true)
            'image_format::strata_source_bc6h': b1_container(true)

  high_res_image:
    seq:
      - id: image_mipmaps
        type: image_mipmap(_index)
        repeat: expr
        repeat-expr: _root.header.v7_0.num_mipmaps

  image_mipmap:
    params:
      - id: mipmap_index
        type: u4

    instances:
      bit_shift:
        value: _root.header.v7_0.num_mipmaps - mipmap_index - 1

      width:
        value: >-
          (_root.header.v7_0.width >> bit_shift) >= 1
          ? (_root.header.v7_0.width >> bit_shift)
          : 1

      height:
        value: >-
          (_root.header.v7_0.height >> bit_shift) >= 1
          ? (_root.header.v7_0.height >> bit_shift)
          : 1

      num_slices:
        value: >-
          (_root.header.logical.num_slices >> bit_shift) >= 1
          ? (_root.header.logical.num_slices >> bit_shift)
          : 1

      image_format:
        value: _root.header.v7_0.high_res_image_format

    seq:
      - id: image_frames
        type: image_frame
        repeat: expr
        repeat-expr: _root.header.v7_0.num_frames

  image_frame:
    seq:
      - id: image_faces
        type: image_face
        repeat: expr
        repeat-expr: _root.header.logical.num_faces
        parent: _parent

  image_face:
    seq:
      - id: image_slices
        type: image(_parent.width, _parent.height, _parent.image_format)
        repeat: expr
        repeat-expr: _parent.num_slices
        parent: _parent

  resource:
    seq:
      - id: tag
        type: b24
        enum: resource_tag

      - id: flags
        type: u1

      - id: ofs_resource
        if: >-
          false
          or tag == resource_tag::low_res_image
          or tag == resource_tag::high_res_image
          or tag == resource_tag::particle_sheet
          or tag == resource_tag::key_values_data
        type: u4

      - if: >-
          true
          and tag != resource_tag::low_res_image
          and tag != resource_tag::high_res_image
          and tag != resource_tag::particle_sheet
          and tag != resource_tag::key_values_data
        type: u4

    instances:
      high_res_image:
        if: >-
          tag == resource_tag::high_res_image
          and _root.header.v7_0.high_res_image_format != image_format::none
        pos: ofs_resource
        type: high_res_image

      low_res_image:
        if: >-
          tag == resource_tag::low_res_image
          and _root.header.v7_0.low_res_image_format != image_format::none
        pos: ofs_resource
        type: image(
            _root.header.v7_0.low_res_image_width,
            _root.header.v7_0.low_res_image_height,
            _root.header.v7_0.low_res_image_format
          )
