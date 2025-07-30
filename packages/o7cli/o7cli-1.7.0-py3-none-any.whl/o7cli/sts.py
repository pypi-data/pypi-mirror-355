# ************************************************************************
# Copyright 2021 O7 Conseils inc (Philippe Gosselin)
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
"""Module for AWS Security Token Service (STS)"""

# --------------------------------
#
# --------------------------------
import logging

from o7cli.base import Base

logger = logging.getLogger(__name__)

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html


# *************************************************
#
# *************************************************
class Sts(Base):
    """Class for AWS Security Token Service (STS)"""

    # *************************************************
    #
    # *************************************************
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sts = self.session.client(
            "sts",
            region_name=self.session.region_name,
            endpoint_url=f"https://sts.{self.session.region_name}.amazonaws.com",
        )

    # *************************************************
    #
    # *************************************************
    def get_account_id(self):
        """Get the account id"""

        resp = self.sts.get_caller_identity()
        ret = resp.get("Account")
        return ret

    # *************************************************
    #
    # *************************************************
    def get_root_account_summary(self, account_id=None):
        """Get the root session for the account"""

        if account_id is None:
            account_id = self.get_account_id()

        logger.info(f"Getting root account summary for: {account_id}")

        try:
            cred = self.sts.assume_root(
                TargetPrincipal=account_id,
                TaskPolicyArn={
                    "arn": "arn:aws:iam::aws:policy/root-task/IAMAuditRootUserCredentials"
                },
                DurationSeconds=60,
            ).get("Credentials")

        except Exception as e:
            logger.error(f"Error assuming root account: {e}")
            return {}

        iam_client = self.session.client(
            "iam",
            aws_access_key_id=cred.get("AccessKeyId"),
            aws_secret_access_key=cred.get("SecretAccessKey"),
            aws_session_token=cred.get("SessionToken"),
            region_name=self.session.region_name,
        )

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/get_account_summary.html
        resp = iam_client.get_account_summary()

        return resp.get("SummaryMap")
