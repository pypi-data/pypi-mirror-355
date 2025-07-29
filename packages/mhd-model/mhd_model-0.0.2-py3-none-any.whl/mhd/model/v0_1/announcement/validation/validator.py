from __future__ import annotations

import logging
from typing import Any

import jsonschema
import jsonschema.protocols

from mhd.model.v0_1.announcement.validation.base import ProfileValidator
from mhd.model.v0_1.announcement.validation.definitions import (
    CheckChildCvTermKeyValues,
    CheckCvTermKeyValue,
    CheckCvTermKeyValues,
)
from mhd.shared.model import ProfileEnabledDataset
from mhd.shared.validation.definitions import (
    AccessibleCompactURI,
    AccessibleURI,
    AllowAnyCvTerm,
    AllowedChildrenCvTerms,
    AllowedCvList,
    AllowedCvTerms,
    ProfileValidationGroup,
)
from mhd.shared.validation.registry import (
    register_validator_class,
    unregister_validator_class,
)

logger = logging.getLogger(__name__)


class MhdAnnouncementFileValidator:
    validators = {
        "validation-group": ProfileValidationGroup,
        "allowed-cv-terms": AllowedCvTerms,
        "allowed-children-cv-terms": AllowedChildrenCvTerms,
        "allow-any-cv-term": AllowAnyCvTerm,
        "allowed-cv-list": AllowedCvList,
        "accessible-uri": AccessibleURI,
        "accessible-compact-uri": AccessibleCompactURI,
        "check-protocol-parameters": CheckChildCvTermKeyValues,
        "check-cv-term-key-values": CheckCvTermKeyValues,
        "check-cv-term-key-value": CheckCvTermKeyValue,
    }

    def register_validators(self):
        for k, v in self.validators.items():
            register_validator_class(k, v)

    def unregister_validators(self):
        for k, v in self.validators.items():
            unregister_validator_class(k)

    def validate(
        self, announcement_file_json: dict[str, Any]
    ) -> list[jsonschema.ValidationError]:
        self.register_validators()
        profile = ProfileEnabledDataset.model_validate(announcement_file_json)
        validator: jsonschema.protocols.Validator = ProfileValidator.new_instance(
            profile.schema_name, profile.profile_uri
        )
        validations = validator.iter_errors(announcement_file_json)

        all_errors = [x for x in validations]

        def update_context(
            error: jsonschema.ValidationError, parent: jsonschema.ValidationError
        ):
            error.parent = parent
            if error.context:
                for item in error.context:
                    if isinstance(item, jsonschema.ValidationError):
                        item.parent = error
                        update_context(item, error)

        profile_validator = ProfileValidator()

        for x in all_errors:
            if x.validator in profile_validator.validators:
                update_context(x, x.parent)

        return all_errors
