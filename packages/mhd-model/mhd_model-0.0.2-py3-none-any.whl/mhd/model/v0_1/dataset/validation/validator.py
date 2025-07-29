import logging
from typing import Any

import jsonschema
import jsonschema.protocols

from mhd.model.v0_1.dataset.validation.base import MhdModelValidator
from mhd.shared.model import ProfileEnabledDataset

logger = logging.getLogger(__name__)


class MhdFileValidator:
    def validate(self, json_file: dict[str, Any]):
        profile = ProfileEnabledDataset.model_validate(json_file)
        validator: jsonschema.protocols.Validator = MhdModelValidator.new_instance(
            profile.schema_name, profile.profile_uri
        )

        validations = validator.iter_errors(json_file)
        all_errors = [x for x in validations]
        return all_errors
