from enum import Enum


class AwakeStatus(str, Enum):
    Awake: str = "AWAKE"
    Asleep: str = "ASLEEP"
    WakingUp: str = "WAKING_UP"
    GoingToSleep: str = "GOING_TO_SLEEP"


class StepStatus(str, Enum):
    NotStarted: str = "not_started"
    Successful: str = "successful"
    InProgress: str = "in_progress"
    Failed: str = "failed"
    Cancelled: str = "cancelled"


class RobotStatus(Enum):
    Available: str = "available"
    Busy: str = "busy"
    Offline: str = "offline"


class MissionStatus(str, Enum):
    StartRequested: str = "START_REQUESTED"
    PauseRequested: str = "PAUSE_REQUESTED"
    ResumeRequested: str = "RESUME_REQUESTED"
    Rejected: str = "REJECTED"
    WakingUp: str = "WAKING_UP"
    Starting: str = "STARTING"
    InProgress: str = "IN_PROGRESS"
    Paused: str = "PAUSED"
    Completed: str = "COMPLETED"

    def to_mission_status(self) -> StepStatus:
        return {
            MissionStatus.StartRequested: StepStatus.NotStarted,
            MissionStatus.PauseRequested: StepStatus.InProgress,
            # Current implementation paused is cancelled
            MissionStatus.ResumeRequested: StepStatus.Cancelled,
            MissionStatus.Rejected: StepStatus.Failed,
            MissionStatus.WakingUp: StepStatus.NotStarted,
            MissionStatus.Starting: StepStatus.NotStarted,
            MissionStatus.InProgress: StepStatus.InProgress,
            MissionStatus.Paused: StepStatus.Cancelled,
            MissionStatus.Completed: StepStatus.Successful,
        }[self]
