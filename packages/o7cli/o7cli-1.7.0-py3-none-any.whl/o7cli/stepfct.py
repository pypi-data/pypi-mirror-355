#!/usr/bin/env python
# ************************************************************************
# Copyright 2025 O7 Conseils inc (Philippe Gosselin)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ************************************************************************
"""Module allows to view and access Lambda Functions"""

# --------------------------------
#
# --------------------------------
import logging

# import datetime
import pprint

import o7util.menu as o7m
import o7util.terminal as o7t
from o7util.table import ColumnParam, Table, TableParam

from o7cli.base import Base

logger = logging.getLogger(__name__)


# *************************************************
#
# *************************************************
class Step(Base):
    """Class Step Functions"""

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/stepfunctions.html

    # *************************************************
    #
    # *************************************************
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = self.session.client("stepfunctions")

        self.state_machines = []
        self.state_machine_arn = ""
        self.state_machine_info = {}
        self.state_machine_executions = []

    # *************************************************
    #
    # *************************************************
    def load_state_machines(self):
        """Returns all State Machines in this Session"""

        logger.info("load_state_machines")

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/stepfunctions/client/list_state_machines.html
        paginator = self.client.get_paginator("list_state_machines")
        unsorted = []
        param = {}

        for page in paginator.paginate(**param):
            unsorted.extend(page.get("stateMachines", []))

        # pprint.pprint(unsorted)

        logger.info(f"load_functions: Number of Functions found {len(unsorted)}")
        self.state_machines = sorted(unsorted, key=lambda x: x.get("name", ""))
        return self

    # *************************************************
    #
    # *************************************************
    def load_state_machine(self):
        """Returns State Machine details"""

        logger.info(f"load_state_machine: state_machine_arn={self.state_machine_arn}")

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/stepfunctions/client/describe_state_machine.html
        self.state_machine_info = self.client.describe_state_machine(
            stateMachineArn=self.state_machine_arn, includedData="ALL_DATA"
        )

        # print(self.state_machine_info)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/stepfunctions/client/list_executions.html
        self.state_machine_executions = self.client.list_executions(
            stateMachineArn=self.state_machine_arn,
            maxResults=10,
        ).get("executions", [])
        # pprint.pprint(self.state_machine_executions)

        return self

    # *************************************************
    #
    # *************************************************
    def start_execution(self):
        """Starts the execution of a state machine"""

        logger.info(f"start_execution: state_machine_arn={self.state_machine_arn}")

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/stepfunctions/client/start_execution.html
        response = self.client.start_execution(
            stateMachineArn=self.state_machine_arn,
        )

        pprint.pprint(response)

        return response

    # *************************************************
    #
    # *************************************************
    def display_state_machines(self):
        """Displays a summary of Functions in a Table Format"""

        self.load_state_machines()
        params = TableParam(
            columns=[
                ColumnParam(title="id", type="i", min_width=4),
                ColumnParam(title="Name", type="str", data_col="name"),
                ColumnParam(title="Created", type="datetime", data_col="creationDate"),
                ColumnParam(title="Type", type="str", data_col="type"),
            ]
        )
        Table(params, self.state_machines).print()

        return self

    # *************************************************
    #
    # *************************************************
    def display_state_machine(self):
        """Displays a details of a functions"""

        self.load_state_machine()

        print()
        print(f"Name: {self.state_machine_info.get('name', 'na')}")
        print(f"Type: {self.state_machine_info.get('type', 'na')}")
        print(
            f"Status: {o7t.format_aws_state(self.state_machine_info.get('status', 'na'))}"
        )
        print()
        print(f"Role: {self.state_machine_info.get('roleArn', 'na')}")
        print()

        print("Executions")
        Table(
            TableParam(
                columns=[
                    ColumnParam(title="Started", type="datetime", data_col="startDate"),
                    ColumnParam(title="Stoped", type="datetime", data_col="stopDate"),
                    ColumnParam(
                        title="Status", type="str", data_col="status", format="aws-status"
                    ),
                    ColumnParam(title="Execution Name", type="str", data_col="name"),
                ],
            ),
            self.state_machine_executions,
        ).print()
        print()

    # *************************************************
    #
    # *************************************************
    def menu_state_machine(self, index):
        """Menu to view and edit all functions in current region"""

        if not 0 < index <= len(self.state_machines):
            return self

        self.state_machine_arn = self.state_machines[index - 1]["stateMachineArn"]

        obj = o7m.Menu(
            exit_option="b",
            title=f"State Machine - {self.state_machine_arn}",
            title_extra=self.session_info(),
            compact=False,
        )
        obj.add_option(
            o7m.Option(
                key="r",
                name="Display Raw Data",
                callback=lambda: pprint.pprint(self.state_machine_info),
            )
        )
        # obj.add_option(
        #     o7m.Option(
        #         key="l",
        #         name="Views Logs",
        #         callback=lambda: o7cli.logs.Logs(session=self.session).menu_log_streams(
        #             log_group_name=f"/aws/lambda/{self.fct_name}"
        #         ),
        #     )
        # )
        obj.add_option(
            o7m.Option(key="s", name="Start New Execution", callback=self.start_execution)
        )

        obj.display_callback = self.display_state_machine
        obj.loop()

        return self

    # *************************************************
    #
    # *************************************************
    def menu_state_machines(self):
        """Menu to view and edit all functions in current region"""

        obj = o7m.Menu(
            exit_option="b",
            title="Step Functions",
            title_extra=self.session_info(),
            compact=True,
        )

        obj.add_option(
            o7m.Option(
                key="r",
                name="Display Raw Data",
                callback=lambda: pprint.pprint(self.state_machines),
            )
        )
        obj.add_option(
            o7m.Option(
                key="int",
                name="Details for a state machine",
                callback=self.menu_state_machine,
            )
        )

        obj.display_callback = self.display_state_machines
        obj.loop()

        return self


# *************************************************
#
# *************************************************
def menu(**kwargs):
    """Run Main Menu"""
    Step(**kwargs).menu_state_machines()


# *************************************************
#
# *************************************************
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)-5.5s] [%(name)s] %(message)s"
    )

    step_obj = Step()
    # step_obj.menu_state_machines()

    # step_obj = Step().load_state_machines()
    # print(step_obj.state_machines)

    step_obj.state_machine_arn = (
        "arn:aws:states:ca-central-1:413285179088:stateMachine:stelar-devops-datalake"
    )
    step_obj.load_state_machine()

    pprint.pprint(step_obj.state_machine_executions)
