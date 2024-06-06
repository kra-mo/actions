# actions.py
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

from typing import Any, Callable, Optional

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from actions.variables import (
    ActionsVariableEntryRow,
    ActionsVariableSpinRow,
    VariableProperties,
    VariableReturn,
)


class Action(VariableReturn, VariableProperties):  # 🧑‍⚖️
    """The smallest part of a workflow."""

    __gtype_name__ = "ActionsAction"

    ident: str
    title: str
    icon_name: str
    app: Gtk.Application
    cb: Optional[Callable] = None

    retval: None = None

    def __init__(self, app: Gtk.Application) -> None:
        VariableReturn.__init__(self)
        VariableProperties.__init__(self)

        self.app = app

    def get_callable(self) -> Callable:
        def wrapper() -> None:
            self.emit("set-from-variable")
            self._get_action_func()()

        return wrapper

    def _get_action_func(self) -> Callable: ...

    def get_widget(self) -> Gtk.Widget: ...

    def _done(self) -> None:
        if self.cb:
            self.cb()


class NotificationAction(Action):
    __gtype_name__ = "ActionsNotificationAction"

    doc = _(
        """
        Sends a desktop notification.


        <big><b>Input</b></big>

        Title: <i>Text</i>
        Description: <i>Text</i>
        """
    )

    ident = "notification"
    title = _("Send Notification")
    icon_name = "preferences-system-notifications-symbolic"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {
            "title": _("Hello World!"),
            "body": None,
        }

    def _get_action_func(self) -> Callable:
        def send_notification() -> None:
            if not (self.app):
                return

            notif = Gio.Notification.new(self.props["title"] or _("Notification"))

            if body := self.props["body"]:
                notif.set_body(body)

            self.app.send_notification(None, notif)

            self._done()

        return send_notification

    def get_widget(self) -> Gtk.Widget:
        (expander := Adw.ExpanderRow(title=self.title)).add_prefix(
            Gtk.Image(icon_name=self.icon_name)
        )

        expander.add_row(
            ActionsVariableEntryRow(
                self.props["title"],
                props=self,
                key="title",
                title=_("Title"),
            )
        )

        expander.add_row(
            ActionsVariableEntryRow(
                self.props["body"],
                props=self,
                key="body",
                title=_("Description"),
            )
        )

        return expander


class RingBellAction(Action):
    __gtype_name__ = "ActionsRingBellAction"

    doc = _(
        """
        Emits a short beep.
        """
    )

    ident = "ring-bell"
    title = _("Play Alert Sound")
    icon_name = "audio-volume-high-symbolic"

    def _get_action_func(self) -> Callable:

        def ring_bell() -> None:
            if not (display := Gdk.Display.get_default()):
                return

            display.beep()

            self._done()

        return ring_bell

    def get_widget(self) -> Gtk.Widget:
        return Adw.ActionRow(title=self.title, icon_name=self.icon_name)


class WaitAction(Action):
    __gtype_name__ = "ActionsWaitAction"

    doc = _(
        """
        Pauses the workflow for a certain number of seconds.


        <big><b>Input</b></big>

        Seconds: <i>Number (0 – 86400)</i>


        <big><b>Output</b></big>

        Seconds: <i>Number (0 – 86400)</i>
        """
    )

    ident = "wait"
    title = _("Wait")
    icon_name = "preferences-system-time-symbolic"
    type = float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {
            "seconds": 5,
        }

    def _get_action_func(self) -> Callable:

        def wait() -> None:
            if not self.cb:
                return

            def timeout_done() -> None:
                self.retval = self.props["seconds"]
                self._done()

            GLib.timeout_add_seconds(self.props["seconds"], timeout_done)

        return wait

    def get_widget(self) -> Gtk.Widget:
        (
            spin_row := ActionsVariableSpinRow(
                Gtk.Adjustment(
                    step_increment=1,
                    upper=86400,  # 24 hours
                    lower=0,
                    value=self.props["seconds"],
                ),
                props=self,
                key="seconds",
                title=self.title,
                subtitle=_("Seconds"),
                icon_name=self.icon_name,
            )
        )

        return spin_row


class ReturnAction(Action):
    __gtype_name__ = "ActionsReturnAction"

    doc = _(
        """
        Stops the workflow permanently.
        """
    )

    ident = "return"
    title = _("End")
    icon_name = "media-playback-stop-symbolic"

    def _get_action_func(self) -> Callable:
        return lambda: None

    def get_widget(self) -> Gtk.Widget:
        return Adw.ActionRow(title=self.title, icon_name=self.icon_name)


class FloatVariableAction(Action):
    __gtype_name__ = "ActionsFloatVariableAction"

    doc = _(
        """
        Simply stores a number in a variable.


        <big><b>Input</b></big>

        Number: <i>Number (-1e15 – 1e15)</i>


        <big><b>Output</b></big>

        Number: <i>Number (-1e15 – 1e15)</i>
        """
    )

    ident = "float"
    title = _("Number")
    icon_name = "accessories-calculator-symbolic"
    type = float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {
            "float": 10.0,
        }

    def _get_action_func(self) -> Callable:

        def number() -> None:
            self.retval = self.props["float"]
            self._done()

        return number

    def get_widget(self) -> Gtk.Widget:
        (
            spin_row := ActionsVariableSpinRow(
                Gtk.Adjustment(
                    step_increment=1,
                    # Biggest/smallest even numbers where `SpinRow` still works correctly
                    upper=1e15,
                    lower=-1e15,
                    value=self.props["float"],
                ),
                digits=3,
                props=self,
                key="float",
                title=self.title,
                icon_name=self.icon_name,
            )
        )

        return spin_row


class StringVariableAction(Action):
    __gtype_name__ = "ActionsTextVariableAction"

    doc = _(
        """
        Simply stores text in a variable.


        <big><b>Input</b></big>

        Text: <i>Text</i>


        <big><b>Output</b></big>

        Text: <i>Text</i>
        """
    )

    ident = "string"
    title = _("Text")
    icon_name = "text-x-generic-symbolic"
    type = str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {
            "string": None,
        }

    def _get_action_func(self) -> Callable:
        def text() -> None:
            self.retval = self.props["string"]
            self._done()

        return text

    def get_widget(self) -> Gtk.Widget:
        return ActionsVariableEntryRow(
            self.props["string"],
            props=self,
            key="string",
            title=self.title,
            icon_name=self.icon_name,
        )


groups = {
    _("System"): (
        NotificationAction,
        RingBellAction,
    ),
    _("Logic"): (
        WaitAction,
        ReturnAction,
    ),
    _("Variables"): (
        FloatVariableAction,
        StringVariableAction,
    ),
}
