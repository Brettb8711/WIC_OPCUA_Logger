import struct

def map_structures(datatype_name):
    """
    Maps OPC UA data types to Python classes.
    
    Parameters
    ----------
    datatype_name : str
        The name of the OPC UA data type.
        
    Returns
    -------
    class
        The corresponding Python class for the data type.
    """
    mapping = {
        "JobInfo": JobInfo,
        "PartInfo": PartInfo,
        "RunInfo": RunInfo,
        "RunPartInfo": RunPartInfo,
        "PlanInfo": PlanInfo,
        "RunStates": RunStates,
        "PlateOperatingData": PlateOperatingData,
        "PartOperatingData": PartOperatingData,
    }
    
    return mapping.get(datatype_name, None)

class OpcuaStructBase:
    def read_guid(self, data, offset):
        guid_bytes = data[offset:offset+16]
        guid = (
            struct.unpack('<I', guid_bytes[0:4])[0],
            struct.unpack('<H', guid_bytes[4:6])[0],
            struct.unpack('<H', guid_bytes[6:8])[0],
            ''.join(f'{b:02x}' for b in guid_bytes[8:])
        )
        guid_str = f'{guid[0]:08x}-{guid[1]:04x}-{guid[2]:04x}-{guid[3]}'
        return guid_str, offset + 16

    def read_string(self, data, offset):
        strlen = struct.unpack('<i', data[offset:offset+4])[0]
        offset += 4
        if strlen == -1:
            return None, offset
        s = data[offset:offset+strlen].decode('utf-8')
        return s, offset + strlen

    def read_uint32(self, data, offset):
        val = struct.unpack('<I', data[offset:offset+4])[0]
        return val, offset + 4

    def read_int32(self, data, offset):
        val = struct.unpack('<i', data[offset:offset+4])[0]
        return val, offset + 4

    def read_double(self, data, offset):
        val = struct.unpack('<d', data[offset:offset+8])[0]
        return val, offset + 8

    def read_utctime(self, data, offset):
        val = struct.unpack('<Q', data[offset:offset+8])[0]
        return val, offset + 8
    
    def read_planstate(self, data, offset):
        data, offset = self.read_int32(data, offset)
        match data:
            case 0: return "Inactive", offset
            case 1: return "Started", offset  
            case 2: return "Completed", offset
            case 3: return "PartiallyCompleted", offset
            case 4: return "Failed", offset
    
    def read_materialFormat(self, data, offset):
        data, offset = self.read_int32(data, offset)
        match data:
            case 0: return "Sheet", offset
            case 1: return "Profile", offset  

    def read_tubeProfile(self, data, offset):
        data, offset = self.read_int32(data, offset)
        match data:
            case 0: return "No Profile", offset
            case 1: return "Circular", offset  
            case 2: return "Rectangular", offset
            case 3: return "Polygon", offset
            case 4: return "UShape", offset
            case 5: return "LShape", offset
            case 6: return "Ellipse", offset

    def read_partCutState(self, data, offset):
        data, offset = self.read_int32(data, offset)
        match data:
            case 0: return "Undefined", offset
            case 1: return "Cut Completed", offset  
            case 2: return "Cut Completed with breaks", offset
            case 3: return "Cut Aborted", offset

class JobInfo(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.JobGuid, offset = self.read_guid(raw_bytes, offset)
        self.ExternalJobGuid, offset = self.read_guid(raw_bytes, offset)
        self.Name, offset = self.read_string(raw_bytes, offset)
        self.Description, offset = self.read_string(raw_bytes, offset)
        self.UserInfo1, offset = self.read_string(raw_bytes, offset)
        self.UserInfo2, offset = self.read_string(raw_bytes, offset)
        self.UserInfo3, offset = self.read_string(raw_bytes, offset)
        self.MeasurementSystem, offset = self.read_uint32(raw_bytes, offset)
        self.NcProgramFile, offset = self.read_string(raw_bytes, offset)

    def as_dict(self):
        return {
            "JobGuid": self.JobGuid,
            "ExternalJobGuid": self.ExternalJobGuid,
            "Name": self.Name,
            "Description": self.Description,
            "UserInfo1": self.UserInfo1,
            "UserInfo2": self.UserInfo2,
            "UserInfo3": self.UserInfo3,
            "MeasurementSystem": self.MeasurementSystem,
            "NcProgramFile": self.NcProgramFile,
        }

class PartInfo(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.JobGuid, offset = self.read_guid(raw_bytes, offset)
        self.PartID, offset = self.read_uint32(raw_bytes, offset)
        self.PartRefIds, offset = self.read_string(raw_bytes, offset)
        self.Name, offset = self.read_string(raw_bytes, offset)
        self.Description, offset = self.read_string(raw_bytes, offset)
        self.Quantity, offset = self.read_uint32(raw_bytes, offset)
        self.OrderInfo, offset = self.read_string(raw_bytes, offset)
        self.UserInfo1, offset = self.read_string(raw_bytes, offset)
        self.UserInfo2, offset = self.read_string(raw_bytes, offset)
        self.UserInfo3, offset = self.read_string(raw_bytes, offset)

    def as_dict(self):
        return {
            "JobGuid": self.JobGuid,
            "PartID": self.PartID,
            "Name": self.Name,
            "Description": self.Description,
            "Quantity": self.Quantity,
            "UserInfo1": self.UserInfo1,
            "UserInfo2": self.UserInfo2,
            "UserInfo3": self.UserInfo3,
            "PartRefIds": self.PartRefIds,
            "OrderInfo": self.OrderInfo,
        }

class RunInfo(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.JobGuid, offset = self.read_guid(raw_bytes, offset)
        self.PlanGuid, offset = self.read_guid(raw_bytes, offset)
        self.RunGuid, offset = self.read_guid(raw_bytes, offset)
        self.SortGuid, offset = self.read_guid(raw_bytes, offset)
        self.RunNumber, offset = self.read_int32(raw_bytes, offset)
        self.CutState, offset = self.read_int32(raw_bytes, offset)
        self.CutStartTime, offset = self.read_utctime(raw_bytes, offset)
        self.CutEndTime, offset = self.read_utctime(raw_bytes, offset)
        self.SortState, offset = self.read_int32(raw_bytes, offset)
        self.SortStartTime, offset = self.read_utctime(raw_bytes, offset)
        self.SortEndTime, offset = self.read_utctime(raw_bytes, offset)
        self.ActualCutTime, offset = self.read_double(raw_bytes, offset)
        self.ActualStopTime, offset = self.read_double(raw_bytes, offset)
        self.ActualWaitTime, offset = self.read_double(raw_bytes, offset)
        self.SheetOffsetX, offset = self.read_double(raw_bytes, offset)
        self.SheetOffsetY, offset = self.read_double(raw_bytes, offset)
        self.SheetAngle, offset = self.read_double(raw_bytes, offset)
        self.ChargeInfo, offset = self.read_string(raw_bytes, offset)
        self.StorageInfo1, offset = self.read_string(raw_bytes, offset)
        self.StorageInfo2, offset = self.read_string(raw_bytes, offset)
        self.StorageInfo3, offset = self.read_string(raw_bytes, offset)

    def as_dict(self):
        return {
            "JobGuid": self.JobGuid,
            "PlanGuid": self.PlanGuid,
            "RunGuid": self.RunGuid,
            "SortGuid": self.SortGuid,
            "RunNumber": self.RunNumber,
            "CutState": self.CutState,
            "CutStartTime": self.CutStartTime,
            "CutEndTime": self.CutEndTime,
            "SortState": self.SortState,
            "SortStartTime": self.SortStartTime,
            "SortEndTime": self.SortEndTime,
            "ActualCutTime": self.ActualCutTime,
            "ActualStopTime": self.ActualStopTime,
            "ActualWaitTime": self.ActualWaitTime,
            "SheetOffsetX": self.SheetOffsetX,
            "SheetOffsetY": self.SheetOffsetY,
            "SheetAngle": self.SheetAngle,
            "ChargeInfo": self.ChargeInfo,
            "StorageInfo1": self.StorageInfo1,
            "StorageInfo2": self.StorageInfo2,
            "StorageInfo3": self.StorageInfo3,
        }

class RunPartInfo(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.JobGuid, offset = self.read_guid(raw_bytes, offset)
        self.PlanGuid, offset = self.read_guid(raw_bytes, offset)
        self.RunGuid, offset = self.read_guid(raw_bytes, offset)
        self.PartId, offset = self.read_uint32(raw_bytes, offset)
        self.PartRefId, offset = self.read_uint32(raw_bytes, offset)
        self.CutState, offset = self.read_int32(raw_bytes, offset)
        self.CutStartTime, offset = self.read_utctime(raw_bytes, offset)
        self.CutEndTime, offset = self.read_utctime(raw_bytes, offset)
        self.SortState, offset = self.read_int32(raw_bytes, offset)
        self.SortStartTime, offset = self.read_utctime(raw_bytes, offset)
        self.SortEndTime, offset = self.read_utctime(raw_bytes, offset)
        self.ActualCutTime, offset = self.read_double(raw_bytes, offset)
        self.ActualStopTime, offset = self.read_double(raw_bytes, offset)
        self.ActualWaitTime, offset = self.read_double(raw_bytes, offset)
        self.StackAreaType, offset = self.read_int32(raw_bytes, offset)

    def as_dict(self):
        return {
            "JobGuid": self.JobGuid,
            "PlanGuid": self.PlanGuid,
            "RunGuid": self.RunGuid,
            "PartId": self.PartId,
            "PartRefId": self.PartRefId,
            "CutState": self.CutState,
            "CutStartTime": self.CutStartTime,
            "CutEndTime": self.CutEndTime,
            "SortState": self.SortState,
            "SortStartTime": self.SortStartTime,
            "SortEndTime": self.SortEndTime,
            "ActualCutTime": self.ActualCutTime,
            "ActualStopTime": self.ActualStopTime,
            "ActualWaitTime": self.ActualWaitTime,
            "StackAreaType": self.StackAreaType,
        }

class PlanInfo(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.JobGuid, offset = self.read_guid(raw_bytes, offset)
        self.PlanGuid, offset = self.read_guid(raw_bytes, offset)
        self.Name, offset = self.read_string(raw_bytes, offset)
        self.Description, offset = self.read_string(raw_bytes, offset)
        self.SizeX, offset = self.read_double(raw_bytes, offset)
        self.SizeY, offset = self.read_double(raw_bytes, offset)
        self.TotalRuns, offset = self.read_uint32(raw_bytes, offset)
        self.TotalParts, offset = self.read_uint32(raw_bytes, offset)
        self.PlanState, offset = self.read_planstate(raw_bytes, offset)
        self.EstimatedCutTime, offset = self.read_double(raw_bytes, offset)
        self.MaterialFormat, offset = self.read_materialFormat(raw_bytes, offset)
        self.MaterialName, offset = self.read_string(raw_bytes, offset)
        self.MaterialSizeX, offset = self.read_double(raw_bytes, offset)
        self.MaterialSizeY, offset = self.read_double(raw_bytes, offset)
        self.MaterialThickness, offset = self.read_double(raw_bytes, offset)
        self.TubeProfile, offset = self.read_tubeProfile(raw_bytes, offset)
        self.ProfileDimA, offset = self.read_double(raw_bytes, offset)
        self.ProfileDimB, offset = self.read_double(raw_bytes, offset)
        self.ProfileDimC, offset = self.read_double(raw_bytes, offset)
        self.Weight, offset = self.read_double(raw_bytes, offset)
        self.Waste, offset = self.read_double(raw_bytes, offset)
        self.ArticleInfo, offset = self.read_string(raw_bytes, offset)
        self.ChargeInfo, offset = self.read_string(raw_bytes, offset)
        self.MaterialInfo1, offset = self.read_string(raw_bytes, offset)
        self.MaterialInfo2, offset = self.read_string(raw_bytes, offset)
        self.MaterialInfo3, offset = self.read_string(raw_bytes, offset)
        self.ParamterFile, offset = self.read_string(raw_bytes, offset)
        self.SpacerPlateInfo, offset = self.read_string(raw_bytes, offset)

    def as_dict(self):
        return {
            "JobGuid": self.JobGuid,
            "PlanGuid": self.PlanGuid,
            "Name": self.Name,
            "Description": self.Description,
            "SizeX": self.SizeX,
            "SizeY": self.SizeY,
            "TotalRuns": self.TotalRuns,
            "TotalParts": self.TotalParts,
            "PlanState": self.PlanState,
            "EstimatedCutTime": self.EstimatedCutTime,
            "MaterialFormat": self.MaterialFormat,
            "MaterialName": self.MaterialName,
            "MaterialSizeX": self.MaterialSizeX,
            "MaterialSizeY": self.MaterialSizeY,
            "MaterialThickness": self.MaterialThickness,
            "TubeProfile": self.TubeProfile,
            "ProfileDimA": self.ProfileDimA,
            "ProfileDimB": self.ProfileDimB,
            "ProfileDimC": self.ProfileDimC,
            "Weight": self.Weight,
            "Waste": self.Waste,
            "ArticleInfo": self.ArticleInfo,
            "ChargeInfo": self.ChargeInfo,
            "MaterialInfo1": self.MaterialInfo1,
            "MaterialInfo2": self.MaterialInfo2,
            "MaterialInfo3": self.MaterialInfo3,
            "ParamterFile": self.ParamterFile,
            "SpacerPlateInfo": self.SpacerPlateInfo,
        }
    
class RunStates(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.Timestamp, offset = self.read_utctime(raw_bytes, offset)
        self.JobGuid, offset = self.read_guid(raw_bytes, offset)
        self.PlanGuid, offset = self.read_guid(raw_bytes, offset)
        self.RunGuid, offset = self.read_guid(raw_bytes, offset)
        self.RunName, offset = self.read_string(raw_bytes, offset)
        self.CurrentState, offset = self.read_string(raw_bytes, offset)
        self.NextState, offset = self.read_string(raw_bytes, offset)
    
    def as_dict(self):
        return {
            "Timestamp": self.Timestamp,
            "JobGuid": self.JobGuid,
            "PlanGuid": self.PlanGuid,
            "RunGuid": self.RunGuid,
            "RunName": self.RunName,
            "CurrentState": self.CurrentState,
            "NextState": self.NextState,
        }
        
class PlateOperatingData(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.Timestamp, offset = self.read_utctime(raw_bytes, offset)
        self.PlateGuid, offset = self.read_guid(raw_bytes, offset)
        self.PlateStae, offset = self.read_partCutState(raw_bytes, offset)
        self.CuttingTime, offset = self.read_double(raw_bytes, offset)
        self.SystemWaitTime, offset = self.read_double(raw_bytes, offset)
        self.StopTime, offset = self.read_double(raw_bytes, offset)
        self.OperateEvent, offset = self.read_int32(raw_bytes, offset)
        self.OperateStops, offset = self.read_int32(raw_bytes, offset)
        self.SystemEvents, offset = self.read_int32(raw_bytes, offset)
        self.SystemStops, offset = self.read_int32(raw_bytes, offset)
        self.BreakOffs, offset = self.read_int32(raw_bytes, offset)

    def as_dict(self):
        return {
            "Timestamp": self.Timestamp,
            "PlateGuid": self.PlateGuid,
            "PlateStae": self.PlateStae,
            "CuttingTime": self.CuttingTime,
            "SystemWaitTime": self.SystemWaitTime,
            "StopTime": self.StopTime,
            "OperateEvent": self.OperateEvent,
            "OperateStops": self.OperateStops,
            "SystemEvents": self.SystemEvents,
            "SystemStops": self.SystemStops,
            "BreakOffs": self.BreakOffs,
        }

class PartOperatingData(OpcuaStructBase):
    def __init__(self, raw_bytes):
        offset = 0
        self.Timestamp, offset = self.read_utctime(raw_bytes, offset)
        self.PlateGuid, offset = self.read_guid(raw_bytes, offset)
        self.PartID, offset = self.read_uint32(raw_bytes, offset)
        self.PartState, offset = self.read_partCutState(raw_bytes, offset)
        self.CuttingTime, offset = self.read_double(raw_bytes, offset)
        self.SystemWaitTime, offset = self.read_double(raw_bytes, offset)
        self.StopTime, offset = self.read_double(raw_bytes, offset)
        self.OperateEvent, offset = self.read_int32(raw_bytes, offset)
        self.OperateStops, offset = self.read_int32(raw_bytes, offset)
        self.SystemEvents, offset = self.read_int32(raw_bytes, offset)
        self.SystemStops, offset = self.read_int32(raw_bytes, offset)
        self.BreakOffs, offset = self.read_int32(raw_bytes, offset)
    
    def as_dict(self):
        return {
            "Timestamp": self.Timestamp,
            "PlateGuid": self.PlateGuid,
            "PartID": self.PartID,
            "PartState": self.PartState,
            "CuttingTime": self.CuttingTime,
            "SystemWaitTime": self.SystemWaitTime,
            "StopTime": self.StopTime,
            "OperateEvent": self.OperateEvent,
            "OperateStops": self.OperateStops,
            "SystemEvents": self.SystemEvents,
            "SystemStops": self.SystemStops,
            "BreakOffs": self.BreakOffs,
        }

