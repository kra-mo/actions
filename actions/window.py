# window.py
#
# Copyright 2024 kramo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""The main application window."""

import logging
from collections import namedtuple
from typing import Any

from gi.repository import Adw, Gio, Gtk

from actions import shared
from actions.actions import Action, actions  # yo dawg

Action = namedtuple("Action", "title props")


@Gtk.Template(resource_path=f"{shared.PREFIX}/gtk/window.ui")
class ActionsWindow(Adw.ApplicationWindow):
    """The main application window."""

    __gtype_name__ = "ActionsWindow"

    navigation_view: Adw.NavigationView = Gtk.Template.Child()
    status_page: Adw.StatusPage = Gtk.Template.Child()

    actions_dialog: Adw.Dialog = Gtk.Template.Child()
    actions_group: Adw.PreferencesGroup = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.active_group = None
        self.actions = []

        if shared.PROFILE == "development":
            self.add_css_class("devel")

        self.status_page.set_icon_name(shared.APP_ID)

        for action in actions.values():
            self.actions_group.add(
                row := Adw.ButtonRow(
                    title=action.title, start_icon_name=action.icon_name
                )
            )
            row.connect("activated", lambda _obj, a=action: self.add_action(a))

    def add_action(self, action: Action) -> None:
        """Appends `action` to the workflow."""
        self.actions_dialog.force_close()

        if not self.active_group:
            return

        instance = action(self.get_application())

        self.actions.append(instance)
        self.active_group.add(instance.get_widget())

    def run(self) -> None:
        """Executes the workflow."""

        if not (length := len(self.actions)):
            return

        last = length - 1

        for index, action in reversed(list(enumerate(self.actions))):
            if index != last:
                action.cb = self.actions[index + 1].get_callable()

            if index == 0:
                action.get_callable()()

    @Gtk.Template.Callback()
    def create_workflow(self, *_args: Any) -> None:
        self.active_group = Adw.PreferencesGroup(separate_rows=True)

        (page := Adw.PreferencesPage()).add(self.active_group)

        page.add(add_group := Adw.PreferencesGroup())

        add_group.add(
            add_button := Adw.ButtonRow(
                title=_("Add Action"), start_icon_name="list-add-symbolic"
            )
        )

        add_button.connect("activated", lambda *_: self.actions_dialog.present(self))

        header_bar = Adw.HeaderBar()

        header_bar.pack_end(
            run_button := Gtk.Button(
                has_frame=False,
                child=Adw.ButtonContent(
                    icon_name="media-playback-start-symbolic", label=_("Run")
                ),
            )
        )

        run_button.connect("clicked", lambda *_: self.run())

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header_bar)
        toolbar_view.set_content(page)

        self.navigation_view.push(
            Adw.NavigationPage.new(toolbar_view, _("New Workflow"))
        )
