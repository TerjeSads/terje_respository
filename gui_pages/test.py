from sads_api_schemas.enums import InternalNetworkKPI
from sadsapi.internal_network import get_nw_kpis

df = get_nw_kpis("NO", InternalNetworkKPI.BusiestSites)
print(df)
