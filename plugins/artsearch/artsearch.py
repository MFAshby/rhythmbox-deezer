# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
#
# Copyright (C) 2011 Jonathan Matthew
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from gi.repository import GObject, Peas, RB, GdkPixbuf

import gettext
gettext.install('rhythmbox', RB.locale_dir())

import oldcache
from lastfm import LastFMSearch
from local import LocalSearch
from musicbrainz import MusicBrainzSearch

class Search(object):
	def __init__(self, store, key, last_time, searches):
		self.store = store
		self.key = key.copy()
		self.last_time = last_time
		self.searches = searches


	def next_search(self):
		if len(self.searches) == 0:
			self.store.store(self.key, RB.ExtDBSourceType.NONE, None)
			return False

		search = self.searches.pop(0)
		search.search(self.key, self.last_time, self.search_results, None)
		return True


	def search_results(self, storekey, data, source_type, args):

		if data is None or storekey is None:
			pass
		elif isinstance(data, str) or isinstance(data, unicode):
			print "got a uri: %s" % str(data)
			self.store.store_uri(storekey, source_type, data)
		elif isinstance(data, list) or isinstance(data, tuple):
			print "got a uri list: %s" % str(data)
			for u in data:
				self.store.store_uri(storekey, source_type, u)
		elif isinstance(data, GdkPixbuf.Pixbuf):
			print "got a pixbuf"
			self.store.store(storekey, source_type, data)
		else:
			# complain quietly
			print "got mystery meat: %s" % data
			pass

		# keep going anyway
		self.next_search()


class ArtSearchPlugin (GObject.GObject, Peas.Activatable):
	__gtype_name__ = 'ArtSearchPlugin'
	object = GObject.property(type=GObject.GObject)

	def __init__ (self):
		GObject.GObject.__init__ (self)

	def do_activate (self):
		self.art_store = RB.ExtDB(name="album-art")
		self.req_id = self.art_store.connect("request", self.album_art_requested)

	def do_deactivate (self):
		self.art_store.disconnect(self.req_id)
		self.req_id = 0
		self.art_store = None
		self.object = None

	def album_art_requested(self, store, key, last_time):
		searches = []
		if oldcache.USEFUL:
			searches.append(oldcache.OldCacheSearch())
		searches.append(LocalSearch())
		searches.append(MusicBrainzSearch())
		searches.append(LastFMSearch())

		s = Search(store, key, last_time, searches)
		return s.next_search()