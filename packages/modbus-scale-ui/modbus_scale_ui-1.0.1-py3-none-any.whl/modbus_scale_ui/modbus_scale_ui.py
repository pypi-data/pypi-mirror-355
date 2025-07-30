#*****************************************************************************
#
#   Module:         modbus_scale_ui.py
#   Project:        UC-02-2024 Coffee Cart Modifications
#
#   Repository:     modbus_scale_ui
#   Target:         N/A
#
#   Author:         Rodney Elliott
#   Date:           16 June 2025
#
#   Description:    Weigh scale Modbus Ethernet client user interface.
#
#*****************************************************************************
#
#   Copyright:      (C) 2025 Rodney Elliott
#
#   This file is part of Coffee Cart Modifications.
#
#   Coffee Cart Modifications is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the license, or (at your
#   option) any later version.
#
#   Coffee Cart Modifications is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
#   Public License for more details.
#
#   You should of received a copy of the GNU General Public License along with
#   Coffee Cart Modifications. If not, see <https://www.gnu.org/licenses/>.
#
#*****************************************************************************

#*****************************************************************************
#   Doxygen file documentation
#*****************************************************************************

##
#   @file modbus_scale_ui.py
#
#   @brief Weigh scale Modbus Ethernet client user interface.
#
#   __Modbus Scale UI__ builds on the capabilities of __Modbus Scale Client__,
#   and permits users of the later to verify that their code is working as
#   expected.
#
#   __Modbus Scale UI__ takes the IPv4 (_Internet Protocol version 4_)
#   addresses of two scale servers as command-line arguments. If only one
#   physical scale exists, then a fake (but legal) IPv4 scale server address
#   may be supplied as the second argument.

#*****************************************************************************
#   Modules
#*****************************************************************************

##
#   @package textual.app
#
#   The _textual.app_ module provides the base Textual app class, as well as
#   the method used to build compound widgets - that is, widgets composed of
#   other widgets.
from textual.app import App, ComposeResult

##
#   @package textual.containers
#
#   The _textual.containers_ module provides access to a variety of built-in
#   containers that may be used to group widgets.
from textual.containers import Horizontal, Vertical

##
#   @package textual.widgets
#
#   The _textual.widgets_ module provides access to a variety of built-in
#   widgets. These are re-usable components responsible for managing parts of
#   the screen.
from textual.widgets import Button, Header, Footer, Static

##
#   @package textual.reactive
#
#   The _textual.reactive module_ provides reactive attributes that permit
#   widgets to be updated in response to events other than user actions.
from textual.reactive import reactive

##
#   @package art
#
#   ASCII art library.
from art import *

##
#   @package modbus_scale_client
#
#   The _modbus_scale_client_ package contains the Modbus Ethernet client
#   class.
from modbus_scale_client import modbus_scale_client

##
#   @package argparse
#
#   The _argparse_ module makes it easy to write user-friendly command-line
#   interfaces.
import argparse

##
#   @package ipaddress
#
#   The _ipaddress_ library provides the capabilities to create, manipulate,
#   and operate on IPv4 and IPv6 addresses and networks.
import ipaddress

#*****************************************************************************
#   Constants
#*****************************************************************************

## Scale weight font.
ART_FONT = "tarty1"

## Scale broker and server detected.
STATUS_NOMINAL = "NOMINAL\n\nTrue scale\nweight value"
## Scale server not detected.
STATUS_WARNING = "WARNING\n\nFake scale\nweight value"
## Scale broker not detected.
STATUS_FAILURE = "FAILURE\n\nNo scale\nbroker found"

#*****************************************************************************
#   Code
#*****************************************************************************

## Instance of the container for argument specifications.
parser = argparse.ArgumentParser(
    ## Name of the program.
    prog = "modbus_scale_ui",
    ## Text to display before the argument help.
    description = "Weigh scale Modbus Ethernet client user interface.",
    ## Text to display after the argument help.
    epilog = "https://gitlab.com/uc_mech_wing/robotics_control_lab/uc-02-2024/modbus_scale_ui"
)

## Positional argument definitions.
parser.add_argument("host_1", help = "IPv4 address of scale one.")
parser.add_argument("host_2", help = "IPv4 address of scale two.")

## Extract arguments and convert to strings.
args = parser.parse_args()

##
#   @brief Check IPv4 addresses are valid.
#
#   __Modbus Scale UI__ takes two command-line arguments, which are the IPv4
#   addresses of the scales whose weights it is to display. It is therefore
#   important that these arguments are valid dot-decimal format addresses.
def is_ipv4(string):
    try:
        ipaddress.IPv4Network(string)
        return True
    except ValueError:
        return False

is_ipv4(args.host_1)
is_ipv4(args.host_2)

## Instance of the scale client class.
mazzer_client = modbus_scale_client.ModbusScaleClient(host = args.host_1)
## Instance of the scale client class.
rancilio_client = modbus_scale_client.ModbusScaleClient(host = args.host_2)

#*****************************************************************************
#   Class
#*****************************************************************************

## The scale application class.
class ScaleApp(App):
    ## Tuples whose values are key, name of the action, short description.
    BINDINGS = [("1", "tare_mazzer", "Tare Mazzer Scale"),
        ("2", "tare_rancilio", "Tare Rancilio Scale")]

    ## Textual CSS is a subset of web CSS.
    CSS_PATH = "modbus_scale_ui.tcss"

    ## 
    #   @brief Assemble the UI out of discrete widgets.
    # 
    #   In addition to the use of pre-existing widgets such as the _Header_ and
    #   _Footer_, it is also necessary to create three compound widgets - that
    #   is, widgets composed of other widgets. These are based upon the
    #   _Static_ widget, and consist of the following.
    # 
    #   | Widget Name | Widget Description
    #   | ----------- | ------------------------ |
    #   | value       | Scale weight (grams)     |
    #   | blank       | Visual space element     |
    #   | state       | Scale status information |
    def compose(self) -> ComposeResult:
        ## Selected visual theme.
        self.theme = "gruvbox"

        ##
        #   By making time a reactive attribute, it becomes possible for UI
        #   elements to be updated automatically without the need for user
        #   interaction.
        time = reactive(0.0)

        yield Header()
        yield Footer()

        ##
        #   In order to be able to manipulate individual widgets, each has been
        #   assigned a unique name. This makes for ugly code, but until I find 
        #   a better way of doing things it will have to do.
        with Vertical():
            ## Mazzer scale horizontal slice.
            self.mazzer_horizontal = Horizontal()
            with self.mazzer_horizontal:
                ## Scale digits.
                self.mazzer_static_value = Static(text2art("-0000.0",
                    ART_FONT), classes = "value")
                ## Visual padding.
                self.mazzer_static_blank = Static(classes = "blank")
                ## Status area.
                self.mazzer_static_state = Static(id = "mazzer_state",
                    classes = "mazzer_error")

                yield self.mazzer_static_value
                yield self.mazzer_static_blank
                yield self.mazzer_static_state
               
            ## Rancilio scale horizontal slice.
            self.rancilio_horizontal = Horizontal()
            with self.rancilio_horizontal:
                ## Scale digits.
                self.rancilio_static_value = Static(text2art("-0000.0",
                    ART_FONT), classes = "value")
                ## Visual padding.
                self.rancilio_static_blank = Static(classes = "blank")
                ## Status area.
                self.rancilio_static_state = Static(id = "rancilio_state",
                    classes = "rancilio_error")
                
                yield self.rancilio_static_value
                yield self.rancilio_static_blank
                yield self.rancilio_static_state

    ##
    #   @brief Method called when entering application mode.
    #    
    #   In order for the UI to appear correctly when first entering application
    #   mode, the appearance of the _state_ compound widgets is set. If this is
    #   not done, UI widgets are not correctly displayed until after the first
    #   call to the _update_time_ method.
    def on_mount(self) -> None:
        self.mazzer_horizontal.border_title = "Mazzer"
        self.mazzer_horizontal.border_subtitle = "Mazzer"
        self.rancilio_horizontal.border_title = "Rancilio"
        self.rancilio_horizontal.border_subtitle = "Rancilio"
        
        self.add_class("mazzer_error")
        self.remove_class("mazzer_success")
        self.remove_class("mazzer_warning")
        self.mazzer_static_state.update(STATUS_FAILURE)
        
        self.add_class("rancilio_error")
        self.remove_class("rancilio_success")
        self.remove_class("rancilio_warning")
        self.rancilio_static_state.update(STATUS_FAILURE)

        ## Set the UI update interval.
        self.set_interval(1, self.update_time)

    ##
    #   @brief Method called upon expiry of the update interval.
    #
    #   It is responsible for refreshing the scale weight values and for
    #   changing the visual appearance of the state compound widgets.
    def update_time(self) -> None:
        if mazzer_client.server_exists() == True and \
            mazzer_client.broker_exists() == True:
            ## Display success visuals.
            self.add_class("mazzer_success")
            self.remove_class("mazzer_error")
            self.remove_class("mazzer_warning")
            self.mazzer_static_state.update(STATUS_NOMINAL)
            ## Update true scale weight.
            value = mazzer_client.read() 
            value = "{:8.1f}".format(value)
            self.mazzer_static_value.update(text2art(value, ART_FONT))

        elif mazzer_client.server_exists() == True and \
            mazzer_client.broker_exists() == False:
            ## Display error visuals
            self.add_class("mazzer_error")
            self.remove_class("mazzer_success")
            self.remove_class("mazzer_warning")
            self.mazzer_static_state.update(STATUS_FAILURE)
            ## Show broker error weight.
            self.mazzer_static_value.update(text2art("-9999.9", ART_FONT))

        else:
            ## Display warning visuals.
            self.add_class("mazzer_warning")
            self.remove_class("mazzer_error")
            self.remove_class("mazzer_success")
            self.mazzer_static_state.update(STATUS_WARNING) 
            ## Update fake scale weight.
            value = mazzer_client.read() 
            value = "{:8.1f}".format(value)
            self.mazzer_static_value.update(text2art(value, ART_FONT))

        if rancilio_client.server_exists() == True and \
            rancilio_client.broker_exists() == True:
            ## Display success visuals.
            self.add_class("rancilio_success")
            self.remove_class("rancilio_error")
            self.remove_class("rancilio_warning")
            self.rancilio_static_state.update(STATUS_NOMINAL)
            ## Update true scale weight.
            value = rancilio_client.read() 
            value = "{:8.1f}".format(value)
            self.rancilio_static_value.update(text2art(value, ART_FONT))

        elif rancilio_client.server_exists() == True and \
            rancilio_client.broker_exists() == False:
            ## Display error visuals.
            self.add_class("rancilio_error")
            self.remove_class("rancilio_success")
            self.remove_class("rancilio_warning")
            self.rancilio_static_state.update(STATUS_FAILURE)
            ## Show broker error weight.
            self.rancilio_static_value.update(text2art("-9999.9", ART_FONT))
        else:
            ## Display warning visuals.
            self.add_class("rancilio_warning")
            self.remove_class("rancilio_error")
            self.remove_class("rancilio_success")
            self.rancilio_static_state.update(STATUS_WARNING)
            ## Update fake scale weight.
            value = rancilio_client.read() 
            value = "{:8.1f}".format(value)
            self.rancilio_static_value.update(text2art(value, ART_FONT))
    
    ## Action method associated with the _tare_mazzer_ binding.
    def action_tare_mazzer(self) -> None:
        mazzer_client.tare()
        value = mazzer_client.read() 
        value = "{:8.1f}".format(value)
        self.mazzer_static_value.update(text2art(value, ART_FONT))

    ## Action method associated with the _tare_rancilio_ binding.
    def action_tare_rancilio(self) -> None:
        rancilio_client.tare()
        value = rancilio_client.read() 
        value = "{:8.1f}".format(value)
        self.rancilio_static_value.update(text2art(value, ART_FONT))

if __name__ == "__main__":
    ## Create an instance of the ScaleApp class and call the run method.
    app = ScaleApp()
    app.run()

