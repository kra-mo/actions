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
            self.emit("get-from-variable")
            self._get_action_func()()

        return wrapper

    def _get_action_func(self) -> Callable: ...

    def get_widget(self) -> Gtk.Widget: ...

    def _done(self) -> None:
        if self.cb:
            self.cb()


class NotificationAction(Action):
    """An action to send a desktop notification."""

    __gtype_name__ = "ActionsNotificationAction"

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
                self.props["title"] or "",
                props=self,
                key="title",
                title=_("Title"),
            )
        )

        expander.add_row(
            ActionsVariableEntryRow(
                self.props["body"] or "",
                props=self,
                key="body",
                title=_("Description"),
            )
        )

        return expander


class RingBellAction(Action):
    """An action that emits a short beep."""

    __gtype_name__ = "ActionsRingBellAction"

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
    """An action to wait a certain number of seconds."""

    __gtype_name__ = "ActionsWaitAction"

    ident = "wait"
    title = _("Wait")
    icon_name = "preferences-system-time-symbolic"
    type = float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {"seconds": 5}

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
                title=_("Wait"),
                subtitle=_("Seconds"),
                icon_name=self.icon_name,
            )
        )

        return spin_row


types = (NotificationAction, RingBellAction, WaitAction)
actions = {}

for type in types:
    actions[type.ident] = type
