# Copyright (c) [2018-2023]  Micro Focus or one of its affiliates.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from dbt.adapters.vertica.connections import verticaConnectionManager
from dbt.adapters.vertica.connections import verticaCredentials
from dbt.adapters.vertica.impl import verticaAdapter
from dbt.adapters.vertica.column import VerticaColumn
from dbt.adapters.vertica.relation import VerticaRelation


from dbt.adapters.base import AdapterPlugin
from dbt.include import vertica


Plugin = AdapterPlugin(
    adapter=verticaAdapter,
    credentials=verticaCredentials,
    include_path=vertica.PACKAGE_PATH)