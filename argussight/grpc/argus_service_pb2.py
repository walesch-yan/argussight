# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: argus_service.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13\x61rgus_service.proto\x12\nargussight\"C\n\x15StartProcessesRequest\x12*\n\tprocesses\x18\x01 \x03(\x0b\x32\x17.argussight.ProcessInfo\"?\n\x16StartProcessesResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x15\n\rerror_message\x18\x02 \x01(\t\"*\n\x19TerminateProcessesRequest\x12\r\n\x05names\x18\x01 \x03(\t\"C\n\x1aTerminateProcessesResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x15\n\rerror_message\x18\x02 \x01(\t\"7\n\x16ManageProcessesRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"@\n\x17ManageProcessesResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x15\n\rerror_message\x18\x02 \x01(\t\"7\n\x0bProcessInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x03 \x03(\t2\xaa\x02\n\x0eSpawnerService\x12W\n\x0eStartProcesses\x12!.argussight.StartProcessesRequest\x1a\".argussight.StartProcessesResponse\x12\x63\n\x12TerminateProcesses\x12%.argussight.TerminateProcessesRequest\x1a&.argussight.TerminateProcessesResponse\x12Z\n\x0fManageProcesses\x12\".argussight.ManageProcessesRequest\x1a#.argussight.ManageProcessesResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'argus_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_STARTPROCESSESREQUEST']._serialized_start=35
  _globals['_STARTPROCESSESREQUEST']._serialized_end=102
  _globals['_STARTPROCESSESRESPONSE']._serialized_start=104
  _globals['_STARTPROCESSESRESPONSE']._serialized_end=167
  _globals['_TERMINATEPROCESSESREQUEST']._serialized_start=169
  _globals['_TERMINATEPROCESSESREQUEST']._serialized_end=211
  _globals['_TERMINATEPROCESSESRESPONSE']._serialized_start=213
  _globals['_TERMINATEPROCESSESRESPONSE']._serialized_end=280
  _globals['_MANAGEPROCESSESREQUEST']._serialized_start=282
  _globals['_MANAGEPROCESSESREQUEST']._serialized_end=337
  _globals['_MANAGEPROCESSESRESPONSE']._serialized_start=339
  _globals['_MANAGEPROCESSESRESPONSE']._serialized_end=403
  _globals['_PROCESSINFO']._serialized_start=405
  _globals['_PROCESSINFO']._serialized_end=460
  _globals['_SPAWNERSERVICE']._serialized_start=463
  _globals['_SPAWNERSERVICE']._serialized_end=761
# @@protoc_insertion_point(module_scope)
