# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Show POI on the map and in the menu.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
#---------------------------------------------------------------------------
from __future__ import with_statement # for python 2.5
from modules.base_module import RanaModule
from core import geo
from core.point import POI
from core.singleton import modrana
import math
import threading


def getModule(*args, **kwargs):
    return ShowPOI(*args, **kwargs)


class ShowPOI(RanaModule):
    """Show POI on the map and in the menu."""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.activePOI = None
        self.visiblePOI = []
        self.listMenusDirty = True
        self.drawActivePOI = False
        self.expectPoint = False
        self.expectLock = threading.Lock()

    def firstTime(self):
        # restore the IDs of visible POI
        self.restoreVisibleIDs()

    def makeMapClickable(self):
        """make the whole map/screen clickable and send a specific message when clicked"""
        clickHandler = self.m.get('clickHandler', None)
        (x, y, w, h) = self.get('viewport')
        if clickHandler:
            clickHandler.registerXYWH(x, y, x + w, y + h, 'showPOI:stopExpecting|ms:showPOI:storePOI:fromMapDone')

    def drawMenu(self, cr, menuName, args=None):
        """make the POI Object draw the menu :D"""
        if menuName == 'POIDetail':
            self.activePOI.drawMenu(cr)

    def drawMapOverlay(self, cr):
        if self.expectPoint:
            self.makeMapClickable()
        if self.drawActivePOI:
            proj = self.m.get('projection', None)
            menus = self.m.get('menu', None)
            if proj and self.visiblePOI:
                for POI in self.visiblePOI:
                    poiID = POI.db_index
                    lat = POI.lat
                    lon = POI.lon
                    name = POI.name
                    hidePOICaptionZl = int(self.get("hideMarkerCaptionsBelowZl", 13))
                    if int(self.get('z', 15)) > hidePOICaptionZl:
                        distanceString = ""
                        pos = self.get('pos', None)
                        units = self.m.get('units', None)
                        if pos and units:
                            (lat1, lon1) = pos # current position coordinates
                            kiloMetricDistance = geo.distance(lat, lon, lat1, lon1)
                            unitString = units.km2CurrentUnitString(kiloMetricDistance, 0, True)
                            distanceString = " (%s)" % unitString

                        text = "" + name + distanceString

                    (x, y) = proj.ll2xy(lat, lon) #   draw the highlighting circle
                    cr.set_line_width(8)
                    cr.set_source_rgba(0.1, 0.6, 0.1, 0.55) # highlight circle color
                    cr.arc(x, y, 15, 0, 2.0 * math.pi)
                    cr.stroke()
                    cr.fill()

                    # draw the point
                    cr.set_source_rgb(0.0, 0.0, 0.0)
                    cr.set_line_width(10)
                    cr.arc(x, y, 3, 0, 2.0 * math.pi)
                    cr.stroke()
                    cr.set_source_rgb(0.0, 0.0, 1.0)
                    cr.set_line_width(8)
                    cr.arc(x, y, 2, 0, 2.0 * math.pi)
                    cr.stroke()

                    # draw a caption with transparent background
                    if int(self.get('z', 15)) > hidePOICaptionZl:
                        cr.set_font_size(25)
                        extents = cr.text_extents(text) # get the text extents
                        (w, h) = (extents[2], extents[3])
                        border = 2
                        cr.set_line_width(2)
                        cr.set_source_rgba(0.1, 0.6, 0.1, 0.45) # transparent blue
                        (rx, ry, rw, rh) = (x - border + 12, y + border + h * 0.2 + 6, w + 4 * border, -(h * 1.4))
                        cr.rectangle(rx, ry, rw, rh) # create the transparent background rectangle
                        cr.fill()

                        # register clickable area
                        click = self.m.get('clickHandler', None)
                        if click:
                            # make the POI caption clickable
                            if poiID is not None: # new POI have id == None
                                click.registerXYWH(rx, ry - (-rh), rw, -rh,
                                                   "ms:showPOI:setActivePOI:%d|set:menu:showPOI#POIDetail" % poiID)
                            else: # the last added POI is still set, no need to set the id
                                click.registerXYWH(rx, ry - (-rh), rw, -rh, "set:menu:showPOI#POIDetail")
                        cr.fill()

                        # draw the actual text
                        #        cr.set_source_rgba(1, 1, 0, 0.95) # slightly transparent white
                        cr.set_source_rgba(1, 1, 1, 0.95) # slightly transparent white
                        menus.drawText(cr, text, rx, ry - (-rh), rw, -rh, 0.05)
                        cr.stroke()

    def handleMessage(self, message, messageType, args):
        # messages that need the store and/or menus go here
        store = self.m.get('storePOI', None)
        menus = self.m.get('menu', None)
        if store and menus:
            if message == "setupCategoryList":
                if messageType == 'ml':
                    # this is used for executing something special instead of going to the POIDetail menu
                    # after a POI is selected
                    POISelectedAction = args[0]
                    action = "ml:showPOI:setupPOIList:%s;%s|set:menu:menu#list#POIList" % ("%d", POISelectedAction)
                else:
                    action = "ms:showPOI:setupPOIList:%d|set:menu:menu#list#POIList"
                usedCategories = store.db.list_used_categories()
                # convert cat_id to actions
                i = 0
                for item in usedCategories:
                    (label, desc, cat_id) = item
                    buttonAction = action % cat_id
                    usedCategories[i] = (label, desc, buttonAction)
                    i += 1
                menus.addListMenu('POICategories', "set:menu:poi", usedCategories)
            elif message == 'setupPOIList':
                if args:
                    catId = None
                    action = "set:menu:None"
                    if messageType == 'ms':
                        catId = int(args)
                        action = 'set:menu:showPOI#POIDetail' # use the default action
                    elif messageType == 'ml':
                        # if the message is a message list, execute a custom action instead of the default POI detail menu
                        # TODO: use this even for selecting the POIDetail menu ?
                        catId = int(args[0])
                        action = args[1]
                    if catId is not None:
                        poiFromCategory = store.db.get_all_poi_from_category(catId)
                    else:
                        poiFromCategory = []
                    # convert the output to a listable menu compatible state
                    i = 0
                    for item in poiFromCategory:
                        (label, lat, lon, poi_id) = item
                        subText = "lat: %f, lon: %f" % (lat, lon)
                        buttonAction = "ms:showPOI:setActivePOI:%d|%s" % (poi_id, action)
                        poiFromCategory[i] = (label, subText, buttonAction)
                        i += 1
                    menus.addListMenu("POIList", 'set:menu:menu#list#POICategories', poiFromCategory)
            elif messageType == 'ms' and message == 'setActivePOI':
                if args:
                    POIId = int(args)
                    self.activePOI = GTKPOI(store.db.get_poi(POIId))
            elif messageType == 'ms' and message == 'storePOI':
                if args == "manualEntry":
                    # add all POI info manually
                    entry = self.m.get('textEntry', None)
                    if entry:
                        self.activePOI = GTKPOI(store.getEmptyPOI())  # set a blank POI as active
                        # start the chain of entry boxes
                        entry.entryBox(self, 'newName', 'POI name', "")
                elif args == "currentPosition":
                    # add current position as a new POI
                    entry = self.m.get('textEntry', None)
                    if entry:
                        pos = self.get('pos', None)
                        if pos:
                            self.activePOI = GTKPOI(store.getEmptyPOI()) # set a blank POI as active
                            (lat, lon) = pos
                            self.activePOI.lat = lat
                            self.activePOI.lon = lon
                            # start the entry box chain
                            entry.entryBox(self, 'newCurrentPositionName', 'POI name', "")
                elif args == "fromMap":
                    with self.expectLock: # nobody expects a lock here
                        self.expectPoint = True # turn on registering the whole screen clickable
                    self.set('menu', None)
                    self.sendMessage('ml:notification:m:Tap on the map to add POI;3')
                    self.set('needRedraw', True)
                elif args == "fromMapDone": # this is after the point has been clicked
                    with self.expectLock:
                        if self.expectPoint == True:
                            self.expectPoint = False # disable the registering
                            proj = self.m.get('projection', None)
                            lastClick = self.get('lastClickXY', None)
                            entry = self.m.get('textEntry', None)
                            if proj and lastClick and entry:
                                (x, y) = lastClick
                                (lat, lon) = proj.xy2ll(x, y)
                                self.activePOI = GTKPOI(store.getEmptyPOI()) # set a blank POI as active
                                self.activePOI.lat = lat
                                self.activePOI.lon = lon
                                # start the entry box chain
                                # we misuse the current position chain
                                entry.entryBox(self, 'newCurrentPositionName', 'POI name', "")

            elif messageType == 'ms' and message == 'editActivePOI':
                entry = self.m.get('textEntry', None)
                if args:
                    if entry:
                        if args == 'name':
                            name = self.activePOI.name
                            entry.entryBox(self, 'name', 'POI name', name)
                        if args == 'description':
                            description = self.activePOI.description
                            entry.entryBox(self, 'description', 'POI Description', description)
                        if args == 'lat':
                            lat = str(self.activePOI.lat)
                            entry.entryBox(self, 'lat', 'POI Latitude', lat)
                        if args == 'lon':
                            lon = str(self.activePOI.lon)
                            entry.entryBox(self, 'lon', 'POI Longitude', lon)

            elif messageType == 'ml' and message == 'setupPOICategoryChooser':
                # setup a category chooser menu
                if args:
                    (menu, key) = args
                    self._setupPOICategoryChooser(menu, key)

            elif messageType == 'ms' and message == 'setCatAndCommit':
                # selecting the category is the final stage of adding a POI
                if args:
                    # set the category index
                    self.activePOI.db_category_index = int(args)
                    # commit the new POI to db
                    self.activePOI.commit()
                    # mark list menus for regeneration
                    self.listMenusDirty = True
                    # go to the new POI menu
                    self.set('menu', 'showPOI#POIDetail')

            elif message == 'checkMenus':
                # check if the POI menus are "dirty" and need to be regenerated
                if self.listMenusDirty:
                    self.sendMessage('showPOI:setupCategoryList')
                    if self.activePOI:
                        catId = self.activePOI.db_category_index
                        self.sendMessage('ms:showPOI:setupPOIList:%d' % catId)
                    self.listMenusDirty = False

            elif message == "updateToolsMenu":
                self.activePOI.updateToolsMenu()

            elif message == 'listMenusDirty':
                # something regarding the POI changed
                # ,the menus might not be up to date
                # and may need a regen
                self.listMenusDirty = True

            elif message == 'askDeleteActivePOI':
                ask = self.m.get('askMenu', None)
                if ask:
                    id = self.activePOI.db_index
                    name = self.activePOI.name
                    question = "Do you really want to delete:\n%s\nfrom the POI database ?" % name
                    yesAction = "ms:storePOI:deletePOI:%d|set:menu:menu#list#POICategories" % id
                    noAction = "showPOI:updateToolsMenu|set:menu:POIDetailTools"
                    ask.setupAskYesNo(question, yesAction, noAction)

            elif message == 'centerOnActivePOI':
                # something regarding the POI changed
                # ,the menus might not be up to date
                # and may need a regen"""
                self.activePOI.showOnMap()

            elif message == 'routeToActivePOI':
                # something regarding the POI changed
                # ,the menus might not be up to date
                # and may need a regen"""
                self.activePOI.routeFrom('currentPosition')
                self.sendMessage('mapView:recentreToPos')
                self.makePOIVisible(self.activePOI)
                self.drawPOI()
                self.set('menu', None)
                self.set('needRedraw', True)

            elif message == 'drawActivePOI':
                if self.activePOI: # only add valid poi
                    self.makePOIVisible(self.activePOI)
                    # enable drawing
                    self.drawPOI()

            elif message == 'dontDrawActivePOI':
                self.removePOIFromVisible(self.activePOI)

            elif message == 'makeAllStoredPOIVisible':
                count = self.makeAllStoredPOIVisible()
                self.set("menu", None)
                self.notify("All %d stored POI are now visible" % count, 2000)

            elif message == 'clearVisiblePOI':
                count = self.clearVisiblePOI()
                if count > 0:
                    self.notify("%d visible POI cleared" % count, 2000)
                else:
                    self.notify("Nothing to clear", 2000)


    def _setupPOICategoryChooser(self, menu, key):
        menus = self.m.get('menu', None)
        store = self.m.get('storePOI', None)
        cats = store.db.list_categories()
        i = 0
        for cat in cats:
            (label, desc, cat_id) = cat
            action = "ms:%s:%s:%d" % (menu, key, cat_id)
            cats[i] = (label, desc, action)
            i += 1
        menus.addListMenu('POICategoryChooser', "set:menu:poi", cats)

    def makePOIVisible(self, POI):
        """add a POI to the list of visible POI & save ID"""
        self._makePOIVisible(POI)
        self.saveVisibleIDs()

    def _makePOIVisible(self, POI):
        """add a POI to the list of visible POI & don't save ID"""
        # check if the POI is already present
        if POI and POI not in self.visiblePOI:
            self.visiblePOI.append(POI)

    def makeAllStoredPOIVisible(self):
        """make all stored POI visible"""
        store = self.m.get('storePOI', None)
        cats = store.db.list_categories()
        count = 0
        _makePOIVisible = self._makePOIVisible
        for cat in cats:
            (label, desc, cat_id) = cat
            catPOI = store.db.get_all_poi_from_category(cat_id)
            count += len(catPOI)
            for item in catPOI:
                (label, lat, lon, poi_id) = item
                _makePOIVisible(store.db.get_poi(poi_id))
        self.saveVisibleIDs()
        self.drawPOI()
        return count

    def clearVisiblePOI(self):
        """discard visible POI"""
        count = len(self.visiblePOI)
        self.dontDrawPOI()
        self.visiblePOI = []
        self.saveVisibleIDs()
        return count

    def removePOIFromVisible(self, POI):
        if POI in self.visiblePOI:
            self.visiblePOI.remove(POI)
            self.saveVisibleIDs()

    def saveVisibleIDs(self):
        visibleIDs = []
        for POI in self.visiblePOI:
            visibleIDs.append(POI.db_index)
        self.set("visiblePOIIDs", visibleIDs)

    def restoreVisibleIDs(self):
        visibleIDs = self.get("visiblePOIIDs", [])
        if visibleIDs:
            store = self.m.get('storePOI', None)
            if store:
                for poiID in visibleIDs:
                    self._makePOIVisible(store.db.get_poi(poiID))
                if self.visiblePOI: # enable POI drawing only if some POI vere restored
                    self.drawPOI()
                self.log.info("showPOI: %d visible POI restored", len(self.visiblePOI))
            else:
                self.log.error("showPOI: can't restore visible, the storePOI module is not loaded")

    def drawPOI(self):
        """enable drawing of the active POI"""
        self.drawActivePOI = True

    def dontDrawPOI(self):
        """disable drawing of the active POI"""
        self.drawActivePOI = False

    def handleTextEntryResult(self, key, result):
        # TODO: add input checking
        entry = self.m.get('textEntry', None)
        if key == 'name':
            self.activePOI.name = result
            self.activePOI.commit()
        elif key == 'description':
            self.activePOI.description = result
            self.activePOI.commit()
        elif key == 'lat':
            self.activePOI.lat = float(result)
            self.activePOI.commit()
        elif key == 'lon':
            self.activePOI.lon = float(result)
            self.activePOI.commit()

        # New POI will be committed at the end, so we don't need to commit
        # after each data entry.
        # The events are also chained, so one entry box follows the other.
        elif key == 'newName':
            self.activePOI.name = result
            entry.entryBox(self, 'newDescription', 'POI Description', "")
        elif key == 'newDescription':
            self.activePOI.description = result
            entry.entryBox(self, 'newLat', 'POI Latitude', "")
        elif key == 'newLat':
            self.activePOI.lat = float(result)
            entry.entryBox(self, 'newLon', 'POI Longitude', "")
        elif key == 'newLon':
            self.activePOI.lon = float(result)
            # final step:
            # * setup the category chooser menu,
            # * make sure the POI is committed after a category is chosen
            self._setupPOICategoryChooser('showPOI', 'setCatAndCommit')
            self.set('menu', 'menu#list#POICategoryChooser')
            self.sendMessage('ml:notification:m:Select a category for this POI;3')

        # current position as a new POI" entry chain
        elif key == 'newCurrentPositionName':
            self.activePOI.name = result
            entry.entryBox(self, 'newCurrentPositionDescription', 'POI Description', "")
        elif key == 'newCurrentPositionDescription':
            self.activePOI.description = result
            # setup the category chooser
            # (category selection will be the last step)
            self._setupPOICategoryChooser('showPOI', 'setCatAndCommit')
            self.set('menu', 'menu#list#POICategoryChooser')
            self.sendMessage('ml:notification:m:Select a category for this POI;3')
            self.set('needRedraw', True)


class GTKPOI(POI):
    """A POI wrapper with additional methods needed by the GTK GUI"""
    def __init__(self, poi):
        POI.__init__(self, name=poi.name, description=poi.description, lat=poi.lat, lon=poi.lon,
                     db_cat_id=poi.db_category_index, db_poi_id=poi.db_index)

    def drawMenu(self, cr):
        menus = modrana.m.get('menu', None)
        if menus:
            button1 = ('map#show on', 'generic',
                       'mapView:recentre %f %f|showPOI:drawActivePOI|set:menu:None' % (self.lat, self.lon))
            button2 = ('tools', 'tools', 'showPOI:updateToolsMenu|set:menu:POIDetailTools')
            if self.name is not None and self.lat is not None and self.lon is not None and self.description is not None:
                text = "<big><b>%s</b></big>\n\n%s\n\nlat: <b>%f</b> lon: <b>%f</b>" % (
                self.name, self.description, self.lat, self.lon)
            else:
                text = "POI is being initialized"
            box = (text, '')
            menus.drawThreePlusOneMenu(cr, 'POIDetail', 'showPOI:checkMenus|set:menu:menu#list#POIList', button1,
                                       button2, box, wrap=True)
    def updateToolsMenu(self):
        # setup the tools submenu
        menus = modrana.m.get('menu', None)
        if menus:
            menus.clearMenu('POIDetailTools', "set:menu:showPOI#POIDetail")
            menus.addItem('POIDetailTools', 'here#route', 'generic', 'showPOI:routeToActivePOI')
            menus.addItem('POIDetailTools', 'name#edit', 'generic', 'ms:showPOI:editActivePOI:name')
            menus.addItem('POIDetailTools', 'description#edit', 'generic', 'ms:showPOI:editActivePOI:description')
            menus.addItem('POIDetailTools', 'latitude#edit', 'generic', 'ms:showPOI:editActivePOI:lat')
            menus.addItem('POIDetailTools', 'longitude#edit', 'generic', 'ms:showPOI:editActivePOI:lon')
            menus.addItem('POIDetailTools', 'category#change', 'generic',
                          'ml:showPOI:setupPOICategoryChooser:showPOI;setCatAndCommit|set:menu:menu#list#POICategoryChooser')
            menus.addItem('POIDetailTools', 'position#set as', 'generic',
                          'showPOI:centerOnActivePOI|ml:location:setPosLatLon:%f;%f' % (self.lat, self.lon))
            # just after the point is stored and and its detail menu shows up for the first time,
            # it cant be deleted from the database, because we don't know which index it got :D
            # TODO: find a free index and then store the point on it
            # (make sure no one writes to the database between getting the free index and writing the poi to it)
            # then we would be able to delete even newly created points
            if self.db_index:
                menus.addItem('POIDetailTools', 'POI#delete', 'generic', 'showPOI:askDeleteActivePOI')