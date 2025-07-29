# -*- coding: utf-8 -*-

"""
Redshift connection parameters and utility functions.
"""

import typing as T
import dataclasses
from datetime import datetime

try:
    import redshift_connector
except ImportError: # pragma: no cover
    pass

from func_args.api import OPT, remove_optional

from .model_redshift_serverless import (
    RedshiftServerlessNamespace,
    RedshiftServerlessWorkgroup,
)
from .client_redshift_serverless import get_namespace, get_workgroup

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_redshift_serverless.client import RedshiftServerlessClient


@dataclasses.dataclass
class RedshiftConnectionParams:
    """
    TODO
    """


@dataclasses.dataclass
class RedshiftServerlessConnectionParams:
    host: str = dataclasses.field()
    port: int = dataclasses.field()
    username: str = dataclasses.field()
    password: str = dataclasses.field()
    database: str = dataclasses.field()

    expiration: datetime = dataclasses.field()
    next_refresh_time: datetime = dataclasses.field()
    namespace: RedshiftServerlessNamespace = dataclasses.field()
    workgroup: RedshiftServerlessWorkgroup = dataclasses.field()

    @classmethod
    def new(
        cls,
        redshift_serverless_client: "RedshiftServerlessClient",
        namespace_name: str,
        workgroup_name: str,
        custom_domain_name: str = OPT,
        duration_seconds: int = OPT,
    ):
        """
        Create a new instance of :class:`RedshiftServerlessConnectionParams`
        based on the redshift serverless namespace and workgroup.

        :param redshift_serverless_client: boto3.client("redshift-serverless") object
        :param namespace_name: The name of the Redshift serverless namespace.
        :param workgroup_name: The name of the Redshift serverless workgroup.
        :param custom_domain_name: Optional custom domain name for the connection.
        :param duration_seconds: Optional duration in seconds for the credentials.
        """
        namespace = get_namespace(
            redshift_serverless_client=redshift_serverless_client,
            namespace_name=namespace_name,
        )
        workgroup = get_workgroup(
            redshift_serverless_client=redshift_serverless_client,
            workgroup_name=workgroup_name,
        )
        kwargs = dict(
            dbName=namespace.db_name,
            workgroupName=workgroup_name,
            customDomainName=custom_domain_name,
            durationSeconds=duration_seconds,
        )
        response = redshift_serverless_client.get_credentials(
            **remove_optional(**kwargs)
        )
        params = cls(
            host=workgroup.endpoint_address,
            port=workgroup.endpoint_port,
            username=response["dbUser"],
            password=response["dbPassword"],
            database=namespace.db_name,
            expiration=response["expiration"],
            next_refresh_time=response["nextRefreshTime"],
            namespace=namespace,
            workgroup=workgroup,
        )
        return params

    def get_connection(
        self,
        timeout: int = 3,
    ) -> "redshift_connector.Connection":
        """
        Create a Redshift connection using the parameters.

        :return: A redshift_connector.Connection object.
        """
        return redshift_connector.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
            is_serverless=True,
            timeout=timeout,
        )
