from raphson_mp import charts, db, i18n
from raphson_mp.vars import LOCALE

from . import T_client


def test_rows_to_xy():
    rows = [
        ("A", 100),
        ("B", 50),
        ("C", 20),
    ]
    axisdata, seriesdata = charts.rows_to_xy(rows)
    assert axisdata == ["A", "B", "C"]
    assert seriesdata == [100, 50, 20]


def test_rows_to_xy_multi():
    rows = [
        ("raphson", "CB", 19181),
        ("raphson", "DK", 14352),
        ("raphson", "JK", 14530),
        ("robin", "CB", 125),
        ("robin", "DK", 1958),
        ("robin", "JK", 3771),
        ("jasper", "CB", 892),
        ("jasper", "DK", 2334),
        ("jasper", "JK", 8101),
        ("daniel", "CB", 209),
        ("daniel", "DK", 4669),
        ("daniel", "JK", 4683),
        ("christian", "CB", 3101),
        ("christian", "DK", 475),
        ("christian", "JK", 64),
        ("jelle", "CB", 74),
        ("wike", "DK", 32),
        ("wike", "JK", 3),
        ("tyrone", "CB", 183),
        ("tyrone", "DK", 269),
        ("tyrone", "JK", 271),
    ]
    axisdata, seriesdata = charts.rows_to_xy_multi(rows)
    assert axisdata == ["raphson", "jasper", "daniel", "robin", "christian", "tyrone", "jelle", "wike"], axisdata
    assert seriesdata.keys() == {row[1] for row in rows}
    for row in rows:
        assert seriesdata[row[1]][axisdata.index(row[0])] == row[2]


async def test_data():
    LOCALE.set(i18n.FALLBACK_LOCALE)
    for period in charts.StatsPeriod:
        with db.connect(read_only=True) as conn:
            for chart in charts.CHARTS:
                data = chart(conn, period)
                assert data is None or data["title"]


async def test_stats_page(client: T_client):
    async with client.get("/stats") as response:
        assert response.status == 200


async def test_stats_data_http(client: T_client):
    async with client.get("/stats/data/8?period=week") as response:
        assert response.status == 200
        await response.json()  # make sure response is valid json
