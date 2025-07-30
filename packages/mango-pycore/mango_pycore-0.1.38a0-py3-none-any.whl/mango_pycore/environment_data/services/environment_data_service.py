import datetime

from mango_pycore.environment_data.adapters.access_control_adapter import AccessControl
from mango_pycore.environment_data.adapters.s3_environment_adapter import S3Environment
from mango_pycore.environment_data.datatypes import EnvironmentDriver
from mango_pycore.tools.utils import set_environment_vars

_ENVIRONMENT_VARS = {}


class EnvironmentDataService:
    def __init__(self, driver: str, parameters: dict):

        assert driver in EnvironmentDriver, "Allowed values for driver are access_control, s3"

        self._driver = None
        if driver == "access_control":
            assert parameters.get('url'), "url parameter is missing for access control driver"
            assert parameters.get('secret_b'), "secret_b parameter is missing for access control driver"
            assert parameters.get('uuid_key'), "uuid_key parameter is missing for access control driver"

            self._driver = AccessControl(
                url=parameters["url"],
                secret_b=parameters["secret_b"],
                uuid_key=parameters["uuid_key"],
                module_pk=parameters.get("module_pk", ""),
                module_sk=parameters.get("module_sk", "")
            )

        if driver == "s3":
            assert parameters.get('bucket'), "bucket parameter is missing for s3 driver"
            assert parameters.get('key'), "key parameter is missing for s3 driver"
            assert parameters.get('role'), "role parameter is missing for s3 driver"

            self._driver = S3Environment(
                bucket=parameters["bucket"],
                key=parameters["key"],
                role=parameters["role"]
            )

    def load_environment_data(self, origin: str):
        global _ENVIRONMENT_VARS
        if self._driver:
            date = datetime.datetime.now()

            # origin is not in environment or environment does not exist
            if origin not in _ENVIRONMENT_VARS:
                data = self._driver.get_backend_data(origin)
                if data:
                    _ENVIRONMENT_VARS[origin] = {
                        "date": date,
                        "data": data
                    }

            # Origin was found
            else:
                if (date - _ENVIRONMENT_VARS[origin]["date"]).seconds > 300:  # Data is deprecated by timeout of 5 min
                    data = self._driver.get_backend_data(origin)
                    if data:
                        _ENVIRONMENT_VARS[origin] = {
                            "date": date,
                            "data": data
                        }

        if origin in _ENVIRONMENT_VARS:
            set_environment_vars(origin=origin, data=_ENVIRONMENT_VARS[origin]["data"])
            if isinstance(_ENVIRONMENT_VARS[origin]["data"], dict):
                _ENVIRONMENT_VARS[origin]["data"].update({
                    "ORIGIN": origin
                })
            return _ENVIRONMENT_VARS[origin]["data"]
