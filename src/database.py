# Created by ohad at 7/27/21
import typing as tp
from functools import lru_cache

from loguru import logger
import pymongo
from uuid import uuid4
from mongoengine import connect


def parse_mongodb_connection_string(user: str, password: str, host: str, port: str,
                                    authentication_database: tp.Optional[str] = "admin", *args, **kwargs) -> str:
    """
    Parses a mongodb connection string from provided inputs

    :param user: name of the mongodb user
    :type user: str
    :param password: password for the requested mongodb user
    :type password: str
    :param host: mongodb host name
    :type host: str
    :param port: mongodb port
    :type port: str
    :param authentication_database: authentication database for the user, defaults to "admin"
    :type authentication_database: tp.Optional[str], optional
    :return: mongodb connection string
    :rtype: str
    """
    return f'mongodb://{user}:{password}@{host}:{port}/{authentication_database}'

@lru_cache
def init_cached_database(connection_string: str, db_name: str,
                         alias: tp.Optional[str] = None, async_flag=False) -> tp.Union[
    pymongo.database.Database]:
    """
    initializes a cahced handle to the mongodb database

    :param connection_string: mongodb connection string
    :type connection_string: str
    :param db_name: name of the database to connect to
    :type db_name: str
    :return: database handle
    :rtype: :class:`pymongo.database.Database`
    """
    alias = alias or uuid4().hex
    if not async_flag:
        return connect(host=connection_string, alias=alias)[db_name]
    else:
        return motor.motor_asyncio.AsyncIOMotorClient(host=connection_string)[db_name]


def connect_to_database(db_config: dict) -> pymongo.database.Database:
    """
    Connection to database method accepting a dictionary for database configuration

    >>> db_config = dict(host='mongomock', user='mock', password='1234', port='27017', authentication_database='admin', db_name='mock')
    >>> db = connect_to_database(db_config)

    :param db_config: database configuration dictionary
    :type db_config: dict
    :return: DB handle instance
    :rtype: :class:`pymongo.database.Database`
    """
    return init_cached_database(parse_mongodb_connection_string(
        **db_config), db_name=db_config['db_name'])


def get_segmentation_files(bcr_patient_barcode: str, db_config: dict) -> tp.List[str]:
    """
    Fetches all segmentation files for a specific patient

    >>> get_segmentation_files('TCGA-AO-A12D')

    :param bcr_patient_barcode: patient barcode id
    :type bcr_patient_barcode: str
    :param db_config: database configuration dictionary, defaults to None
    :type db_config: tp.Optional[str], optional
    :return: list of segmentation file paths
    :rtype: List[str]
    """
    db = connect_to_database(db_config=db_config)

    return [item['segmentation_file'] for item in
            db['segmentation_files'].find({'bcr_patient_barcode': bcr_patient_barcode})]


def get_dcm_dirs(bcr_patient_barcode: str, db_config: dict) -> tp.List[str]:
    """
    Fetches all dicom directories for a specific patient

    >>> get_dcm_dirs('TCGA-AO-A12D')

    :param bcr_patient_barcode: patient barcode id
    :type bcr_patient_barcode: str
    :param db_config: database configuration dictionary, defaults to None
    :type db_config: tp.Optional[str], optional
    :return: list of dicom directories paths
    :rtype: List[str]
    """
    db = connect_to_database(db_config)
    return [item['dcm_dir'] for item in (db['dcm_files'].find({'bcr_patient_barcode': bcr_patient_barcode}))]


def get_unique_patient_barcodes(collection_name: str, db_config: dict) -> tp.List[str]:
    """
    Fetches unique patient barcode values for a specific collection

    :param collection_name: collection name to query
    :type collection_name: str
    :param db_config: database configuration dictionary, defaults to None
    :type db_config: tp.Optional[str], optional
    :return: list of unique barcode names
    :rtype: tp.List[str]
    """
    db = connect_to_database(db_config)
    col = db[collection_name]
    return col.find({}).distinct("bcr_patient_barcode")


def get_series_uids(collection_name: str, patient_barcode: str, db_config: dict) -> tp.List[str]:
    """
    Fetches uids for a specific patient barcode

    :param collection_name: collection name to query
    :type collection_name: str
    :param patient_barcode: [unique identifier for a patient
    :type patient_barcode: str
    :return: series uids matching specific dicom images
    :param db_config: database configuration dictionary, defaults to None
    :type db_config: tp.Optional[str], optional
    :rtype: tp.List[str]
    """
    db = connect_to_database(db_config)
    col = db[collection_name]
    return col.find({"bcr_patient_barcode": patient_barcode}).distinct("series_uid")
