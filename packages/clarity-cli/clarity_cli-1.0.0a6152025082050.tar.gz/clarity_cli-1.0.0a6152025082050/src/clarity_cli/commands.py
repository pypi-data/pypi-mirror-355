from clarity_cli.outputs import CliOutput, CliTable
from clarity_cli.input import CliInputs
from clarity_cli.helpers import (is_logged_in, get_tests, trigger_test_execution, write_new_profile_to_config,
                                 get_profile_configuration, get_clarity_access_token, get_devices, format_device_state, get_params, parse_and_upload_poetry_package)
from clarity_cli.defs import TableColumn, ThemeColors, CONFIG_FILE, ProfileConfig, InputTypes
from clarity_cli.exceptions import StopCommand


class CliCommands():
    def __init__(self):
        self.out = CliOutput()
        self.input = CliInputs()

    def _get_current_profile_and_config(self, profile=None, override_config_path=None):
        config, profile_name = self.out.run_sync_function("Validate profile...",
                                                          get_profile_configuration, profile=profile, override_config_path=override_config_path)
        return config, profile_name

    def execute(self, ctx, test_id=None, profile=None, override_config_path=None, project=None, workspace=None, agent_id=None, parameters_file=None):
        """Execute a test from the available tests"""
        self.out.setup_context(ctx)
        self.input.setup_context(ctx)
        config, profile_name = self._get_current_profile_and_config(profile, override_config_path)
        web_token = is_logged_in(profile_name)

        project = project or config.project
        workspace = workspace or config.workspace
        agent_id = agent_id or config.agent

        if not project:
            self.out.vprint("project wasn't provided, asking user")
            project = self.input.ask_for_text_input("Project id")
        if not workspace:
            self.out.vprint("workspace id wasn't provided, asking user")
            workspace = self.input.ask_for_text_input("Workspace id")

        self.out.main_message("Test Execution")

        # Display available tests in a table
        test_execution_columns = [TableColumn("ID", ThemeColors.CYAN),
                                  TableColumn("Name", ThemeColors.GREEN),
                                  TableColumn("Version", ThemeColors.RED),
                                  TableColumn("Description", ThemeColors.YELLOW)]
        tests_table = CliTable("Available Tests", test_execution_columns)
        available_tests, params = self.out.run_sync_function("Getting Tests...", get_tests, token=web_token, workspace_id=workspace, domain=config.domain)

        selected_test = None

        # If test ID is provided directly, use it
        if test_id:
            selected_test = next((test for test in available_tests if test["test_id"] == test_id), None)
            if not selected_test:
                raise StopCommand(f"Error: Test with ID '{test_id}' not found")

            self.input.ask_for_confirmation(f"Execute test '{selected_test['test_name']}' ({test_id})?")
            selected_test_id = test_id

        # If no test ID provided, use interactive selection
        else:
            tests_table.add_data(available_tests,
                                 headers_mapping={"ID": "test_id", "Name": "test_name", "Version": "test_version", "Description": "description"})
            tests_table.print_table()
            # Create choices for the test selection
            choices = [f"{test['test_id']} - {test['test_name']}, {test['test_version']}" for test in available_tests]
            selected = self.input.ask_for_input_from_list("Select a test to execute", choices)

            # Get the selected test ID
            selected_test_id = selected.split(' - ')[0]
            selected_test = next((test for test in available_tests if test["test_id"] == selected_test_id), None)

            if not selected_test:
                raise StopCommand("Error: Could not find the selected test")

        if selected_test.get('iot_device_required'):
            if not agent_id:
                self.out.vprint("agent id wasn't provided, asking user")
                devices_column = [TableColumn("Name", ThemeColors.CYAN),
                                  TableColumn("ID"),
                                  TableColumn("Version"),
                                  TableColumn("Status")]
                available_devices = self.out.run_sync_function("Getting devices...", get_devices, token=web_token, workspace_id=workspace, domain=config.domain)
                devices_by_name = {}
                for device in available_devices:
                    format_device_state(device)
                    devices_by_name[device['device_name']] = device
                devices_table = CliTable("Available Devices", devices_column)
                devices_table.add_data(available_devices,
                                       headers_mapping={"ID": "device_id", "Name": "device_name", "Version": "iot_client_version", "Status": "state"})
                devices_table.print_table()
                agent_name = self.input.ask_for_input_from_list("Please select an agent id", devices_by_name.keys())
                agent_id = devices_by_name.get(agent_name)
            if not agent_id:
                raise StopCommand("Agent was not provided, please ")

        self.out.main_message("Configure flow parameters")
        self.out.vprint(f"test flow param config:\n{params[selected_test_id].get('properties', {})}")
        if parameters_file:
            self.out.vprint(f"Loading parameters file: {parameters_file}")
            params_from_config = get_params(parameters_file)
        else:
            params_from_config = {}

        for param_name, param in params[selected_test_id].get('properties', {}).items():
            if param.get('type') in list(InputTypes.__members__):
                input_value = self.input.ask_for_text_input(param_name, default=param.get('default'))
                if input_value:
                    if params_from_config.get(param_name):
                        self.out.vprint(f"Got param: {param_name} from file, value: {params_from_config[param_name]}")
                        param['default'] = params_from_config[param_name]
                    else:
                        self.out.vprint(f"Got param: {param_name} user: { InputTypes[param['type']].value(input_value)}")
                        param['default'] = InputTypes[param['type']].value(input_value)
        if not params[selected_test_id]:
            self.out.warning("Flow variables weren't found")
        # Execute the test (in a real app, this would trigger an actual test)
        web_token = is_logged_in(profile_name)
        execution_url = self.out.run_sync_function(f"Executing: {selected_test['test_name']}...",
                                                   function=trigger_test_execution, domain=config.domain, token=web_token, workspace=workspace,
                                                   project_id=project, agent_id=agent_id, test_id=selected_test_id, params=params[selected_test_id])

        self.out.ok(f"Successfully executed test: {CliOutput.bold(selected_test['test_name'])}")
        self.out.print(f"[dim]Results will be available in the dashboard: {execution_url}[/dim]")

    def write_profile_to_config(self, ctx, profile_name=None, client_id=None, client_secret=None, token_endpoint=None,
                                scope=None, project=None, workspace=None, agent_id=None, domain=None, default=None):
        self.out.setup_context(ctx)
        self.input.setup_context(ctx)
        self.out.main_message("New Profile")
        if not profile_name:
            self.out.vprint("profile name wasn't provided, asking user")
            profile_name = self.input.ask_for_text_input("Profile name")
        if not client_id:
            self.out.vprint("client_id wasn't provided, asking user")
            client_id = self.input.ask_for_text_input("Client id")
        if not client_secret:
            self.out.vprint("client_secret wasn't provided, asking user")
            client_secret = self.input.ask_for_password_input("Client secret")
        if not token_endpoint:
            self.out.vprint("token endpoint wasn't provided, asking user")
            token_endpoint = self.input.ask_for_password_input("Token endpoint")
        if not scope:
            self.out.vprint("scope wasn't provided, asking user")
            scope = self.input.ask_for_password_input("Scope")
        if not domain:
            self.out.vprint("domain wasn't provided, asking user")
            domain = self.input.ask_for_text_input("Clarity domain")
        if not project:
            self.out.vprint("project wasn't provided, asking user")
            project = self.input.ask_for_text_input("Project id", optional=True)
        if not workspace:
            self.out.vprint("workspace provided, asking user")
            workspace = self.input.ask_for_text_input("Workspace id", optional=True)
        if not agent_id:
            self.out.vprint("agent_id wasn't provided, asking user")
            agent_id = self.input.ask_for_text_input("Agent id", optional=True)
        if default is None:
            default = self.input.ask_for_confirmation("Set this profile as default?", default=False)
        if profile_name and client_id and client_secret and token_endpoint and scope and domain:
            columns = [TableColumn("Property", ThemeColors.CYAN), TableColumn("Value", ThemeColors.GREEN)]
            table = CliTable("New Profile", columns)
            table_data = [
                {"property": "Profile name", "value": profile_name},
                {"property": "Client id", "value": client_id},
                {"property": "Client secret", "value": client_secret},
                {"property": "Clarity domain", "value": domain},
                {"property": "Default Project id", "value": project},
                {"property": "Default workspace id", "value": workspace},
                {"property": "Default agent id", "value": agent_id},
                {"property": "Is default", "value": str(default)}
            ]
            table.add_data(table_data, headers_mapping={"Property": "property", "Value": "value"})
            table.print_table()
            self.input.ask_for_confirmation("Setup the new profile?", default=True, hard_stop=True)
        else:
            raise StopCommand("Missing property")

        config = ProfileConfig(client_id=client_id, client_secret=client_secret, domain=domain, token_endpoint=token_endpoint, scope=scope,
                               project=project, workspace=workspace, agent_id=agent_id)
        self.out.run_sync_function(f"Configuring new profile {profile_name}...",
                                   write_new_profile_to_config, profile_name=profile_name, default=default, config=config)
        self.out.ok(f"New profile {CliOutput.bold(profile_name)} successfully configured")
        self.out.vprint(f"All profiles can be found at: {CONFIG_FILE}")

    def login_using_config_file(self, ctx, profile=None, override_config_path=None):
        self.out.setup_context(ctx)
        self.input.setup_context(ctx)
        config, profile = self._get_current_profile_and_config(profile, override_config_path)
        self.out.run_sync_function("Logging in", get_clarity_access_token, profile=profile, client_id=config.client_id,
                                   client_secret=config.client_secret, token_endpoint=config.token_endpoint, scope=config.scope)
        self.out.ok("Successfully logged in!")

    def upload_component_from_package(self, ctx, profile=None, override_config_path=None, component_path=None, default_entrypoint=None, default_running_env=None, pyc=None):
        self.out.setup_context(ctx)
        self.input.setup_context(ctx)
        config, profile_name = self._get_current_profile_and_config(profile, override_config_path)
        web_token = is_logged_in(profile_name)
        if not component_path:
            self.out.vprint("component path wasn't provided, asking user")
            component_path = self.input.ask_for_text_input("Component path (path to poetry project directory)")
        parse_and_upload_poetry_package(package_dir=component_path, domain=config.domain, workspace_id=config.workspace,
                                        auth_token=web_token, default_entrypoint=default_entrypoint, default_running_env=default_running_env, pyc=pyc)
