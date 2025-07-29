from pm4py.algo.discovery.inductive.fall_through.activity_once_per_trace import ActivityOncePerTraceUVCL
from powl.algo.discovery.inductive.fall_through.activity_concurrent import POWLActivityConcurrentUVCL


class POWLActivityOncePerTraceUVCL(ActivityOncePerTraceUVCL, POWLActivityConcurrentUVCL):
    pass
