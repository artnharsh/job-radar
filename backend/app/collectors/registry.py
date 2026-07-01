"""
Collector registry.

Single place that maps source names to collector instances.
The scheduler imports this to know which collectors to run.
Adding a new collector = one line here.
"""

from app.collectors.apis.greenhouse import GreenhouseCollector
from app.collectors.apis.lever import LeverCollector
from app.collectors.apis.ashby import AshbyCollector
from app.collectors.apis.remotive import RemotiveCollector
from app.collectors.apis.jobicy import JobicyCollector
from app.collectors.apis.arbeitnow import ArbeitnowCollector
from app.collectors.apis.adzuna import AdzunaCollector
from app.collectors.apis.themuse import TheMuseCollector
from app.collectors.grey.remoteok import RemoteOKCollector
from app.collectors.grey.hn_hiring import HNHiringCollector
from app.collectors.grey.wellfound import WellfoundCollector
from app.collectors.grey.yc_jobs import YCJobsCollector
from app.collectors.grey.builtin import BuiltInCollector
from app.collectors.grey.weworkremotely import WeWorkRemotelyCollector
from app.collectors.grey.internshala import InternshalaCollector
from app.collectors.grey.foundit import FounditCollector
from app.collectors.grey.shine import ShineCollector
from app.collectors.grey.timesjobs import TimesJobsCollector

TIER1_COLLECTORS = [
    GreenhouseCollector(),
    LeverCollector(),
    AshbyCollector(),
    RemotiveCollector(),
    JobicyCollector(),
    ArbeitnowCollector(),
    AdzunaCollector(),
    TheMuseCollector(),
]

GREY_COLLECTORS = [
    RemoteOKCollector(),
    HNHiringCollector(),
    WellfoundCollector(),
    YCJobsCollector(),
    BuiltInCollector(),
    WeWorkRemotelyCollector(),
    InternshalaCollector(),
    FounditCollector(),
    ShineCollector(),
    TimesJobsCollector(),
]

ALL_COLLECTORS = TIER1_COLLECTORS + GREY_COLLECTORS