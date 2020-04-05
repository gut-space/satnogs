from datetime import timedelta
from app import app
from app.repository import Repository
from app.pagination import use_pagination

from webargs import fields
from webargs.flaskparser import use_kwargs

@app.route('/obslist')
@use_pagination()
# Use_kwargs introduces ugly behavior when user provide parameter without value,
# for example "?sat_id=". It should be ignored or handle as None value, but
# I cannot set them. Now user get HTTP 422 Unprocessable Entity. I think that
# it isn't important, because user doesn't provide it manually.
@use_kwargs({
    'aos_before': fields.Date(),
    'los_after': fields.Date(),
    'sat_id': fields.Int(),
    'station_id': fields.Int(),
    'has_tle': fields.Bool()
}, validate=lambda kwargs: "aos_before" not in kwargs or
                        "los_after" not in kwargs or
                        kwargs["aos_before"] >= kwargs["los_after"])
def obslist(limit_and_offset, **filters):
    '''This function retrieves observations list from a local database and
        displays it.'''
    aos_before_org = filters.get("aos_before")
    if aos_before_org is not None:
        # Repository uses datetime.datetime structure to bound dates and it is
        # exact date.
        # User provides datetime.date (which not include hour) and it means that
        # list should contain observations from @los_after day 00:00:00 hour to
        # @aos_before day 23:59:59.999 hour. For handle it we add 1 day to
        # @aos_before day before send to repository.
        filters["aos_before"] = aos_before_org + timedelta(days=1)
        
    repository = Repository()
    obslist = repository.read_observations(filters, **limit_and_offset)
    satellites_list = repository.read_satellites()
    observation_count = repository.count_observations(filters)
    stations_list = repository.read_stations()

    satellites_dict = { sat["sat_id"]: sat["sat_name"] for sat in satellites_list }
    stations_dict = { s["station_id"]: s["name"] for s in stations_list }
    for obs in obslist:
        obs["sat_name"] = satellites_dict[obs["sat_id"]]
        obs["station_name"] = stations_dict[obs["station_id"]]

    if aos_before_org is not None:
        # We send back to user the same date as user provide.
        filters["aos_before"] = aos_before_org

    # When database will contain many satellites and stations then we need
    # refactor this code to lazy, async read satellites and stations. 
    return 'obslist.html', dict(obslist=obslist, item_count=observation_count,
        satellites=satellites_list, stations=stations_list, filters=filters)
