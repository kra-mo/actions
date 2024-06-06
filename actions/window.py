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
from textwrap import dedent
from typing import Any, Optional

from gi.repository import Adw, Gio, Gtk, Pango

from actions import shared
from actions.actions import Action, groups
from actions.variables import ActionsVariableRow

Action = namedtuple("Action", "title props")


@Gtk.Template(resource_path=f"{shared.PREFIX}/gtk/window.ui")
class ActionsWindow(Adw.ApplicationWindow):
    """The main application window."""

    __gtype_name__ = "ActionsWindow"

    navigation_view: Adw.NavigationView = Gtk.Template.Child()
    status_page: Adw.StatusPage = Gtk.Template.Child()

    actions_dialog: Adw.PreferencesDialog = Gtk.Template.Child()
    actions_page: Adw.PreferencesPage = Gtk.Template.Child()

    add_group: Optional[Adw.PreferencesGroup] = None

    header_bar: Optional[Adw.HeaderBar] = None
    run_button: Optional[Gtk.Button] = None
    cancel_revealer: Optional[Gtk.Revealer] = None
    cancel_button: Optional[Gtk.Button] = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.actions_box = None
        self.actions = {}

        if shared.PROFILE == "development":
            self.add_css_class("devel")

        self.status_page.set_icon_name(shared.APP_ID)

        for title, actions in groups.items():
            group = Adw.PreferencesGroup(title=title, separate_rows=True)

            for index, action in enumerate(actions):
                group.add(row := Adw.ActionRow(title=action.title, activatable=True))
                row.add_prefix(Gtk.Image(icon_name=action.icon_name))
                row.add_suffix(
                    info_button := Gtk.Button(
                        has_frame=False,
                        valign=Gtk.Align.CENTER,
                        icon_name="info-outline-symbolic",
                        tooltip_text=_("More Information"),
                    )
                )

                toolbar_view = Adw.ToolbarView()
                toolbar_view.add_top_bar(Adw.HeaderBar())
                # TODO: Translations
                toolbar_view.set_content(
                    Gtk.ScrolledWindow(
                        child=Gtk.Label(
                            margin_start=24,
                            margin_end=24,
                            halign=Gtk.Align.START,
                            valign=Gtk.Align.START,
                            xalign=0.0,
                            label=dedent(action.doc),
                            wrap=True,
                            use_markup=True,
                            attributes=Pango.AttrList.from_string("0 -1 size 13000"),
                        )
                    )
                )

                row.connect("activated", lambda _obj, a=action: self.add_action(a))
                info_button.connect(
                    "clicked",
                    lambda _obj, view=toolbar_view, title=action.title: self.actions_dialog.push_subpage(
                        Adw.NavigationPage.new(view, title)
                    ),
                )

            self.actions_page.add(group)

    def add_action(self, action: Action) -> None:
        """Appends `action` to the workflow."""
        self.actions_dialog.force_close()

        if not self.actions_box:
            return

        instance = action(self.get_application())
        widget = instance.get_widget()

        self.actions[widget] = instance
        self.actions_box.append(widget)

    def run(self) -> None:
        """Executes the workflow."""

        if not (length := len(self.actions)):
            return

        last = length - 1

        values = list(self.actions.values())

        for index, action in reversed(list(enumerate(values))):
            if index != last:
                action.cb = values[index + 1].get_callable()

            if index == 0:
                action.get_callable()()

    def choose_variable(self, row: ActionsVariableRow) -> None:
        self.header_bar.set_show_back_button(False)
        self.cancel_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self.cancel_revealer.set_reveal_child(True)
        self.run_button.set_sensitive(False)
        self.add_group.set_sensitive(False)

        reached = False
        for widget, action in self.actions.items():
            widget.set_can_target(False)
            reached = reached or action == row.props

            if reached or (action.type != row.type):
                widget.set_sensitive(False)
                continue

        self.actions_box.set_selection_mode(Gtk.SelectionMode.BROWSE)
        self.actions_box.connect("row-selected", self.on_row_selected, row)

    def on_row_selected(
        self,
        _obj: Any = None,
        selected_row: Optional[Gtk.ListBoxRow] = None,
        variable_row: Optional[ActionsVariableRow] = None,
    ) -> None:
        self.header_bar.set_show_back_button(True)
        self.cancel_revealer.set_transition_type(Gtk.RevealerTransitionType.NONE)
        self.cancel_revealer.set_reveal_child(False)
        self.run_button.set_sensitive(True)
        self.add_group.set_sensitive(True)

        self.actions_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.actions_box.disconnect_by_func(self.on_row_selected)

        for widget in self.actions:
            widget.set_can_target(True)
            widget.set_sensitive(True)

        if not selected_row:
            return

        variable_row.source = self.actions[selected_row]

    @Gtk.Template.Callback()
    def create_workflow(self, *_args: Any) -> None:
        self.actions_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.actions_box.add_css_class("boxed-list-separate")

        (group := Adw.PreferencesGroup()).add(self.actions_box)
        (page := Adw.PreferencesPage()).add(group)

        self.add_group = Adw.PreferencesGroup()

        page.add(self.add_group)

        self.add_group.add(
            add_button := Adw.ButtonRow(
                title=_("Add Action"), start_icon_name="list-add-symbolic"
            )
        )

        add_button.connect("activated", lambda *_: self.actions_dialog.present(self))

        self.header_bar = Adw.HeaderBar()

        self.cancel_button = Gtk.Button(label=_("Cancel"))
        self.cancel_button.connect("clicked", lambda *_: self.on_row_selected())

        self.cancel_revealer = Gtk.Revealer(child=self.cancel_button)

        self.header_bar.pack_start(self.cancel_revealer)

        self.run_button = Gtk.Button(
            has_frame=False,
            child=Adw.ButtonContent(
                icon_name="media-playback-start-symbolic", label=_("Run")
            ),
        )
        self.run_button.connect("clicked", lambda *_: self.run())

        self.header_bar.pack_end(self.run_button)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(self.header_bar)
        toolbar_view.set_content(page)

        self.navigation_view.push(
            Adw.NavigationPage.new(toolbar_view, _("New Workflow"))
        )
