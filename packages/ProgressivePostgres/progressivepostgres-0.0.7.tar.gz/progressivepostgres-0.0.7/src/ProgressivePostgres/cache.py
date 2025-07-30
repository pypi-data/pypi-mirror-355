# src/ZeitgleichClient/cache.py

from datetime import datetime
from datetime import timedelta

class Cache:
    """
    A class implementing a cache for caching table schema/column name definitions.
    
    Refresh/Expiration of the cache is defined by the class variable <exipration> in hours.

    table_cache = 
    {
        "table1" : {
            "col_names" : [col1, col2, col3, ...],
            "expire_time" : 17xxxxxxx.xxx
        },
        "table2" : {
            "col_names" : [col1, col2, col3, ...],
            "expire_time" : 17xxxxxxx.xxx
        }, 
        ...
    }
    
    meta_cache = 
    {
        "topic/meta1" : 17xxxxxxx.xxx
        },
        "topic/meta2" : 17xxxxxxx.xxx
        },
        ...
    }
    """

    meta_cache = {}
    table_cache = {}
    expiration = 6
    
    @classmethod
    def check_cache(cls, table: str) -> list:
        """
        Checks and returns the cached value for the provided table.
        If cache expired or cache does not exist for the table, will return 0. 

        Args:
            table (str):    The table name.

        Returns:
            list:   A list containing the cached column names of the provided table.
        """

        try:
            Cache.table_cache[table]
        except KeyError as err:
            Cache._init_cache_table(table)
            return 0

        if Cache._get_cache_expire(table) < datetime.now().timestamp() or not Cache._get_cache_value(table):
            return 0
        else:
            return Cache._get_cache_value(table)
            
    @classmethod
    def _init_cache_table(cls, table: str):
        """
        Initializes a new cache entry for the provided table.

        Args:
            table (str):    The table name.
        """

        Cache.table_cache[table] = {
            'col_names': None,
            'expire_time': (datetime.now() + timedelta(hours=Cache.expiration)).timestamp()
        }

    @classmethod
    def update_cache(cls, table: str, value: list) -> None:
        """
        Updates the cache with given table and value.

        Args:
            table (str):    The table name.
            value (list):   The list of values to be cached.

        Returns:
            _type_: _description_
        """

        cls._set_cache_value(table, value)
        cls._set_cache_expire(table, (datetime.now() + timedelta(hours=Cache.expiration)).timestamp())
    
        
    @classmethod
    def _set_cache_expire(cls, table: str, timestamp):
        """
        Sets the new expiration date for the provided table.

        Args:
            table (str):        The table name.
            timestamp (float):  The timestamp in unix epoch format.
        """

        Cache.table_cache[table]['expire_time'] = timestamp
        
    @classmethod
    def _get_cache_expire(cls, table: str) -> float:
        """
        Gets the expiration date for the provided table

        Args:
            table (str):    The table name.

        Returns:
            float: The expiration timestamp in unix epoch format.
        """

        return Cache.table_cache[table]['expire_time']

    @classmethod
    def _set_cache_value(cls, table: str, value: list):
        """
        Sets the value to be cached for the provided table.
        Values are a list of column names for the provided table.

        Args:
            table (str):    The table name.
            value (list):   The list of values to be cached.
        """

        Cache.table_cache[table]['col_names'] = value

    @classmethod
    def _get_cache_value(cls, table: str) -> list:
        """
        Gets the cached value for the provided table.

        Args:
            table (str):    The table name.

        Returns:
            list:   A list of column names.
        """

        return Cache.table_cache[table]['col_names']
    


    @classmethod
    def check_meta_cache(cls, meta_topic: str) -> bool:
        """
        Checks cached value for the provided meta_topic.
        If cache expired or cache does not exist for the table, will return 0.
        If cache exist and not expired, will return 1.

        Args:
            meta_topic (str):    The meta topic name.

        Returns:
            0 if cache not exists or expired and needs to be updated manually
            1 if cache exists
        """

        try:
            Cache.meta_cache[meta_topic]
        except KeyError as err:
            Cache._init_cache_meta_topic(meta_topic)
            return 0

        # if cached meta topic expired
        if Cache._get_meta_cache(meta_topic) < datetime.now().timestamp():
            return 0
        else:
            return 1
            
    @classmethod
    def _init_cache_meta_topic(cls, meta_topic: str) -> None:
        """
        Initializes a new cache entry for the provided table.

        Args:
            table (str):    The table name.
        """

        Cache.meta_cache[meta_topic] = (datetime.now() + timedelta(hours=Cache.expiration)).timestamp()

    @classmethod
    def update_meta_cache(cls, meta_topic: str) -> None:
        """
        Updates the expiration date with given meta_topic.

        Args:
            meta_topic (str):    The meta topic name.
        """

        cls._set_meta_cache(meta_topic, (datetime.now() + timedelta(hours=Cache.expiration)).timestamp())
    
        
    @classmethod
    def _set_meta_cache(cls, meta_topic: str, timestamp) -> None:
        """
        Sets the new expiration date for the provided meta_topic.

        Args:
            meta_topic (str):   The meta topic name.
            timestamp (float):  The timestamp in unix epoch format.
        """

        Cache.meta_cache[meta_topic] = timestamp
        
    @classmethod
    def _get_meta_cache(cls, meta_topic: str) -> float:
        """
        Gets the expiration date for the provided meta_topic

        Args:
            meta_topic (str):    The meta topic name.

        Returns:
            float: The expiration timestamp in unix epoch format.
        """
        return Cache.meta_cache[meta_topic]
    
    #TODO
    @classmethod
    def clear_cache(cls) -> None:
        """
        Clears the cache.
        Important in case of changed values and old cache not removed.
        """
        raise NotImplementedError
