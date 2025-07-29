# -*- coding: utf-8 -*-

import aws_cdk as cdk
import cdkit.api as cdkit

from .cdk_stack_def import (
    ExperimentRedshiftServerlessStack,
    ExperimentRedshiftServerlessParams,
)

from .settings import settings

app = cdk.App()
stack = ExperimentRedshiftServerlessStack(
    scope=app,
    params=cdkit.StackParams(**settings.stack_ctx.to_stack_kwargs()),
    experiment_redshift_serverless_params=ExperimentRedshiftServerlessParams(
        id="ExperimentRedshiftServerless",
        vpc_id=settings.vpc_id,
        security_group_name=settings.security_group_name,
        namespace_name=settings.namespace_name,
        db_name=settings.db_name,
        workgroup_name=settings.workgroup_name,
    ),
)
