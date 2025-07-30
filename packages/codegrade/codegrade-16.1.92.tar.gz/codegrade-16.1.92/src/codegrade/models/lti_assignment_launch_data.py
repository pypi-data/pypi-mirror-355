"""The module that defines the ``LTIAssignmentLaunchData`` model.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

import typing as t
from dataclasses import dataclass, field

import cg_request_args as rqa

from .. import parsers
from ..utils import to_dict
from .assignment import Assignment
from .base_launch_data import BaseLaunchData


@dataclass
class LTIAssignmentLaunchData(BaseLaunchData):
    """This is the data returned to the client after a successful LTI launch."""

    #: Always `normal_result`.
    type: "t.Literal['normal_result']"
    #: Same as `course` but the assignment instead.
    assignment: "Assignment"

    raw_data: t.Optional[t.Dict[str, t.Any]] = field(init=False, repr=False)

    data_parser: t.ClassVar = rqa.Lazy(
        lambda: BaseLaunchData.data_parser.parser.combine(
            rqa.FixedMapping(
                rqa.RequiredArgument(
                    "type",
                    rqa.StringEnum("normal_result"),
                    doc="Always `normal_result`.",
                ),
                rqa.RequiredArgument(
                    "assignment",
                    parsers.ParserFor.make(Assignment),
                    doc="Same as `course` but the assignment instead.",
                ),
            )
        ).use_readable_describe(True)
    )

    def to_dict(self) -> t.Dict[str, t.Any]:
        res: t.Dict[str, t.Any] = {
            "type": to_dict(self.type),
            "assignment": to_dict(self.assignment),
            "course": to_dict(self.course),
            "new_role_created": to_dict(self.new_role_created),
            "new_session": to_dict(self.new_session),
            "updated_email": to_dict(self.updated_email),
        }
        return res

    @classmethod
    def from_dict(
        cls: t.Type["LTIAssignmentLaunchData"], d: t.Dict[str, t.Any]
    ) -> "LTIAssignmentLaunchData":
        parsed = cls.data_parser.try_parse(d)

        res = cls(
            type=parsed.type,
            assignment=parsed.assignment,
            course=parsed.course,
            new_role_created=parsed.new_role_created,
            new_session=parsed.new_session,
            updated_email=parsed.updated_email,
        )
        res.raw_data = d
        return res


import os

if os.getenv("CG_GENERATING_DOCS", "False").lower() in ("", "true"):
    from .course import Course
    from .user_login_response import UserLoginResponse
