# main.py
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

"""The main application singleton class."""
import sys
from typing import Any, Optional, Sequence

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order

from gi.repository import Adw, Gio, Gtk

from actions import shared
from actions.window import ActionsWindow


class ActionsApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id=shared.APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )

        self.create_action(
            "close-window",
            lambda *_: self.get_active_window().close(),
            ("<primary>w",),
        )
        self.create_action(
            "quit",
            lambda *_: self.quit(),
            ("<primary>q",),
        )
        self.create_action(
            "about",
            self.on_about_action,
        )

    def do_activate(  # pylint: disable=arguments-differ
        self, gfile: Optional[Gio.File] = None
    ) -> None:
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        if self.get_active_window():
            return

        ActionsWindow(application=self).present()

    def on_about_action(self, *_args: Any):
        """Callback for the app.about action."""
        about = Adw.AboutDialog.new_from_appdata(
            shared.PREFIX + "/" + shared.APP_ID + ".metainfo.xml", shared.VERSION
        )
        about.set_developers(("kramo https://kramo.page",))
        about.set_designers(("kramo https://kramo.page",))
        about.set_copyright("© 2024 kramo")
        # Translators: Replace this with your name for it to show up in the about dialog
        about.set_translator_credits = (_("translator_credits"),)
        about.present(self.get_active_window())

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main():
    """The application's entry point."""
    app = ActionsApplication()
    return app.run(sys.argv)
