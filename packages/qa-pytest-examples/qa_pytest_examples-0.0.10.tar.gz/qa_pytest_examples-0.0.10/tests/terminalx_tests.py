# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from hamcrest import is_  # type: ignore
import pytest
from qa_pytest_examples.model.terminalx_user import TerminalXUser
from qa_pytest_webdriver.selenium_tests import SeleniumTests
from qa_pytest_examples.terminalx_configuration import TerminalXConfiguration
from qa_testing_utils.matchers import contains_string_ignoring_case, traced, yields_item
from qa_pytest_examples.terminalx_steps import TerminalXSteps


@pytest.mark.external
@pytest.mark.selenium
class TerminalXTests(
    SeleniumTests[TerminalXSteps[TerminalXConfiguration],
                  TerminalXConfiguration]):
    _steps_type = TerminalXSteps
    _configuration = TerminalXConfiguration()

    # NOTE sections may be further collected in superclasses and reused across tests
    def login_section(
            self, user: TerminalXUser) -> TerminalXSteps[TerminalXConfiguration]:
        return (self.steps
                .given.terminalx(self.web_driver)
                .when.logging_in_with(user.credentials)
                .then.the_user_logged_in(is_(user.name)))

    def should_login(self):
        self.login_section(self.configuration.random_user)

    def should_find(self):
        (self.login_section(self.configuration.random_user)
            .when.clicking_search())

        for word in ["hello", "kitty"]:
            (self.steps
             .when.searching_for(word)
             .then.the_search_hints(yields_item(traced(
                 contains_string_ignoring_case(word)))))
