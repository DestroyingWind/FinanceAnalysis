# -*- coding: utf-8 -*-
import logging

from zvt.contract import IntervalLevel
from zvt.contract.api import get_entities
from zvt.utils.time_utils import now_pd_timestamp
from zvt.domain import Stock
from zvt.contract.common import Region, Provider, EntityType
from zvt.factors.ma.ma_factor import MaFactor
from zvt.factors.ma.ma_stats import MaStateStatsFactor

logger = logging.getLogger(__name__)


def cal_ma_states(region: Region, start='000001', end='002000'):
    logger.info(f'start cal day ma stats {start}:{end}')

    entities = get_entities(region=region,
                            provider=Provider.Default, 
                            entity_type=EntityType.Stock, 
                            columns=[Stock.entity_id, Stock.code],
                            filters=[Stock.code >= start, Stock.code < end])

    codes = entities.index.to_list()

    ma_1d_stats = MaStateStatsFactor(region=region,
                                     codes=codes, 
                                     start_timestamp='2005-01-01',
                                     end_timestamp=now_pd_timestamp(Region.CHN),
                                     level=IntervalLevel.LEVEL_1DAY)

    ma_1d_factor = MaFactor(region=region,
                            codes=codes, 
                            start_timestamp='2005-01-01',
                            end_timestamp=now_pd_timestamp(Region.CHN),
                            level=IntervalLevel.LEVEL_1DAY)

    logger.info(f'finish cal day ma stats {start}:{end}')

    ma_1wk_stats = MaStateStatsFactor(region=region,
                                      codes=codes, 
                                      start_timestamp='2005-01-01',
                                      end_timestamp=now_pd_timestamp(Region.CHN),
                                      level=IntervalLevel.LEVEL_1WEEK)

    logger.info(f'finish cal week ma stats {start}:{end}')
