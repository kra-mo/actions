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


class Action:  # 🧑‍⚖️
    """The smallest part of a workflow."""

    ident: str
    title: str
    icon_name: str
    app: Gtk.Application
    props: dict
    cb: Optional[Callable] = None

    def __init__(self, app: Gtk.Application) -> None:
        self.app = app

    def get_callable(self) -> Callable: ...

    def get_widget(self) -> Gtk.Widget: ...

    def _done(self) -> None:
        if self.cb:
            self.cb()


class NotificationAction(Action):
    ident = "notification"
    title = _("Send Notification")
    icon_name = "preferences-system-notifications-symbolic"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {
            "title": _("Hello World!"),
            "body": None,
        }

    def get_callable(self) -> Callable:
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
            title_entry := Adw.EntryRow(
                title=_("Title"), text=self.props["title"] or ""
            )
        )
        title_entry.connect(
            "changed", lambda *_: self.props.update({"title": title_entry.get_text()})
        )

        expander.add_row(
            body_entry := Adw.EntryRow(
                title=_("Description"), text=self.props["body"] or ""
            )
        )
        body_entry.connect(
            "changed",
            lambda *_: self.props.update({"body": body_entry.get_text()}),
        )

        return expander


class RingBellAction(Action):
    ident = "ring-bell"
    title = _("Play Alert Sound")
    icon_name = "audio-volume-high-symbolic"

    def get_callable(self) -> Callable:

        def ring_bell() -> None:
            if not (display := Gdk.Display.get_default()):
                return

            display.beep()

            self._done()

        return ring_bell

    def get_widget(self) -> Gtk.Widget:
        return Adw.ActionRow(title=self.title, icon_name=self.icon_name)


class WaitAction(Action):
    ident = "wait"
    title = _("Wait")
    icon_name = "preferences-system-time-symbolic"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.props = {"seconds": 5}

    def get_callable(self) -> Callable:

        def wait() -> None:
            if not self.cb:
                return

            GLib.timeout_add_seconds(self.props["seconds"], self._done)

        return wait

    def get_widget(self) -> Gtk.Widget:
        (
            spin_row := Adw.SpinRow(
                title=_("Wait"),
                subtitle=_("Seconds"),
                adjustment=Gtk.Adjustment(
                    step_increment=1,
                    upper=86400,  # 24 hours
                    lower=0,
                    value=self.props["seconds"],
                ),
            )
        ).add_prefix(Gtk.Image(icon_name=self.icon_name))

        spin_row.connect(
            "notify::value",
            lambda *_: self.props.update({"seconds": spin_row.get_value()}),
        )

        return spin_row


types = (NotificationAction, RingBellAction, WaitAction)
actions = {}

for type in types:
    actions[type.ident] = type
