#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2015
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
import unittest

import Pyro4

from dfms import doutils
from dfms.data_object_mgr import DataObjectMgr
from dfms.ddap_protocol import DOStates

class TestDOM(unittest.TestCase):

    def test_runGraphOneDOPerDOM(self):
        """
        A test that creates two DataObjects in two different DOMs, wire them
        together externally (i.e., using their proxies), and runs the graph.
        For this the graphs that are fed into the DOMs must *not* express the
        inter-DOM relationships. The graph looks like:

        DOM #1     DOM #2
        =======    =======
        | A --|----|-> B |
        =======    =======
        """
        dom1 = DataObjectMgr(useDLM=False)
        dom2 = DataObjectMgr(useDLM=False)

        sessionId = 's1'
        g1 = '[{"oid":"A", "type":"plain", "storage": "memory"}]'
        g2 = '[{"oid":"B", "type":"app", "app":"dfms.data_object.CRCResultConsumer", "storage": "memory"}]'

        uids1 = dom1.createDataObjectGraph(sessionId, g1)
        uids2 = dom2.createDataObjectGraph(sessionId, g2)
        self.assertEquals(1, len(uids1))
        self.assertEquals(1, len(uids2))

        # Start the Pyro.daemon for our session on each DOM so we can
        # interact with our DOs
        dom1.startDOBDaemon(sessionId)
        dom2.startDOBDaemon(sessionId)

        # We externally wire the Proxy objects now
        a = Pyro4.Proxy(uids1[0])
        b = Pyro4.Proxy(uids2[0])
        a.addConsumer(b)

        # Run!
        a.write('a')
        a.setCompleted()

        self.assertEquals(DOStates.COMPLETED, a.status)
        self.assertEquals(DOStates.COMPLETED, b.status)
        self.assertEquals(a.checksum, int(doutils.allDataObjectContents(b)))

    def test_runGraphSeveralDOsPerDOM(self):
        """
        A test that creates several DataObjects in two different DOMs and  runs
        the graph. The graph looks like this

        DOM #1           DOM #2
        =============    ================
        | A --> C --|----|-|            |
        |           |    | |--> D --> E |
        | B --------|----|-|            |
        =============    ================

        :see: `self.test_runGraphSingleDOPerDOM`
        """
        dom1 = DataObjectMgr(useDLM=False)
        dom2 = DataObjectMgr(useDLM=False)

        sessionId = 's1'
        g1 = '[{"oid":"A", "type":"plain", "storage": "memory", "consumers":["C"]},\
               {"oid":"B", "type":"plain", "storage": "memory"},\
               {"oid":"C", "type":"app", "app":"dfms.data_object.CRCResultConsumer", "storage": "memory"}]'
        g2 = '[{"oid":"D", "type":"container", "consumers":["E"]},\
               {"oid":"E", "type":"app", "app":"test.test_data_object.SumupContainerChecksum", "storage": "memory"}]'

        uids1 = dom1.createDataObjectGraph(sessionId, g1)
        uids2 = dom2.createDataObjectGraph(sessionId, g2)
        self.assertEquals(3, len(uids1))
        self.assertEquals(2, len(uids2))

        # Start the Pyro.daemon for our session on each DOM so we can
        # interact with our DOs
        dom1.startDOBDaemon(sessionId)
        dom2.startDOBDaemon(sessionId)

        # We externally wire the Proxy objects to establish the inter-DOM
        # relationships
        a = Pyro4.Proxy(uids1[0])
        b = Pyro4.Proxy(uids1[1])
        c = Pyro4.Proxy(uids1[2])
        d = Pyro4.Proxy(uids2[0])
        e = Pyro4.Proxy(uids2[1])
        d.addChild(b)
        d.addChild(c)

        # Run! The sole fact that this doesn't throw exceptions is already
        # a good proof that everything is working as expected
        a.write('a')
        a.setCompleted()
        b.write('a')
        b.setCompleted()

        for do in a,b,c,d,e:
            self.assertEquals(DOStates.COMPLETED, do.status)

        self.assertEquals(a.checksum, int(doutils.allDataObjectContents(c)))
        self.assertEquals(b.checksum + c.checksum, int(doutils.allDataObjectContents(e)))

    def test_runWithFourDOMs(self):
        """
        A test that creates several DataObjects in two different DOMs and  runs
        the graph. The graph looks like this

                     DOM #2
                     +--------------------------+
                     |        |--> C --|        |
                 +---|--> B --|--> D --|--> F --|--|
                 |   |        |--> E --|        |  |
        DOM #1   |   +--------------------------+  |  DOM #4
        +-----+  |                                 |  +---------------+
        |     |  |                                 |--|--> L --|      |
        | A --|--+                                    |        |--> N |
        |     |  |                                 |--|--> M --|      |
        +-----+  |   DOM #3                        |  +---------------+
                 |   +--------------------------+  |
                 |   |        |--> H --|        |  |
                 +---|--> G --|--> I --|--> K --|--|
                     |        |--> J --|        |
                     +--------------------------+
        """

        dom1 = DataObjectMgr(useDLM=False)
        dom2 = DataObjectMgr(useDLM=False)
        dom3 = DataObjectMgr(useDLM=False)
        dom4 = DataObjectMgr(useDLM=False)
        allDOMs = [dom1, dom2, dom3, dom4]

        memoryCRCAppSpec = '"type":"app", "app":"dfms.data_object.CRCResultConsumer", "storage":"memory"'
        memoryCRCSumAppSpec = '"type":"app", "app":"test.test_data_object.SumupContainerChecksum", "storage":"memory"'

        sessionId = 's1'
        g1 = '[{"oid":"A", "type":"plain", "storage": "memory", "expectedSize":1}]'
        g2 = '[{{"oid":"B", {0}, "consumers":["C","D","E"]}},\
               {{"oid":"C", {0}}},\
               {{"oid":"D", {0}}},\
               {{"oid":"E", {0}}},\
               {{"oid":"F", "type":"container", "children":["C","D","E"]}}]'.format(memoryCRCAppSpec)
        g3 = '[{{"oid":"G", {0}, "consumers":["H","I","J"]}},\
               {{"oid":"H", {0}}},\
               {{"oid":"I", {0}}},\
               {{"oid":"J", {0}}},\
               {{"oid":"K", "type":"container", "children":["H","I","J"]}}]'.format(memoryCRCAppSpec)
        g4 = '[{{"oid":"L", {0}}},\
               {{"oid":"M", {0}}},\
               {{"oid":"N", "type":"container", "children":["L","M"]}}]'.format(memoryCRCSumAppSpec)

        uids1 = dom1.createDataObjectGraph(sessionId, g1)
        uids2 = dom2.createDataObjectGraph(sessionId, g2)
        uids3 = dom3.createDataObjectGraph(sessionId, g3)
        uids4 = dom4.createDataObjectGraph(sessionId, g4)
        self.assertEquals(1, len(uids1))
        self.assertEquals(5, len(uids2))
        self.assertEquals(5, len(uids3))
        self.assertEquals(3, len(uids4))

        # Start the Pyro.daemons
        for dom in allDOMs:
            dom.startDOBDaemon(sessionId)

        # We externally wire the Proxy objects to establish the inter-DOM
        # relationships. Intra-DOM relationships are already established
        uids = []
        [uids.extend(i) for i in [uids1, uids2, uids3, uids4]]
        proxies = []
        for uid in uids:
            proxies.append(Pyro4.Proxy(uid))

        a = proxies[0]
        b = proxies[1]
        f = proxies[5]
        g = proxies[6]
        k = proxies[10]
        l = proxies[11]
        m = proxies[12]

        a.addConsumer(b)
        a.addConsumer(g)
        f.addConsumer(l)
        k.addConsumer(m)

        # Run! This should trigger the full execution of the graph
        a.write('a')

        for do in proxies:
            self.assertEquals(DOStates.COMPLETED, do.status)