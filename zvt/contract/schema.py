# -*- coding: utf-8 -*-
import inspect
from datetime import timedelta
from typing import List, Union

import pandas as pd
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session

from zvt.contract import IntervalLevel
from zvt.contract.common import Region, Provider
from zvt.utils.time_utils import date_and_time, is_same_time, now_pd_timestamp


class Mixin(object):
    id = Column(String(length=256), primary_key=True)
    # entity id for this model
    entity_id = Column(String(length=32))

    # the meaning could be different for different case,most of time it means 'happen time'
    timestamp = Column(DateTime)

    @classmethod
    def help(cls):
        print(inspect.getsource(cls))

    @classmethod
    def important_cols(cls):
        return []

    @classmethod
    def time_field(cls):
        return 'timestamp'

    @classmethod
    def register_recorder_cls(cls, provider: Provider, recorder_cls):
        """
        register the recorder for the schema

        :param provider:
        :param recorder_cls:
        """
        # dont't make provider_map_recorder as class field,it should be created for the sub class as need
        if not hasattr(cls, 'provider_map_recorder'):
            cls.provider_map_recorder = {}

        if provider not in cls.provider_map_recorder:
            cls.provider_map_recorder[provider] = recorder_cls

    @classmethod
    def register_provider(cls, region: Region, provider: Provider):
        # dont't make providers as class field,it should be created for the sub class as need
        if not hasattr(cls, 'providers'):
            cls.providers = {}

        if region in cls.providers.keys():
            if provider not in cls.providers[region]:
                cls.providers[region].append(provider)
        else:
            cls.providers.update({region:[provider]})

    @classmethod
    def query_data(cls,
                   region: Region,
                   provider_index: int = 0,
                   ids: List[str] = None,
                   entity_ids: List[str] = None,
                   entity_id: str = None,
                   codes: List[str] = None,
                   code: str = None,
                   level: Union[IntervalLevel, str] = None,
                   provider: Provider = Provider.Default,
                   columns: List = None,
                   col_label: dict = None,
                   return_type: str = 'df',
                   start_timestamp: Union[pd.Timestamp, str] = None,
                   end_timestamp: Union[pd.Timestamp, str] = None,
                   filters: List = None,
                   session: Session = None,
                   order=None,
                   limit: int = None,
                   index: Union[str, list] = None,
                   time_field: str = 'timestamp'):
        from .api import get_data
        if provider == Provider.Default:
            provider = cls.providers[region][provider_index]
        return get_data(data_schema=cls, region=region, ids=ids, entity_ids=entity_ids, entity_id=entity_id, codes=codes,
                        code=code, level=level, provider=provider, columns=columns, col_label=col_label,
                        return_type=return_type, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                        filters=filters, session=session, order=order, limit=limit, index=index, time_field=time_field)


class NormalMixin(Mixin):
    # the record created time in db
    created_timestamp = Column(DateTime, default=now_pd_timestamp(Region.CHN))
    # the record updated time in db, some recorder would check it for whether need to refresh
    updated_timestamp = Column(DateTime)


class EntityMixin(Mixin):
    entity_type = Column(String(length=64))
    exchange = Column(String(length=32))
    code = Column(String(length=64))
    name = Column(String(length=128))

    @classmethod
    def get_trading_dates(cls, start_date=None, end_date=None):
        """
        overwrite it to get the trading dates of the entity

        :param start_date:
        :param end_date:
        :return:
        """
        return pd.date_range(start_date, end_date, freq='B')

    @classmethod
    def get_trading_intervals(cls):
        """
        overwrite it to get the trading intervals of the entity

        :return:[(start,end)]
        """
        return [('09:30', '11:30'), ('13:00', '15:00')]

    @classmethod
    def get_interval_timestamps(cls, start_date, end_date, level: IntervalLevel):
        """
        generate the timestamps for the level

        :param start_date:
        :param end_date:
        :param level:
        """

        for current_date in cls.get_trading_dates(start_date=start_date, end_date=end_date):
            if level >= IntervalLevel.LEVEL_1DAY:
                yield current_date
            else:
                start_end_list = cls.get_trading_intervals()

                for start_end in start_end_list:
                    start = start_end[0]
                    end = start_end[1]

                    current_timestamp = date_and_time(the_date=current_date, the_time=start)
                    end_timestamp = date_and_time(the_date=current_date, the_time=end)

                    while current_timestamp <= end_timestamp:
                        yield current_timestamp
                        current_timestamp = current_timestamp + timedelta(minutes=level.to_minute())

    @classmethod
    def is_open_timestamp(cls, timestamp):
        timestamp = pd.Timestamp(timestamp)
        return is_same_time(timestamp, date_and_time(the_date=timestamp.date(),
                                                     the_time=cls.get_trading_intervals()[0][0]))

    @classmethod
    def is_close_timestamp(cls, timestamp):
        timestamp = pd.Timestamp(timestamp)
        return is_same_time(timestamp, date_and_time(the_date=timestamp.date(),
                                                     the_time=cls.get_trading_intervals()[-1][1]))

    @classmethod
    def is_finished_kdata_timestamp(cls, timestamp: pd.Timestamp, level: IntervalLevel):
        """
        :param timestamp: the timestamp could be recorded in kdata of the level
        :type timestamp: pd.Timestamp
        :param level:
        :type level: zvt.domain.common.IntervalLevel
        :return:
        :rtype: bool
        """
        timestamp = pd.Timestamp(timestamp)

        for t in cls.get_interval_timestamps(timestamp.date(), timestamp.date(), level=level):
            if is_same_time(t, timestamp):
                return True

        return False

    @classmethod
    def could_short(cls):
        """
        whether could be shorted

        :return:
        """
        return False

    @classmethod
    def get_trading_t(cls):
        """
        0 means t+0
        1 means t+1

        :return:
        """
        return 1


class NormalEntityMixin(EntityMixin):
    # the record created time in db
    created_timestamp = Column(DateTime, default=now_pd_timestamp(Region.CHN))
    # the record updated time in db, some recorder would check it for whether need to refresh
    updated_timestamp = Column(DateTime)
