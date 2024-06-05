# variables.py
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Optional, Type

from gi.repository import Adw, Gdk, GObject, Gtk


class VariableProperties(GObject.Object):
    """An object that has variable properties."""

    __gtype_name__ = "ActionsVariableProperties"

    props: dict = {}

    @GObject.Signal(name="set-from-variable")
    def get_from_variable(self) -> None:
        """
        Emitted to signal that keys of `props` should be set from a `VariableReturn` if available.
        """


class VariableReturn:
    """An object that returns a variable by assigning it to `retval`."""

    type: Type = None
    retval: Any = None


class ActionsVariableRow(Gtk.ListBoxRow):
    """
    A row used to represent a property that can be defined by a variable.

    Will set `key` on `props` to the value when it changes.
    """

    __gtype_name__ = "ActionsVariableRow"

    _title: Optional[str] = None
    _subtitle: Optional[str] = None
    _icon_name: Optional[str] = None
    _source: Optional[VariableReturn] = None

    row: Adw.PreferencesRow
    props: VariableProperties
    key: Any

    type: Type = None

    @property
    def source(self) -> Optional[VariableReturn]:
        """The variable source for this row."""
        return self._source

    @source.setter
    def source(self, source: Optional[VariableReturn]) -> None:
        self._source = source

        if source:
            self.set_child(self.variable_row)
            self.change_variable_button.set_child(
                Adw.ButtonContent(icon_name=source.icon_name, label=source.title)
            )
            self.clear_variable_revealer.set_reveal_child(True)

        else:
            self.set_child(self.row)
            self.clear_variable_revealer.set_reveal_child(False)

    def get_source(self) -> Optional[VariableReturn]:
        """Gets the variable source for `self`."""
        return self.source

    def set_source(self, source: Optional[VariableReturn]) -> None:
        """Sets the variable source for `self`."""
        self.source = source

    @GObject.Property(type=str)
    def title(self) -> str:
        """The title of the action represented by this row."""
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    def get_title(self) -> str:
        """Gets the title for `self`."""
        return self.title

    def set_title(self, title: str) -> None:
        """Sets the title for `self`."""
        self.title = title

    @GObject.Property(type=str)
    def subtitle(self) -> str:
        """The subtitle for this row."""
        return self._subtitle

    @subtitle.setter
    def subtitle(self, subtitle: str) -> None:
        self._subtitle = subtitle

    def get_subtitle(self) -> str:
        """Gets the subtitle for `self`."""
        return self.subtitle

    def set_subtitle(self, subtitle: str) -> None:
        """Sets the subtitle for `self`."""
        self.subtitle = subtitle

    @GObject.Property(type=str)
    def icon_name(self) -> str:
        """The subtitle for this row."""
        return self._icon_name

    @icon_name.setter
    def icon_name(self, icon_name: str) -> None:
        self._icon_name = icon_name

    def get_icon_name(self) -> str:
        """Gets the icon name for `self`."""
        return self.icon_name

    def set_icon_name(self, icon_name: str) -> None:
        """Sets the icon name for `self`."""
        self.icon_name = icon_name

    def __init__(
        self,
        row: Adw.PreferencesRow,
        type: Type,
        props: VariableProperties,
        key: Any,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        icon_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(activatable=False, **kwargs)

        self.props = props

        self.props.connect(
            "set-from-variable",
            lambda *_: (
                self.props.props.update({self.key: self.source.retval})
                if self.source
                else self.update_props()
            ),
        )

        self.key = key

        self.title = title
        self.subtitle = subtitle
        self.icon_name = icon_name

        self.add_css_class("no-padding")
        self.set_row(row)

        self.change_variable_button = Gtk.Button(
            valign=Gtk.Align.CENTER, tooltip_text=_("Choose Variable"), has_frame=False
        )
        self.change_variable_button.connect(
            "clicked", lambda *_: self.choose_variable()
        )

        self.clear_variable_button = Gtk.Button(
            valign=Gtk.Align.CENTER, icon_name="edit-clear-symbolic", has_frame=False
        )
        self.clear_variable_button.connect("clicked", lambda *_: self.set_source(None))

        self.clear_variable_revealer = Gtk.Revealer(
            child=self.clear_variable_button,
            transition_type=Gtk.RevealerTransitionType.SLIDE_LEFT,
        )

        self.variable_box = Gtk.Box(spacing=3)
        self.variable_box.append(self.change_variable_button)
        self.variable_box.append(self.clear_variable_revealer)

        self.variable_row = Adw.ActionRow()
        self.bind_property(
            "title",
            self.variable_row,
            "title",
            GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE,
        )
        self.bind_property(
            "subtitle",
            self.variable_row,
            "subtitle",
            GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE,
        )

        self.variable_row.add_prefix(icon := Gtk.Image())
        self.bind_property(
            "icon-name",
            icon,
            "icon-name",
            GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE,
        )

        self.variable_row.add_suffix(self.variable_box)

    def update_props(self) -> None:
        """Updates `self.props` from the value in the widget."""

    def do_focus(self, direction: Gtk.DirectionType) -> bool:
        if not self.row:
            return False

        if self.get_focus_child() == self.row:
            return self.row.child_focus(direction)

        self.row.grab_focus()
        return True

    def choose_variable(self) -> None:
        """Starts a choose action for `self`."""
        if not (win := self.get_root()):
            return

        win.choose_variable(self)

    def set_row(self, row: Adw.PreferencesRow) -> None:
        """
        Sets row as a child of `self`.

        A suffix will be added to choose a variable.
        """
        self.row = row
        self.row.set_activatable(False)

        self.choose_variable_button = Gtk.Button(
            valign=Gtk.Align.CENTER,
            icon_name="step-in-symbolic",
            tooltip_text=_("Choose Variable"),
            has_frame=False,
        )
        self.choose_variable_button.connect(
            "clicked", lambda *_: self.choose_variable()
        )
        row.add_suffix(self.choose_variable_button)

        self.bind_property(
            "title",
            self.row,
            "title",
            GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE,
        )

        if isinstance(row, Adw.ActionRow):
            self.bind_property(
                "subtitle",
                self.row,
                "subtitle",
                GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE,
            )

        self.row.add_prefix(icon := Gtk.Image())
        self.bind_property(
            "icon-name",
            icon,
            "icon-name",
            GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE,
        )

        self.row.add_css_class("rounded")

        self.set_child(self.row)


class ActionsVariableSpinRow(ActionsVariableRow):
    """
    A row used to represent a property that can be changed via an `AdwSpinRow`
    or defined by a variable.
    """

    __gtype_name__ = "ActionsVariableSpinRow"

    row: Adw.SpinRow
    type = float

    def __init__(
        self, adjustment: Gtk.Adjustment, digits: Optional[int] = 0, **kwargs: Any
    ) -> None:
        super().__init__(
            Adw.SpinRow(adjustment=adjustment, digits=digits), float, **kwargs
        )

        self.row.connect("notify::value", lambda *_: self.update_props())

    def update_props(self) -> None:
        self.props.props.update({self.key: self.row.get_value()})


class ActionsVariableEntryRow(ActionsVariableRow):
    """
    A row used to represent a property that can be changed via an `AdwEntryRow`
    or defined by a variable.
    """

    __gtype_name__ = "ActionsVariableEntryRow"

    row: Adw.EntryRow
    type = str

    def __init__(self, text: Optional[str], **kwargs: Any) -> None:
        super().__init__(Adw.EntryRow(text=text or ""), str, **kwargs)

        self.row.connect("changed", lambda *_: self.update_props())

    def update_props(self) -> None:
        self.props.props.update({self.key: self.row.get_text()})
