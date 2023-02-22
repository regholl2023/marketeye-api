"""
Endpoints to access stock market analytics
"""

import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response

from utils.handle_validation import validate_api_key, validate_date_string
from utils.handle_external_apis import (
    get_ticker_analytics,
    get_market_sp500,
    get_market_vixs,
)
from db.crud.analytics import (
    get_normalazied_cvi_slope,
    get_analytics_sorted_by,
    get_dates,
)
from db.crud.scrapes import get_mentions
from db.mongodb import AsyncIOMotorClient, get_database

analytics_router = APIRouter()


@analytics_router.get("/", tags=["Analytics"])
async def analytics():
    """
    Initial analytics route endpoint
    """
    return Response("Hello World! It's an Analytics Router")


@analytics_router.get("/get_ticker_analytics", tags=["Analytics"])
async def read_ticker_analytics(
    date: str = Depends(validate_date_string),
    ticker: str = Query(
        default=None,
        description="Ticker representing the stock",
    ),
    api_key: str = Depends(validate_api_key),  # pylint: disable=W0613
    db: AsyncIOMotorClient = Depends(get_database),
):
    """
    Endpoint to get analytics (both base and extra) for a single stock

    Returns:  see _compute_base_analytics_ and _compute_extra_analytics_ for details
    """

    return {
        **get_ticker_analytics(ticker, date, 45, 15),
        **await get_mentions(db, ticker, date),
    }


@analytics_router.get("/get_market_analytics", tags=["Analytics"])
async def read_market_analytics(
    date: str = Depends(validate_date_string),
    api_key: str = Depends(validate_api_key),  # pylint: disable=W0613
    db: AsyncIOMotorClient = Depends(get_database),
):
    """
    Endpoint to get analytics (both base and extra) for a single stock

    Returns:  see _get_market_sp500_, _get_market_vixs_, _get_normalazied_cvi_slope_ and for details
    """

    return {
        "SP500": get_market_sp500(date),
        **get_market_vixs(date),
        "normalazied_CVI_slope": await get_normalazied_cvi_slope(db, date),
    }


@analytics_router.get("/get_analytics_lists_by_criteria", tags=["Analytics"])
async def read_analytics_by_criteria(
    date: str = Depends(validate_date_string),
    api_key: str = Depends(validate_api_key),  # pylint: disable=W0613
    db: AsyncIOMotorClient = Depends(get_database),
) -> dict:
    """
    Endpoint to get analytics (both base and extra) for a single stock

    Returns:
        each field is a list of outputs for
        the functions _compute_base_analytics_ and _compute_extra_analytics_
    """

    futures = [
        get_analytics_sorted_by(db, date, "one_day_avg_mf"),
        get_analytics_sorted_by(db, date, "three_day_avg_mf"),
        get_analytics_sorted_by(db, date, "volume"),
        get_analytics_sorted_by(db, date, "three_day_avg_volume"),
        get_analytics_sorted_by(db, date, "macd"),
    ]
    res = await asyncio.gather(*futures)

    return {
        "by_one_day_avg_mf": res[0],
        "by_three_day_avg_mf": res[1],
        "by_volume": res[2],
        "by_three_day_avg_volume": res[3],
        "by_macd": res[4],
    }


@analytics_router.get("/get_analytics_lists_by_criterion", tags=["Analytics"])
async def read_analytics_lists_by_criterion(
    date: str = Depends(validate_date_string),
    criterion: str = Query(
        default=None,
        description="""Criterion by which the top 20 tickers are selected.
        One of "one_day_avg_mf", "three_day_avg_mf", "volume", "three_day_avg_volume", "macd\"""",
    ),
    api_key: str = Depends(validate_api_key),  # pylint: disable=W0613
    db: AsyncIOMotorClient = Depends(get_database),
) -> dict:
    """
    Endpoint to get analytics (both base and extra) for a single stock

    Returns: see output for the functions _compute_base_analytics_ and _compute_extra_analytics_
    """

    if criterion not in [
        "one_day_avg_mf",
        "three_day_avg_mf",
        "volume",
        "three_day_avg_volume",
        "macd",
    ]:
        raise HTTPException(status_code=422, detail="No such criterion implemented.")

    return {criterion: await get_analytics_sorted_by(db, date, criterion)}


@analytics_router.get("/get_dates", tags=["Analytics"])
async def read_dates(
    api_key: str = Depends(validate_api_key),  # pylint: disable=W0613
    db: AsyncIOMotorClient = Depends(get_database),
) -> dict:
    """
    Endpoint to get dates for which analytics data exists in the database

    Returns: Correspongding to list of epoch dates ("dates")
    """

    return await get_dates(db)
