import credentials

from sys import path
path.append('./src/bgp_data_interface')
from tmd import TMD
from typing import Any
from utils import location


import pandas as pd




def _location_params(site: str) -> dict[str, Any]:
    loc = location.get_location(site)

    return {
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
    }


def test_init_tmd() -> None:
    api = TMD(credentials.TMD_TOKEN)

    assert api is not None
    assert isinstance(api, TMD)


def test_forecast_empty_params() -> None:
    api = TMD(credentials.TMD_TOKEN)
    df = api.forecast({})

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (24, 11)


def test_forecast_today() -> None:
    api = TMD(credentials.TMD_TOKEN)
    today = pd.Timestamp.today().strftime('%Y-%m-%d')

    df = api.forecast({
        'start_date': today,
        'end_date': today,
    })

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    # assert df.shape[1] == 11
    assert df.shape == (24, 11)


def test_forecast_2days() -> None:
    api = TMD(credentials.TMD_TOKEN)
    today = pd.Timestamp.today()

    df = api.forecast({
        'start_date': today.strftime('%Y-%m-%d'),
        'end_date': (today + pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
    })

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    # assert df.shape[1] == 11
    assert df.shape == (48, 11)


def test_forecast_cnx() -> None:
    api = TMD(credentials.TMD_TOKEN)
    df = api.forecast(_location_params(location.CNX))

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (24, 11)


def test_forecast_dmk() -> None:
    api = TMD(credentials.TMD_TOKEN)
    df = api.forecast(_location_params(location.DMK))   

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (24, 11)


def test_forecast_abp() -> None:
    api = TMD(credentials.TMD_TOKEN)
    df = api.forecast(_location_params(location.ABP))

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (24, 11)

def test_forecast_bip() -> None:
    api = TMD(credentials.TMD_TOKEN)
    df = api.forecast(_location_params(location.BIP))

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (24, 11)

