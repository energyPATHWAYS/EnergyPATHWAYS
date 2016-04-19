import energyPATHWAYS.config as cfg
import energyPATHWAYS.util as util
import pandas as pd
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import cPickle as pickle
import os
from data_source import Base
from data_mapper import DataMapper
from sqlalchemy import Column, Integer, Text, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, reconstructor
from system import CleaningMethod, DayType, DispatchConstraintType, FlexibleLoadShiftType, ShapesType, ShapesUnit,\
    TimeZone
from geography import Geography, GeographiesDatum, GeographyMapKey
from dispatch import DispatchFeeder
import data_source


class OtherIndex(Base):
    __tablename__ = 'OtherIndexes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class OtherIndexesDatum(Base):
    __tablename__ = 'OtherIndexesData'

    id = Column(Integer, primary_key=True)
    other_index_id = Column(ForeignKey(OtherIndex.id))
    name = Column(Text)

    UniqueConstraint(other_index_id, name)

    other_index = relationship(OtherIndex)


class Shape(DataMapper, Base):
    """
    Note that in general other model classes that need to have a relationship to Shape should use the ShapeUser mixin
    below. That way their shape property will leverage Shape's in-memory and disk caching capabilities.
    (If you wish to disable disk caching, e.g. for testing, set Shape._use_disk_cache to False.)
    """
    __tablename__ = 'Shapes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    shape_type_id = Column(ForeignKey(ShapesType.id))
    shape_unit_type_id = Column(ForeignKey(ShapesUnit.id))
    time_zone_id = Column(ForeignKey(TimeZone.id))
    geography_id = Column(ForeignKey(Geography.id))
    other_index_1_id = Column(ForeignKey(OtherIndex.id))
    other_index_2_id = Column(ForeignKey(OtherIndex.id))
    geography_map_key_id = Column(ForeignKey(GeographyMapKey.id))
    interpolation_method_id = Column(ForeignKey(CleaningMethod.id))
    extrapolation_method_id = Column(ForeignKey(CleaningMethod.id))

    _extrapolation_method = relationship(CleaningMethod,
                                         primaryjoin='Shape.extrapolation_method_id == CleaningMethod.id',
                                         lazy='joined')
    _geography = relationship(Geography, lazy='joined')
    _geography_map_key = relationship(GeographyMapKey, lazy='joined')
    _interpolation_method = relationship(CleaningMethod,
                                         primaryjoin='Shape.interpolation_method_id == CleaningMethod.id',
                                         lazy='joined')
    _other_index_1 = relationship(OtherIndex, primaryjoin='Shape.other_index_1_id == OtherIndex.id', lazy='joined')
    _other_index_2 = relationship(OtherIndex, primaryjoin='Shape.other_index_2_id == OtherIndex.id', lazy='joined')
    _shape_type = relationship(ShapesType, lazy='joined')
    _shape_unit_type = relationship(ShapesUnit, lazy='joined')
    time_zone = relationship(TimeZone, lazy='joined')

    TIME_SLICE_COLS = ['year', 'month', 'week', 'hour', 'day_type']

    # If this is True, Shape will attempt to load processed shapes from an on-disk cache before loading and
    # processing them from the database. If you would like to use the disk cache feature but need to invalidate the
    # cache due to data or code changes (or changing your primary_geography), simply delete the cache directory from
    # your disk (CACHE_DIR, below)
    _use_disk_cache = True
    _cache = {}
    CACHE_DIR = os.path.join(os.getcwd(), 'shape_cache')
    FILENAME_PREFIX = 'shape_'
    FILENAME_SUFFIX = '.p'

    @classmethod
    def shape_file(cls, id_):
        """returns the file name where we will cache a shape with a particular id"""
        return os.path.join(cls.CACHE_DIR, cls.FILENAME_PREFIX + str(id_) + cls.FILENAME_SUFFIX)

    @classmethod
    def get(cls, id_):
        try:
            shape = cls._cache[id_]
            # This message is overkill for normal use because it fires every time a shape relationship is accessed,
            # but it may be helpful for debugging.
            # print "[Shape] returning shape %i ('%s') from in-memory cache" % (id_, shape.name)
            return shape
        except KeyError:
            print "[Shape] did not find shape %i in memory cache" % (id_,)
            if cls._use_disk_cache:
                try:
                    with open(cls.shape_file(id_), 'rb') as infile:
                        cls._cache[id_] = pickle.load(infile)
                    print "[Shape] returning shape %i ('%s') from disk cache" % (id_, cls._cache[id_].name)
                    return cls._cache[id_]
                except IOError:
                    print "[Shape] did not find shape %i in disk cache" % (id_,)
                # Note: this second list of exceptions to catch comes from the list of likely errors during
                # unpickling from https://docs.python.org/2/library/pickle.html. Since we can always reload from
                # the database none of these are fatal for us.
                except (pickle.UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
                    print "[Shape] found shape %i in disk cache but failed to unpickle" % (id_,)

        # We haven't found the shape at any level of caching (memory or disk) so load it from the database
        # into the in-memory cache
        cls._cache[id_] = data_source.get(cls, id_)

        # If we are using the disk cache and got this far that means we weren't able to read the current shape
        # from the disk cache, so we should write it to the cache for next time
        if cls._use_disk_cache:
            print "[Shape] writing processed shape %i ('%s') to disk cache" % (id_, cls._cache[id_].name)
            # Create the cache directory if it does not yet exist; try to do it in a thread-safe way
            # http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary/14364249#14364249
            # Note that the overall process of shape caching isn't necessarily thread-safe, though (e.g., two threads
            # could try to write to the cache for the same shape at the same time).
            try:
                os.makedirs(cls.CACHE_DIR)
            except OSError:
                if not os.path.isdir(cls.CACHE_DIR):
                    raise
            # Save the shape to the disk cache
            with open(cls.shape_file(id_), 'wb') as outfile:
                pickle.dump(cls._cache[id_], outfile, pickle.HIGHEST_PROTOCOL)

        return cls._cache[id_]

    @property
    def shape_type(self):
        return self._shape_type.name

    @property
    def shape_unit_type(self):
        return self._shape_unit_type.name

    @reconstructor
    def reconstruct(self):
        print "[Shape] loading shape %i ('%s') from database" % (self.id, self.name)
        self.read_timeseries_data()
        print "[Shape] processing shape %i ('%s')" % (self.id, self.name)
        self.process_shape()

    @classmethod
    def active_dates_index(cls):
        try:
            return cls._active_dates_index
        except AttributeError:
            start = datetime.strptime(cfg.cfgfile.get('case', 'dispatch_start_date'), '%Y-%m-%d')
            years = int(cfg.cfgfile.get('case', 'dispatch_years'))
            end = start + relativedelta(years=years, hours=-1)
            cls._active_dates_index = pd.date_range(start, end, freq='H')
            return cls._active_dates_index

    @classmethod
    def num_active_years(cls):
        return len(cls.active_dates_index()) / 8766.

    @classmethod
    def dispatch_outputs_timezone(cls):
        try:
            return cls._dispatch_outputs_timezone
        except AttributeError:
            dispatch_outputs_timezone_id = int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))
            cls._dispatch_outputs_timezone = pytz.timezone(cfg.geo.timezone_names[dispatch_outputs_timezone_id])
            return cls._dispatch_outputs_timezone

    @classmethod
    def localized_active_dates_index(cls):
        try:
            return cls._localized_active_dates_index
        except AttributeError:
            cls._localized_active_dates_index = pd.date_range(cls.active_dates_index()[0],
                                                             periods=len(cls.active_dates_index()),
                                                             freq='H', tz=cls.dispatch_outputs_timezone())
            return cls._localized_active_dates_index

    @classmethod
    def time_slice_elements(cls):
        try:
            return cls._time_slice_elements
        except AttributeError:
            business_days = pd.bdate_range(cls.active_dates_index()[0].date(), cls.active_dates_index()[-1].date())
            biz_map = {day_type.name: day_type.id for day_type in data_source.fetch(DayType)}

            cls._time_slice_elements = {}
            for ti in cls.TIME_SLICE_COLS:
                if ti == 'day_type':
                    cls._time_slice_elements['day_type'] = np.array([biz_map['workday']
                                                                    if s.date() in business_days
                                                                    else biz_map['non-workday']
                                                                    for s in cls.active_dates_index()], dtype=int)
                else:
                    cls._time_slice_elements[ti] = getattr(cls.active_dates_index(), ti)
            cls._time_slice_elements['hour24'] = cls._time_slice_elements['hour'] + 1
            return cls._time_slice_elements

    def create_empty_shape_data(self):
        self._active_time_keys = [ind for ind in self.raw_values.index.names if ind in self.TIME_SLICE_COLS]
        self._active_time_dict = dict(
            [(ind, loc) for loc, ind in enumerate(self.raw_values.index.names) if ind in self.TIME_SLICE_COLS])

        self._non_time_keys = [ind for ind in self.raw_values.index.names if ind not in self._active_time_keys]
        self._non_time_dict = dict(
            [(ind, loc) for loc, ind in enumerate(self.raw_values.index.names) if ind in self._non_time_keys])

        data = pd.DataFrame(index=pd.Index(self.active_dates_index(), name='weather_datetime'), columns=['value'])

        for ti in self._active_time_keys:
            # hour is given as 1-24 not 0-23
            if ti == 'hour' and min(self.raw_values.index.levels[self._active_time_dict['hour']]) == 1 and max(
                    self.raw_values.index.levels[self._active_time_dict['hour']]) == 24:
                # the minimum value is 1 and max value is 24
                data[ti] = self.time_slice_elements()['hour24']
            else:
                data[ti] = self.time_slice_elements()[ti]

        non_time_levels = [list(l) for l, n in zip(self.raw_values.index.levels, self.raw_values.index.names) if
                           n in self._non_time_keys]
        # this next step could be done outside of a for loop, but I'm not able to get the Pandas syntax to take
        for name, level in zip(self._non_time_keys, non_time_levels):
            data = pd.concat([data] * len(level), keys=level, names=[name])

        data.reset_index(inplace=True)
        data.set_index(self._non_time_keys + self._active_time_keys + ['weather_datetime'], inplace=True)
        data.sort(inplace=True)
        return data


    def process_shape(self):
        if self.shape_type == 'weather date':
            self.values = util.reindex_df_level_with_new_elements(self.raw_values, 'weather_datetime',
                                                                  self.active_dates_index())  # this step is slow, consider replacing
            if self.values.isnull().values.any():
                raise ValueError('Weather data did not give full coverage of the active dates')

        elif self.shape_type == 'time slice':
            self.values = self.create_empty_shape_data()

            non_time_elements_in_levels = [list(util.get_elements_from_level(self.values, e)) for e in self._non_time_keys]
            time_elements_in_levels = [list(util.get_elements_from_level(self.values, e)) for e in self._active_time_keys]

            for ind, value in self.raw_values.iterrows():
                non_time_portion = [ind[self._non_time_dict[e]] for e in self._non_time_keys]
                time_portion = [ind[self._active_time_dict[e]] for e in self._active_time_keys]
                if not np.all([s in l for s, l in zip(non_time_portion + time_portion,
                                                      non_time_elements_in_levels + time_elements_in_levels)]):
                    continue

                indexer = tuple(non_time_portion + time_portion + [slice(None)])

                if self.shape_unit_type == 'energy':
                    len_slice = len(self.values.loc[indexer])
                    self.values.loc[indexer] = value[0] / float(len_slice) * self.num_active_years()
                elif self.shape_unit_type == 'power':
                    self.values.loc[indexer] = value[0]

            if self.values.isnull().values.any():
                raise ValueError('Shape time slice data did not give full coverage of the active dates')
            # reindex to remove the helper columns
            self.values.index = self.values.index.droplevel(self._active_time_keys)

        self.values = self.values.swaplevel('weather_datetime', -1).sort_index()
        self.geomap_to_time_zone()
        self.localize_shapes()
        self.standardize_time_across_timezones()
        self.geomap_to_primary_geography()
        self.sum_over_time_zone()
        self.normalize()
        self.add_timeshift_type()


    def add_timeshift_type(self):
        """Later these shapes will need a level called timeshift type, and it is faster to add it now if it doesn't already have it"""
        if 'timeshift_type' not in self.values.index.names:
            self.values['timeshift_type'] = 2  # index two is the native demand shape
            self.values = self.values.set_index('timeshift_type', append=True).swaplevel('timeshift_type',
                                                                                         'weather_datetime').sort_index()


    def normalize(self):
        group_to_normalize = [n for n in self.values.index.names if n != 'weather_datetime']
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint_type' in group_to_normalize:
            temp = self.values.groupby(level=group_to_normalize).transform(lambda x: x / x.sum()) * self.num_active_years()
            # TODO: 2, and 3 should not be hard coded here, they represent p_min and p_max
            indexer = util.level_specific_indexer(temp, 'dispatch_constraint_type', [[2, 3]])
            temp.loc[indexer, :] = self.values.loc[indexer, :]
            self.values = temp
        else:
            self.values = self.values.groupby(level=group_to_normalize).transform(
                lambda x: x / x.sum()) * self.num_active_years()


    def geomap_to_time_zone(self, attr='values', inplace=True):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        if self.geography == 'time zones':
            if inplace:
                return
            else:
                return getattr(self, attr)

        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self,
                                                                                                'geography_map_key') else self.geography_map_key

        subsection, supersection = 'time zones', self.geography
        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        self.map_df = map_df

        mapped_data = util.DfOper.mult([getattr(self, attr), map_df])
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
        mapped_data.sort(inplace=True)
        if inplace:
            setattr(self, attr, mapped_data)
        else:
            return mapped_data


    def geomap_to_primary_geography(self, attr='values', inplace=True, converted_geography=None):
        """This needs more testing for cases where the converted_geography is time zone or self.geography is time zone
        """
        converted_geography = cfg.cfgfile.get('case', 'primary_geography')
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self,
                                                                                                'geography_map_key') else self.geography_map_key

        if self.geography == converted_geography:
            if inplace:
                return
            else:
                return getattr(self, attr)

        # we should add dispatch region as another subsection to ensure proper geomap to dispatch region after
        subsection = 'time zones' if self.geography == 'time zones' else ['time zones', self.geography]
        supersection = converted_geography

        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        mapped_data = util.DfOper.mult((getattr(self, attr), map_df), fill_value=None)
        levels = [ind for ind in mapped_data.index.names if (ind != self.geography and self.geography != 'time zones')]
        mapped_data = mapped_data.groupby(level=levels).sum()
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
        mapped_data.sort(inplace=True)

        if inplace:
            setattr(self, attr, mapped_data)
        else:
            return mapped_data


    @staticmethod
    def geomap_to_dispatch_geography(df):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        converted_geography = cfg.cfgfile.get('case', 'primary_geography')
        dispatch_geography = cfg.cfgfile.get('case', 'dispatch_geography')
        if converted_geography == dispatch_geography:
            return df
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key')

        subsection, supersection = dispatch_geography, converted_geography
        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        mapped_data = util.DfOper.mult([df, map_df])

        levels = [ind for ind in mapped_data.index.names if ind != converted_geography]
        mapped_data = mapped_data.groupby(level=levels).sum()
        mapped_data.sort(inplace=True)

        return mapped_data


    def sum_over_time_zone(self, attr='values', inplace=True):
        converted_geography = cfg.cfgfile.get('case', 'primary_geography')

        if converted_geography == 'time zones':
            if inplace:
                return
            else:
                return getattr(self, attr)

        levels = [ind for ind in getattr(self, attr).index.names if ind != 'time zones']
        df = getattr(self, attr).groupby(level=levels).sum()
        df.sort(inplace=True)

        if inplace:
            setattr(self, attr, df)
        else:
            return df


    def standardize_time_across_timezones(self, attr='values', inplace=True):
        df = util.reindex_df_level_with_new_elements(getattr(self, attr).copy(), 'weather_datetime',
                                                     self.localized_active_dates_index())
        levels = [n for n in self.values.index.names if n != 'weather_datetime']
        df = df.groupby(level=levels).fillna(method='bfill').fillna(method='ffill')

        if inplace:
            setattr(self, attr, df)
        else:
            return df


    def localize_shapes(self, attr='values', inplace=True):
        """ Step through time zones and put each profile maped to time zone in that time zone
        """
        new_df = []
        for tz_id, group in getattr(self, attr).groupby(level='time zones'):
            # get the time zone name and figure out the offset from UTC
            tz_id = tz_id if self.time_zone_id is None else self.time_zone_id
            tz = pytz.timezone(cfg.geo.timezone_names[tz_id])
            _dt = datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds() / 60.
            # localize and then convert to dispatch_outputs_timezone
            df = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime').tz_convert(
                self.dispatch_outputs_timezone(), level='weather_datetime')
            new_df.append(df)

        if inplace:
            setattr(self, attr, pd.concat(new_df).sort_index())
        else:
            return pd.concat(new_df).sort_index()

    @staticmethod
    def produce_flexible_load(shape_df, percent_flexible=None, hr_delay=None, hr_advance=None):
        percent_flexible = 0 if percent_flexible is None else percent_flexible
        hr_delay = 0 if hr_delay is None else hr_delay
        hr_advance = 0 if hr_advance is None else hr_advance

        if percent_flexible == 0 or (hr_delay == 0 and hr_advance == 0):
            return util.df_slice(shape_df, elements=2, levels='timeshift_type')

        timeshift_levels = list(util.get_elements_from_level(shape_df, 'timeshift_type'))
        timeshift_levels.sort()
        if timeshift_levels == [1, 2, 3]:
            delay = util.df_slice(shape_df, elements=1, levels='timeshift_type')
            native = util.df_slice(shape_df, elements=2, levels='timeshift_type')
            advance = util.df_slice(shape_df, elements=3, levels='timeshift_type')
        elif timeshift_levels == [2]:
            # TODO this could be a lambda function
            def shift(df, hr):
                """ positive hours is a shift forward, negative hours a shift back"""
                return df.shift(hr).bfill().ffill()

            non_weather = [n for n in shape_df.index.names if n != 'weather_datetime']
            delay = shape_df.groupby(level=non_weather).apply(shift, hr=hr_delay)
            native = shape_df
            advance = shape_df.groupby(level=non_weather).apply(shift, hr=-hr_advance)
        else:
            raise ValueError("elements in the level timeshift_type are not recognized")

        return pd.concat([delay * percent_flexible + native * (1 - percent_flexible),
                          native,
                          advance * percent_flexible + native * (1 - percent_flexible)], keys=[1, 2, 3],
                         names=['timeshift_type'])


class ShapeUser(object):
    """
    This is a mixin that allows an object with a shape_id to access its shape via the caching mechanisms
    built into Shape. A class that mixes in ShapeUser should not define its own shape property/relationship/method/etc.
    """

    @property
    def shape(self):
        if self.shape_id is None:
            return None
        return Shape.get(self.shape_id)


class ShapesDatum(Base):
    __tablename__ = 'ShapesData'

    id = Column(Integer, primary_key=True)
    parent_id = Column(ForeignKey(Shape.id))
    gau_id = Column(ForeignKey(GeographiesDatum.id))
    dispatch_feeder_id = Column(ForeignKey(DispatchFeeder.id))
    timeshift_type_id = Column(ForeignKey(FlexibleLoadShiftType.id))
    resource_bin = Column(Integer)
    dispatch_constraint_type_id = Column(ForeignKey(DispatchConstraintType.id))
    year = Column(Integer)
    month = Column(Integer)
    week = Column(Integer)
    hour = Column(Integer)
    day_type_id = Column(ForeignKey(DayType.id))
    weather_datetime = Column(DateTime)
    value = Column(Float)

    UniqueConstraint(parent_id, gau_id, dispatch_feeder_id, timeshift_type_id, resource_bin)

    day_type = relationship(DayType)
    dispatch_feeder = relationship(DispatchFeeder)
    gau = relationship(GeographiesDatum)
    timeshift_type = relationship(FlexibleLoadShiftType)
    dispatch_constraint_type = relationship(DispatchConstraintType)
    shape = relationship(Shape, order_by=id, backref='data')